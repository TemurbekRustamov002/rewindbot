import logging
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import CommandStart, Command
from sqlalchemy import select, func
from app.db.session import async_session_factory
from app.services.subscription_service import subscription_service
from app.models.business_connection import BusinessConnection
from app.models.message import Message as DBMessage
from app.models.user import User
from app.telegram.keyboards.menu import (
    get_start_inline_keyboard,
    get_main_reply_keyboard,
    get_language_inline_keyboard
)
from app.core.config import settings
from app.core.i18n import t, normalize_language_code, SUPPORTED_LANGUAGES

logger = logging.getLogger(__name__)
start_router = Router(name="start_router")


@start_router.message(CommandStart())
async def handle_start(message: Message):
    """FR-001: /start handler with dynamic language detection & modern UI."""
    raw_lang = message.from_user.language_code
    detected_lang = normalize_language_code(raw_lang)

    async with async_session_factory() as session:
        user = await subscription_service.get_or_create_user(
            session=session,
            telegram_user_id=message.from_user.id,
            username=message.from_user.username,
            first_name=message.from_user.first_name,
            last_name=message.from_user.last_name,
            language=detected_lang
        )
        user_lang = user.language or detected_lang
        await session.commit()

    welcome_text = t("start_welcome", user_lang)
    await message.answer(
        text=welcome_text,
        parse_mode="HTML",
        reply_markup=get_start_inline_keyboard(user_lang)
    )
    # Also provide persistent bottom keyboard in user's language
    await message.answer(
        t("start_bottom_hint", user_lang),
        reply_markup=get_main_reply_keyboard(user_lang)
    )


@start_router.callback_query(F.data == "guide_connect")
async def handle_guide_connect(callback: CallbackQuery):
    """Instructions on connecting the bot to Telegram Business / Chat Automation."""
    async with async_session_factory() as session:
        user = await subscription_service.get_or_create_user(
            session=session,
            telegram_user_id=callback.from_user.id
        )
        user_lang = user.language or "uz"

    text = t("start_guide", user_lang, bot_username=settings.BOT_USERNAME)
    await callback.message.edit_text(
        text=text,
        parse_mode="HTML",
        reply_markup=get_start_inline_keyboard(user_lang)
    )
    await callback.answer()


@start_router.callback_query(F.data == "menu_main")
async def handle_menu_main(callback: CallbackQuery):
    """Returns to start view."""
    async with async_session_factory() as session:
        user = await subscription_service.get_or_create_user(
            session=session,
            telegram_user_id=callback.from_user.id
        )
        user_lang = user.language or "uz"

    text = t("start_welcome", user_lang)
    await callback.message.edit_text(
        text=text,
        parse_mode="HTML",
        reply_markup=get_start_inline_keyboard(user_lang)
    )
    await callback.answer()


@start_router.message(F.text.in_(["🛡 Status", "🛡 Holat", "🛡 Статус"]))
@start_router.message(Command("status"))
async def handle_status(message: Message):
    """Shows user connection, subscription and today's activity status in user language."""
    async with async_session_factory() as session:
        user = await subscription_service.get_or_create_user(
            session=session,
            telegram_user_id=message.from_user.id
        )
        user_lang = user.language or "uz"
        has_access, status_label = await subscription_service.has_active_access(session, user)

        # Connection check
        conn_q = select(BusinessConnection).where(
            BusinessConnection.user_id == user.id,
            BusinessConnection.is_enabled == True
        )
        conn = (await session.execute(conn_q)).scalar_one_or_none()

        # Stats check
        del_count_q = select(func.count(DBMessage.id)).where(
            DBMessage.user_id == user.id,
            DBMessage.is_deleted == True
        )
        del_count = (await session.execute(del_count_q)).scalar_one()

        conn_status = t("status_active", user_lang) if conn else t("status_not_connected", user_lang)
        mon_status = t("status_monitored", user_lang) if (conn and has_access) else t("status_paused", user_lang)

        exp_date_str = t("status_na", user_lang)
        if user.trial_expires_at and status_label == "TRIAL_ACTIVE":
            exp_date_str = user.trial_expires_at.strftime("%d.%m.%Y %H:%M") + " (Trial)"

        status_display = {
            "TRIAL_ACTIVE": t("status_trial", user_lang),
            "PAID_ACTIVE": t("status_pro_active", user_lang),
            "EXPIRED": t("status_expired", user_lang)
        }.get(status_label, status_label)

        archive_stat = t("status_archive_stat", user_lang, count=del_count)

        text = (
            f"{t('status_title', user_lang)}\n\n"
            f"• {t('status_business', user_lang)}: <b>{conn_status}</b>\n"
            f"• {t('status_monitoring', user_lang)}: <b>{mon_status}</b>\n"
            f"• {t('status_current_plan', user_lang)}: <b>{status_display}</b>\n"
            f"• {t('status_expiration', user_lang)}: <b><code>{exp_date_str}</code></b>\n\n"
            f"<blockquote>{archive_stat}</blockquote>"
        )
        await message.answer(text=text, parse_mode="HTML")


@start_router.message(F.text.in_(["ℹ️ Yordam", "ℹ️ Помощь", "ℹ️ Help"]))
@start_router.message(Command("help"))
@start_router.callback_query(F.data == "menu_help")
async def handle_help(event: Message | CallbackQuery):
    """Renders localized help guide."""
    user_id = event.from_user.id
    async with async_session_factory() as session:
        user = await subscription_service.get_or_create_user(session=session, telegram_user_id=user_id)
        user_lang = user.language or "uz"

    text = t("help_text", user_lang)
    if isinstance(event, CallbackQuery):
        await event.message.answer(text=text, parse_mode="HTML")
        await event.answer()
    else:
        await event.answer(text=text, parse_mode="HTML")


@start_router.message(F.text.in_(["🌐 Til", "🌐 Язык", "🌐 Language"]))
@start_router.message(Command("lang"))
@start_router.message(Command("language"))
@start_router.callback_query(F.data == "menu_lang")
async def handle_language_menu(event: Message | CallbackQuery):
    """Displays language selection keyboard."""
    user_id = event.from_user.id
    async with async_session_factory() as session:
        user = await subscription_service.get_or_create_user(session=session, telegram_user_id=user_id)
        user_lang = user.language or "uz"

    kb = get_language_inline_keyboard(current_lang=user_lang)
    text = t("lang_select_title", user_lang)

    if isinstance(event, CallbackQuery):
        await event.message.edit_text(text=text, parse_mode="HTML", reply_markup=kb)
        await event.answer()
    else:
        await event.answer(text=text, parse_mode="HTML", reply_markup=kb)


@start_router.callback_query(F.data.startswith("set_lang:"))
async def handle_set_language(callback: CallbackQuery):
    """Saves user's chosen language and updates UI."""
    new_lang = callback.data.split(":")[-1]
    if new_lang not in SUPPORTED_LANGUAGES:
        new_lang = "uz"

    async with async_session_factory() as session:
        user = await subscription_service.get_or_create_user(
            session=session,
            telegram_user_id=callback.from_user.id
        )
        user.language = new_lang
        await session.commit()

    success_text = t("lang_changed", new_lang)
    kb = get_start_inline_keyboard(new_lang)

    await callback.message.edit_text(text=success_text, parse_mode="HTML", reply_markup=kb)
    await callback.answer(t("lang_changed", new_lang))

    # Also update persistent reply keyboard
    await callback.message.answer(
        t("start_bottom_hint", new_lang),
        reply_markup=get_main_reply_keyboard(new_lang)
    )
