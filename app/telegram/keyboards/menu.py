from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup, KeyboardButton
from app.core.i18n import t, SUPPORTED_LANGUAGES


def get_main_reply_keyboard(lang: str = "uz") -> ReplyKeyboardMarkup:
    """Returns modern persistent reply menu keyboard localized by language."""
    return ReplyKeyboardMarkup(
        keyboard=[
            [
                KeyboardButton(text=t("btn_pro", lang)),
                KeyboardButton(text=t("btn_status", lang))
            ],
            [
                KeyboardButton(text=t("btn_settings", lang)),
                KeyboardButton(text=t("btn_language", lang)),
                KeyboardButton(text=t("btn_help", lang))
            ]
        ],
        resize_keyboard=True
    )


def get_start_inline_keyboard(lang: str = "uz") -> InlineKeyboardMarkup:
    """Returns modern onboarding start keyboard."""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text=t("btn_connect_guide", lang), callback_data="guide_connect")],
            [
                InlineKeyboardButton(text=t("btn_pro_plans", lang), callback_data="menu_pro"),
                InlineKeyboardButton(text=t("btn_change_lang", lang), callback_data="menu_lang")
            ],
            [InlineKeyboardButton(text=t("btn_about", lang), callback_data="menu_help")]
        ]
    )


def get_pro_inline_keyboard(lang: str = "uz", is_active: bool = False, auto_renew: bool = True) -> InlineKeyboardMarkup:
    """Returns subscription management keyboard."""
    buttons = []
    if not is_active:
        buttons.append([InlineKeyboardButton(text=t("btn_activate_pro", lang), callback_data="buy_pro_stars")])
    else:
        if auto_renew:
            buttons.append([InlineKeyboardButton(text=t("btn_disable_autorenew", lang), callback_data="cancel_pro_autorenew")])
        else:
            buttons.append([InlineKeyboardButton(text=t("btn_enable_autorenew", lang), callback_data="enable_pro_autorenew")])
    buttons.append([InlineKeyboardButton(text=t("btn_main_menu", lang), callback_data="menu_main")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def get_language_inline_keyboard(current_lang: str = "uz") -> InlineKeyboardMarkup:
    """Returns language selection keyboard with active language indicator."""
    buttons = []
    for code, label in SUPPORTED_LANGUAGES.items():
        is_active = " ✓" if code == current_lang else ""
        buttons.append([InlineKeyboardButton(text=f"{label}{is_active}", callback_data=f"set_lang:{code}")])
    buttons.append([InlineKeyboardButton(text=t("btn_back", current_lang), callback_data="menu_main")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def get_pagination_keyboard(current_page: int, total_pages: int, prefix: str, lang: str = "uz") -> InlineKeyboardMarkup:
    """Returns localized pagination keyboard: ⬅️ 1 / 12 ➡️"""
    nav_row = []
    if current_page > 1:
        nav_row.append(InlineKeyboardButton(text=t("btn_prev", lang), callback_data=f"{prefix}:page:{current_page - 1}"))

    nav_row.append(InlineKeyboardButton(text=f"✦ {current_page} / {max(1, total_pages)} ✦", callback_data="noop"))

    if current_page < total_pages:
        nav_row.append(InlineKeyboardButton(text=t("btn_next", lang), callback_data=f"{prefix}:page:{current_page + 1}"))

    return InlineKeyboardMarkup(inline_keyboard=[nav_row])
