from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from app.models.settings import UserSettings
from app.core.i18n import t


def get_settings_keyboard(settings: UserSettings, lang: str = "uz") -> InlineKeyboardMarkup:
    """Returns interactive toggle keyboard for user notification preferences."""
    def mark(val: bool) -> str:
        return f"🟢 {t('status_on', lang)}" if val else f"🔴 {t('status_off', lang)}"

    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(
                text=f"{t('toggle_deleted_text', lang)}: {mark(settings.notify_deleted_text)}",
                callback_data="toggle:notify_deleted_text"
            )],
            [InlineKeyboardButton(
                text=f"{t('toggle_edited_messages', lang)}: {mark(settings.notify_edited_messages)}",
                callback_data="toggle:notify_edited_messages"
            )],
            [InlineKeyboardButton(
                text=f"{t('toggle_deleted_photos', lang)}: {mark(settings.notify_deleted_photos)}",
                callback_data="toggle:notify_deleted_photos"
            )],
            [InlineKeyboardButton(
                text=f"{t('toggle_deleted_videos', lang)}: {mark(settings.notify_deleted_videos)}",
                callback_data="toggle:notify_deleted_videos"
            )],
            [InlineKeyboardButton(
                text=f"{t('toggle_deleted_voice', lang)}: {mark(settings.notify_deleted_voice)}",
                callback_data="toggle:notify_deleted_voice"
            )],
            [InlineKeyboardButton(
                text=f"{t('toggle_all_notifications', lang)}: {mark(settings.notifications_enabled)}",
                callback_data="toggle:notifications_enabled"
            )],
            [InlineKeyboardButton(
                text=t("btn_change_lang", lang),
                callback_data="menu_lang"
            )],
            [InlineKeyboardButton(
                text=t("btn_delete_my_data", lang),
                callback_data="confirm_delete_data"
            )],
            [InlineKeyboardButton(
                text=t("btn_main_menu", lang),
                callback_data="menu_main"
            )]
        ]
    )


def get_delete_confirmation_keyboard(lang: str = "uz") -> InlineKeyboardMarkup:
    """Returns confirmation keyboard for data deletion."""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text=t("btn_cancel", lang), callback_data="menu_settings"),
                InlineKeyboardButton(text=t("btn_confirm_delete", lang), callback_data="do_delete_data")
            ]
        ]
    )
