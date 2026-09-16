import logging
from aiogram import Bot, Dispatcher
from aiogram.enums import ParseMode
from aiogram.client.default import DefaultBotProperties
from app.core.config import settings

logger = logging.getLogger(__name__)

bot = Bot(
    token=settings.BOT_TOKEN,
    default=DefaultBotProperties(parse_mode=ParseMode.HTML)
)

dp = Dispatcher()


def register_all_handlers() -> None:
    """Registers all routers and handlers onto the dispatcher."""
    from app.telegram.handlers.start import start_router
    from app.telegram.handlers.connection import connection_router
    from app.telegram.handlers.business_message import business_message_router
    from app.telegram.handlers.edited_message import edited_message_router
    from app.telegram.handlers.deleted_message import deleted_message_router
    from app.telegram.handlers.subscription import subscription_router
    from app.telegram.handlers.settings import settings_router
    from app.telegram.handlers.admin import admin_router

    dp.include_router(start_router)
    dp.include_router(connection_router)
    dp.include_router(business_message_router)
    dp.include_router(edited_message_router)
    dp.include_router(deleted_message_router)
    dp.include_router(subscription_router)
    dp.include_router(settings_router)
    dp.include_router(admin_router)
    logger.info("All Telegram handlers successfully registered.")
