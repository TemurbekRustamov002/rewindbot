import logging
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command
from sqlalchemy import select
from app.db.session import async_session_factory
from app.services.subscription_service import subscription_service
from app.services.search_service import search_service
from app.models.settings import UserSettings
from app.telegram.keyboards.settings import get_settings_keyboard, get_delete_confirmation_keyboard
from app.core.i18n import t

logger = logging.getLogger(__name__)
settings_router = Router(name="settings_router")


async def get_or_create_user_settings(session, user_id):
    query = select(UserSettings).where(UserSettings.user_id == user_id)
    res = await session.execute(query)
    s = res.scalar_one_or_none()
    if not s:
        s = UserSettings(user_id=user_id)
        session.add(s)
        await session.flush()
    return s


@settings_router.message(F.text.in_(["⚙️ Sozlamalar", "⚙️ Настройки", "⚙️ Settings"]))
@settings_router.message(Command("settings"))
@settings_router.callback_query(F.data == "menu_settings")
async def handle_settings_menu(event: Message | CallbackQuery):
    """Shows user preferences and toggle switches in chosen language."""
    telegram_user_id = event.from_user.id

    async with async_session_factory() as session:
        user = await subscription_service.get_or_create_user(session, telegram_user_id)
        user_lang = user.language or "uz"
        s = await get_or_create_user_settings(session, user.id)
        kb = get_settings_keyboard(s, lang=user_lang)
        await session.commit()

    text = t("settings_title", user_lang)

    if isinstance(event, CallbackQuery):
        await event.message.edit_text(text=text, parse_mode="HTML", reply_markup=kb)
        await event.answer()
    else:
        await event.answer(text=text, parse_mode="HTML", reply_markup=kb)


@settings_router.callback_query(F.data.startswith("toggle:"))
async def handle_toggle_setting(callback: CallbackQuery):
    """Toggles notification boolean fields."""
    field_name = callback.data.split(":")[-1]
    telegram_user_id = callback.from_user.id

    async with async_session_factory() as session:
        user = await subscription_service.get_or_create_user(session, telegram_user_id)
        user_lang = user.language or "uz"
        s = await get_or_create_user_settings(session, user.id)

        if hasattr(s, field_name):
            current_val = getattr(s, field_name)
            setattr(s, field_name, not current_val)
            await session.flush()

        kb = get_settings_keyboard(s, lang=user_lang)
        await session.commit()

    await callback.message.edit_reply_markup(reply_markup=kb)
    await callback.answer(t("settings_updated", user_lang))


@settings_router.message(Command("delete_my_data"))
@settings_router.callback_query(F.data == "confirm_delete_data")
async def handle_confirm_delete_data(event: Message | CallbackQuery):
    """Presents confirmation dialog before permanent GDPR data purging."""
    telegram_user_id = event.from_user.id
    async with async_session_factory() as session:
        user = await subscription_service.get_or_create_user(session, telegram_user_id)
        user_lang = user.language or "uz"

    text = t("delete_data_confirm", user_lang)
    kb = get_delete_confirmation_keyboard(lang=user_lang)

    if isinstance(event, CallbackQuery):
        await event.message.edit_text(text=text, parse_mode="HTML", reply_markup=kb)
        await event.answer()
    else:
        await event.answer(text=text, parse_mode="HTML", reply_markup=kb)


@settings_router.callback_query(F.data == "do_delete_data")
async def handle_execute_delete_data(callback: CallbackQuery):
    """Purges all user data."""
    telegram_user_id = callback.from_user.id

    async with async_session_factory() as session:
        user = await subscription_service.get_or_create_user(session, telegram_user_id)
        user_lang = user.language or "uz"
        success = await search_service.delete_all_user_data(session, user)

    if success:
        text = t("delete_data_success", user_lang)
    else:
        text = t("delete_data_error", user_lang)

    await callback.message.edit_text(text=text, parse_mode="HTML")
    await callback.answer()
