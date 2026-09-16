import logging
import json
from aiogram import Router
from aiogram.types import Message
from sqlalchemy import select
from app.db.session import async_session_factory
from app.services.subscription_service import subscription_service
from app.services.archive_service import archive_service
from app.services.notification_service import notification_service
from app.models.business_connection import BusinessConnection
from app.models.user import User
from app.models.message import Message as DBMessage
from app.telegram.bot import bot

logger = logging.getLogger(__name__)
edited_message_router = Router(name="edited_message_router")


@edited_message_router.edited_business_message()
async def handle_edited_business_message(message: Message):
    """
    FR-200: Handles edited_business_message updates without overwriting previous content.
    Creates a new version in message_versions and notifies the user with diff.
    """
    business_conn_id = message.business_connection_id
    if not business_conn_id:
        return

    telegram_chat_id = message.chat.id
    telegram_message_id = message.message_id
    edit_date = message.edit_date or message.date

    async with async_session_factory() as session:
        # 1. Identify user owner accurately
        resolved = await subscription_service.resolve_business_connection(
            session=session,
            bot=bot,
            business_connection_id=business_conn_id
        )
        if not resolved:
            return

        conn, user = resolved
        if not conn.is_enabled:
            return

        has_access, _ = await subscription_service.has_active_access(session, user)
        if not has_access:
            await notification_service.send_expired_subscription_alert(
                bot=bot,
                user=user,
                business_conn_id=business_conn_id
            )
            return

        # 2. Record edit version
        entities_json = json.dumps([e.model_dump() for e in message.entities]) if message.entities else None

        new_version = await archive_service.record_message_edit(
            session=session,
            business_connection_id=business_conn_id,
            telegram_chat_id=telegram_chat_id,
            telegram_message_id=telegram_message_id,
            new_text=message.text,
            new_caption=message.caption,
            new_entities_json=entities_json,
            edit_date=edit_date,
            user=user
        )

        if not new_version:
            return

        # 3. Retrieve DB message
        msg_q = select(DBMessage).where(
            DBMessage.business_connection_id == business_conn_id,
            DBMessage.telegram_chat_id == telegram_chat_id,
            DBMessage.telegram_message_id == telegram_message_id
        )
        db_msg = (await session.execute(msg_q)).scalar_one_or_none()

        if db_msg:
            # Send real-time edit notification
            await notification_service.send_edit_notification(
                bot=bot,
                session=session,
                user=user,
                message=db_msg,
                new_version=new_version
            )

        await session.commit()
