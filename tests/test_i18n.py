import pytest
from app.core.i18n import (
    SUPPORTED_LANGUAGES,
    TRANSLATIONS,
    normalize_language_code,
    t
)
from app.telegram.keyboards.menu import (
    get_main_reply_keyboard,
    get_start_inline_keyboard,
    get_pro_inline_keyboard,
    get_language_inline_keyboard,
    get_pagination_keyboard
)
from app.telegram.keyboards.settings import (
    get_settings_keyboard,
    get_delete_confirmation_keyboard
)
from app.models.settings import UserSettings


def test_i18n_keys_parity():
    """Ensures all supported languages have the exact same translation keys."""
    uz_keys = set(TRANSLATIONS["uz"].keys())
    ru_keys = set(TRANSLATIONS["ru"].keys())
    en_keys = set(TRANSLATIONS["en"].keys())

    missing_in_ru = uz_keys - ru_keys
    missing_in_en = uz_keys - en_keys
    extra_in_ru = ru_keys - uz_keys
    extra_in_en = en_keys - uz_keys

    assert not missing_in_ru, f"Missing RU keys: {missing_in_ru}"
    assert not missing_in_en, f"Missing EN keys: {missing_in_en}"
    assert not extra_in_ru, f"Extra RU keys: {extra_in_ru}"
    assert not extra_in_en, f"Extra EN keys: {extra_in_en}"


def test_normalize_language_code():
    assert normalize_language_code("ru") == "ru"
    assert normalize_language_code("ru-RU") == "ru"
    assert normalize_language_code("en") == "en"
    assert normalize_language_code("en-US") == "en"
    assert normalize_language_code("uz") == "uz"
    assert normalize_language_code(None) == "uz"
    assert normalize_language_code("fr") == "uz"


def test_translation_formatting():
    # Interpolation test
    formatted_uz = t("start_guide", "uz", bot_username="testbot")
    assert "@testbot" in formatted_uz

    formatted_ru = t("start_guide", "ru", bot_username="testbot")
    assert "@testbot" in formatted_ru

    formatted_en = t("start_guide", "en", bot_username="testbot")
    assert "@testbot" in formatted_en

    # Fallback test
    fallback = t("btn_pro", "de")
    assert fallback == t("btn_pro", "uz")


def test_localized_keyboards():
    for lang in ["uz", "ru", "en"]:
        # Reply menu
        kb = get_main_reply_keyboard(lang)
        assert len(kb.keyboard) == 2

        # Start inline
        start_kb = get_start_inline_keyboard(lang)
        assert len(start_kb.inline_keyboard) >= 3

        # PRO inline
        pro_kb_inactive = get_pro_inline_keyboard(lang, is_active=False)
        assert len(pro_kb_inactive.inline_keyboard) == 2
        pro_kb_active = get_pro_inline_keyboard(lang, is_active=True, auto_renew=True)
        assert len(pro_kb_active.inline_keyboard) == 2

        # Language inline
        lang_kb = get_language_inline_keyboard(lang)
        assert len(lang_kb.inline_keyboard) == len(SUPPORTED_LANGUAGES) + 1

        # Pagination
        pag_kb = get_pagination_keyboard(1, 5, "prefix", lang)
        assert len(pag_kb.inline_keyboard) == 1

        # Settings
        dummy_settings = UserSettings(user_id=None)
        settings_kb = get_settings_keyboard(dummy_settings, lang)
        assert len(settings_kb.inline_keyboard) >= 7

        del_kb = get_delete_confirmation_keyboard(lang)
        assert len(del_kb.inline_keyboard) == 1
