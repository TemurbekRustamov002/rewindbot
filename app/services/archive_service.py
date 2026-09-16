import asyncio
import logging
from datetime import datetime, timezone
from typing import Optional, List
from sqlalchemy import select, update
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.user import User
from app.models.chat import Chat, ExcludedChat
from app.models.message import Message, MessageVersion
from app.models.event import DeletedEvent
from app.core.security import calculate_content_hash

logger = logging.getLogger(__name__)

# In-process lock to prevent database race conditions on concurrent updates
_db_lock = asyncio.Lock()


def ensure_datetime(val) -> datetime:
    """Converts int/float timestamps or naive datetimes into timezone-aware datetime objects."""
    if val is None:
        return datetime.now(timezone.utc)
    if isinstance(val, (int, float)):
        return datetime.fromtimestamp(val, tz=timezone.utc)
    if isinstance(val, datetime):
        if val.tzinfo is None:
            return val.replace(tzinfo=timezone.utc)
        return val
    return datetime.now(timezone.utc)


class ArchiveService:
    async def get_or_create_chat(
        self,
        session: AsyncSession,
        user: User,
        business_connection_id: str,
        telegram_chat_id: int,
        username: Optional[str] = None,
        first_name: Optional[str] = None,
        last_name: Optional[str] = None,
        title: Optional[str] = None
    ) -> Chat:
        """Gets or creates a chat entry for a business connection."""
        async with _db_lock:
            query = select(Chat).where(
                Chat.user_id == user.id,
                Chat.business_connection_id == business_connection_id,
                Chat.telegram_chat_id == telegram_chat_id
            )
            result = await session.execute(query)
            chat = result.scalar_one_or_none()

            if not chat:
                # Check if chat is in excluded list
                ex_query = select(ExcludedChat).where(
                    ExcludedChat.user_id == user.id,
                    ExcludedChat.telegram_chat_id == telegram_chat_id
                )
                ex_result = await session.execute(ex_query)
                is_excluded = ex_result.scalar_one_or_none() is not None

                chat = Chat(
                    user_id=user.id,
                    business_connection_id=business_connection_id,
                    telegram_chat_id=telegram_chat_id,
                    username=username,
                    first_name=first_name,
                    last_name=last_name,
                    title=title,
                    is_excluded=is_excluded
                )
                try:
                    session.add(chat)
                    await session.flush()
                except Exception:
                    await session.rollback()
                    result = await session.execute(query)
                    chat = result.scalar_one_or_none()
            else:
                # Update info
                if username: chat.username = username
                if first_name: chat.first_name = first_name
                if last_name: chat.last_name = last_name
                if title: chat.title = title

            return chat

    async def save_business_message(
        self,
        session: AsyncSession,
        user: User,
        chat: Chat,
        business_connection_id: str,
        telegram_message_id: int,
        sender_id: int,
        sender_username: Optional[str],
        sender_first_name: Optional[str],
        sender_last_name: Optional[str],
        direction: str,
        message_type: str,
        sent_at,
        text: Optional[str] = None,
        caption: Optional[str] = None,
        entities_json: Optional[str] = None,
        reply_to_message_id: Optional[int] = None,
        media_group_id: Optional[str] = None
    ) -> Message:
        """Saves incoming or outgoing business message with concurrency/idempotency protection."""
        async with _db_lock:
            query = select(Message).where(
                Message.business_connection_id == business_connection_id,
                Message.telegram_chat_id == chat.telegram_chat_id,
                Message.telegram_message_id == telegram_message_id
            )
            result = await session.execute(query)
            msg = result.scalar_one_or_none()

            dt_sent_at = ensure_datetime(sent_at)

            if not msg:
                msg = Message(
                    user_id=user.id,
                    chat_id=chat.id,
                    business_connection_id=business_connection_id,
                    telegram_chat_id=chat.telegram_chat_id,
                    telegram_message_id=telegram_message_id,
                    sender_id=sender_id,
                    sender_username=sender_username,
                    sender_first_name=sender_first_name,
                    sender_last_name=sender_last_name,
                    direction=direction,
                    type=message_type,
                    text=text,
                    caption=caption,
                    entities_json=entities_json,
                    reply_to_message_id=reply_to_message_id,
                    media_group_id=media_group_id,
                    sent_at=dt_sent_at,
                    is_deleted=False
                )
                try:
                    session.add(msg)
                    await session.flush()

                    # Save initial version (v1)
                    initial_hash = calculate_content_hash(text, caption)
                    v1 = MessageVersion(
                        message_id_fk=msg.id,
                        version_number=1,
                        text=text,
                        caption=caption,
                        entities_json=entities_json,
                        content_hash=initial_hash,
                        telegram_edit_date=dt_sent_at
                    )
                    session.add(v1)
                    await session.flush()
                except Exception:
                    await session.rollback()
                    result = await session.execute(query)
                    msg = result.scalar_one_or_none()
            else:
                # Update existing record if needed
                if text: msg.text = text
                if caption: msg.caption = caption
                if reply_to_message_id: msg.reply_to_message_id = reply_to_message_id

            return msg

    async def record_message_edit(
        self,
        session: AsyncSession,
        business_connection_id: str,
        telegram_chat_id: int,
        telegram_message_id: int,
        new_text: Optional[str],
        new_caption: Optional[str],
        new_entities_json: Optional[str],
        edit_date: datetime,
        user: Optional[User] = None
    ) -> Optional[MessageVersion]:
        """
        Records an edited version of a message.
        Preserves complete version history without overwriting original content.
        """
        query = select(Message).where(
            Message.business_connection_id == business_connection_id,
            Message.telegram_chat_id == telegram_chat_id,
            Message.telegram_message_id == telegram_message_id
        )
        result = await session.execute(query)
        msg = result.scalar_one_or_none()

        new_hash = calculate_content_hash(new_text, new_caption)

        if not msg:
            logger.info(f"Edited message {telegram_message_id} was not in archive, creating initial entry.")
            if user:
                # Auto-create chat & message stub if missed initially
                chat = await self.get_or_create_chat(
                    session=session,
                    user=user,
                    business_connection_id=business_connection_id,
                    telegram_chat_id=telegram_chat_id
                )
                msg = await self.save_business_message(
                    session=session,
                    user=user,
                    chat=chat,
                    business_connection_id=business_connection_id,
                    telegram_message_id=telegram_message_id,
                    sender_id=telegram_chat_id,
                    sender_username=None,
                    sender_first_name="Suhbatdosh",
                    sender_last_name=None,
                    direction="INCOMING",
                    message_type="TEXT",
                    sent_at=edit_date,
                    text=new_text,
                    caption=new_caption,
                    entities_json=new_entities_json
                )
            else:
                return None

        async with _db_lock:
            # Get latest version
            v_query = select(MessageVersion).where(
                MessageVersion.message_id_fk == msg.id
            ).order_by(MessageVersion.version_number.desc()).limit(1)
            v_result = await session.execute(v_query)
            latest_version = v_result.scalar_one_or_none()

            if latest_version and latest_version.content_hash == new_hash:
                # Duplicate edit event, ignore
                return None

            next_version_num = (latest_version.version_number + 1) if latest_version else 1

            dt_edit_date = ensure_datetime(edit_date)

            new_version = MessageVersion(
                message_id_fk=msg.id,
                version_number=next_version_num,
                text=new_text,
                caption=new_caption,
                entities_json=new_entities_json,
                content_hash=new_hash,
                telegram_edit_date=dt_edit_date
            )
            try:
                session.add(new_version)
                # Update message current text pointer
                msg.text = new_text
                msg.caption = new_caption
                msg.entities_json = new_entities_json
                await session.flush()
            except Exception:
                await session.rollback()
                return None

            logger.info(f"Recorded edit v{next_version_num} for message {telegram_message_id}")
            return new_version

    async def process_deleted_messages(
        self,
        session: AsyncSession,
        business_connection_id: str,
        telegram_chat_id: int,
        deleted_message_ids: List[int]
    ) -> List[Message]:
        """Marks messages as deleted and creates deletion events."""
        found_messages: List[Message] = []
        now = datetime.now(timezone.utc)

        for msg_id in deleted_message_ids:
            query = select(Message).where(
                Message.business_connection_id == business_connection_id,
                Message.telegram_chat_id == telegram_chat_id,
                Message.telegram_message_id == msg_id
            )
            result = await session.execute(query)
            msg = result.scalar_one_or_none()

            if msg:
                msg.is_deleted = True
                msg.deleted_at = now

                event = DeletedEvent(
                    message_id_fk=msg.id,
                    business_connection_id=business_connection_id,
                    telegram_chat_id=telegram_chat_id,
                    telegram_message_id=msg_id,
                    notification_sent=False
                )
                session.add(event)
                found_messages.append(msg)
            else:
                logger.info(f"Deleted message {msg_id} was not in archive.")

        await session.flush()
        return found_messages


archive_service = ArchiveService()
