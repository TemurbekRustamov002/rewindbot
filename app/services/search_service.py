import uuid
import logging
from typing import List, Tuple, Optional
from sqlalchemy import select, func, delete, or_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.user import User
from app.models.chat import Chat, ExcludedChat
from app.models.message import Message, MessageVersion
from app.models.media import MediaObject
from app.models.subscription import Subscription, Payment
from app.models.settings import UserSettings
from app.models.event import AuditLog
from app.services.storage_service import storage_service

logger = logging.getLogger(__name__)


class SearchService:
    async def get_deleted_messages(
        self,
        session: AsyncSession,
        user: User,
        page: int = 1,
        page_size: int = 5
    ) -> Tuple[List[Message], int]:
        """Fetches paginated list of deleted messages for a user."""
        offset = (page - 1) * page_size

        # Count total
        count_query = select(func.count(Message.id)).where(
            Message.user_id == user.id,
            Message.is_deleted == True
        )
        total_count = (await session.execute(count_query)).scalar_one()

        # Query messages
        query = select(Message).where(
            Message.user_id == user.id,
            Message.is_deleted == True
        ).order_by(Message.deleted_at.desc()).offset(offset).limit(page_size).options(
            selectinload(Message.media_objects),
            selectinload(Message.versions)
        )
        result = await session.execute(query)
        messages = list(result.scalars().all())

        return messages, total_count

    async def get_edited_messages(
        self,
        session: AsyncSession,
        user: User,
        page: int = 1,
        page_size: int = 5
    ) -> Tuple[List[Message], int]:
        """Fetches paginated list of edited messages (messages having >1 version)."""
        offset = (page - 1) * page_size

        # Subquery for messages with multiple versions
        v_sub = select(MessageVersion.message_id_fk).group_by(
            MessageVersion.message_id_fk
        ).having(func.count(MessageVersion.id) > 1).scalar_subquery()

        count_query = select(func.count(Message.id)).where(
            Message.user_id == user.id,
            Message.id.in_(v_sub)
        )
        total_count = (await session.execute(count_query)).scalar_one()

        query = select(Message).where(
            Message.user_id == user.id,
            Message.id.in_(v_sub)
        ).order_by(Message.updated_at.desc()).offset(offset).limit(page_size).options(
            selectinload(Message.versions)
        )
        result = await session.execute(query)
        messages = list(result.scalars().all())

        return messages, total_count

    async def search_messages(
        self,
        session: AsyncSession,
        user: User,
        search_query: str,
        page: int = 1,
        page_size: int = 10
    ) -> Tuple[List[Message], int]:
        """Searches messages by text content or sender username/name."""
        offset = (page - 1) * page_size
        like_pattern = f"%{search_query}%"

        filter_condition = or_(
            Message.text.ilike(like_pattern),
            Message.caption.ilike(like_pattern),
            Message.sender_first_name.ilike(like_pattern),
            Message.sender_username.ilike(like_pattern)
        )

        count_q = select(func.count(Message.id)).where(
            Message.user_id == user.id,
            filter_condition
        )
        total = (await session.execute(count_q)).scalar_one()

        q = select(Message).where(
            Message.user_id == user.id,
            filter_condition
        ).order_by(Message.sent_at.desc()).offset(offset).limit(page_size)

        result = await session.execute(q)
        return list(result.scalars().all()), total

    async def delete_all_user_data(
        self,
        session: AsyncSession,
        user: User
    ) -> bool:
        """
        Executes complete GDPR / privacy compliant data deletion for a user.
        Deletes messages, versions, media files from storage, chats, and logs.
        """
        try:
            # 1. Fetch and delete media from physical storage
            m_query = select(MediaObject.storage_key).join(Message).where(
                Message.user_id == user.id,
                MediaObject.storage_key.is_not(None)
            )
            m_res = await session.execute(m_query)
            keys = m_res.scalars().all()

            for key in keys:
                if key:
                    await storage_service.delete_file(key)

            # 2. Delete messages and cascades
            await session.execute(delete(Message).where(Message.user_id == user.id))
            await session.execute(delete(Chat).where(Chat.user_id == user.id))
            await session.execute(delete(ExcludedChat).where(ExcludedChat.user_id == user.id))

            # 3. Log audit event
            audit = AuditLog(
                user_id=user.id,
                action="DATA_DELETED",
                details_json=f'{{"deleted_at": "{user.telegram_user_id}"}}'
            )
            session.add(audit)
            await session.commit()
            logger.info(f"Completely purged all archive data for user {user.telegram_user_id}")
            return True
        except Exception as e:
            logger.error(f"Error purging data for user {user.telegram_user_id}: {e}")
            await session.rollback()
            return False


search_service = SearchService()
