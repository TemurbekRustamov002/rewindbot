import logging
from aiogram import Router
from aiogram.types import BusinessMessagesDeleted
from sqlalchemy import select
from app.db.session import async_session_factory
from app.services.subscription_service import subscription_service
from app.services.archive_service import archive_service
from app.services.notification_service import notification_service
from app.models.business_connection import BusinessConnection
from app.models.user import User
from app.telegram.bot import bot

logger = logging.getLogger(__name__)
deleted_message_router = Router(name="deleted_message_router")


@deleted_message_router.deleted_business_messages()
async def handle_deleted_business_messages(event: BusinessMessagesDeleted):
    """
    FR-300: Handles deleted_business_messages updates.
    Finds original message records from the database, marks them as deleted,
    and alerts the user with original text / media in their private bot chat.
    """
    business_conn_id = event.business_connection_id
    telegram_chat_id = event.chat.id
    deleted_message_ids = event.message_ids

    logger.info(f"Deleted messages received: conn={business_conn_id}, chat={telegram_chat_id}, count={len(deleted_message_ids)}")

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

        # 2. Process and mark deleted messages in DB
        found_messages = await archive_service.process_deleted_messages(
            session=session,
            business_connection_id=business_conn_id,
            telegram_chat_id=telegram_chat_id,
            deleted_message_ids=deleted_message_ids
        )

        # 3. Send notifications for each found message
        for msg in found_messages:
            await notification_service.send_deleted_notification(
                bot=bot,
                session=session,
                user=user,
                message=msg
            )

        # Edge case: If messages were deleted that were never in the archive (e.g., sent before bot was connected)
        found_ids = {m.telegram_message_id for m in found_messages}
        missing_ids = [mid for mid in deleted_message_ids if mid not in found_ids]
        if missing_ids and not found_messages:
            try:
                from app.core.i18n import t
                user_lang = user.language or "uz"
                await bot.send_message(
                    chat_id=user.telegram_user_id,
                    text=t("deleted_missing_text", user_lang, count=len(missing_ids)),
                    parse_mode="HTML"
                )
            except Exception as e:
                logger.warning(f"Could not send missing message notice to {user.telegram_user_id}: {e}")

        await session.commit()
