import logging
from datetime import datetime, timezone
from aiogram import Router
from aiogram.types import BusinessConnection as TelegramBusinessConnection
from sqlalchemy import select
from app.db.session import async_session_factory
from app.services.subscription_service import subscription_service
from app.models.business_connection import BusinessConnection
from app.telegram.bot import bot
from app.core.i18n import t, normalize_language_code

logger = logging.getLogger(__name__)
connection_router = Router(name="connection_router")


@connection_router.business_connection()
async def handle_business_connection(conn: TelegramBusinessConnection):
    """
    Handles business_connection updates when user links/unlinks the bot.
    Enforces Section 6: Trial starts when Business Connection is first established.
    """
    telegram_user_id = conn.user.id
    business_conn_id = conn.id
    user_chat_id = conn.user_chat_id
    is_enabled = conn.is_enabled
    can_reply = conn.can_reply

    logger.info(f"Business connection update: id={business_conn_id}, user={telegram_user_id}, enabled={is_enabled}")

    async with async_session_factory() as session:
        # 1. Get or create user with language detection
        detected_lang = normalize_language_code(getattr(conn.user, "language_code", None))
        user = await subscription_service.get_or_create_user(
            session=session,
            telegram_user_id=telegram_user_id,
            username=conn.user.username,
            first_name=conn.user.first_name,
            last_name=conn.user.last_name,
            language=detected_lang
        )
        user_lang = user.language or detected_lang

        # 2. Get or create BusinessConnection
        q = select(BusinessConnection).where(
            BusinessConnection.business_connection_id == business_conn_id
        )
        db_conn = (await session.execute(q)).scalar_one_or_none()

        now = datetime.now(timezone.utc)
        if not db_conn:
            db_conn = BusinessConnection(
                business_connection_id=business_conn_id,
                user_id=user.id,
                user_chat_id=user_chat_id,
                connection_date=now,
                is_enabled=is_enabled,
                can_reply=can_reply
            )
            session.add(db_conn)
        else:
            db_conn.user_id = user.id
            db_conn.user_chat_id = user_chat_id
            db_conn.is_enabled = is_enabled
            db_conn.can_reply = can_reply

        # 3. Activate 72h trial if first connection
        trial_activated = False
        if is_enabled:
            trial_activated = await subscription_service.initialize_trial_on_connection(session, user)

        await session.commit()

    # Send confirmation message to user's bot chat in user's language
    try:
        if is_enabled:
            if trial_activated:
                msg = t("conn_connected_trial", user_lang)
            else:
                msg = t("conn_reconnected", user_lang)
            await bot.send_message(chat_id=telegram_user_id, text=msg, parse_mode="HTML")
        else:
            await bot.send_message(
                chat_id=telegram_user_id,
                text=t("conn_disconnected", user_lang),
                parse_mode="HTML"
            )
    except Exception as e:
        logger.warning(f"Could not send connection confirmation to user {telegram_user_id}: {e}")
