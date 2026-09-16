import uuid
import logging
from aiogram import Router, F
from aiogram.types import (
    Message,
    CallbackQuery,
    PreCheckoutQuery,
    LabeledPrice,
)
from aiogram.filters import Command
from app.db.session import async_session_factory
from app.services.subscription_service import subscription_service
from app.core.config import settings
from app.telegram.keyboards.menu import get_pro_inline_keyboard
from app.core.i18n import t

logger = logging.getLogger(__name__)
subscription_router = Router(name="subscription_router")


@subscription_router.message(F.text.in_(["💎 Obuna (PRO)", "💎 PRO Obuna", "💎 PRO Подписка", "💎 PRO Subscription"]))
@subscription_router.message(Command("pro"))
@subscription_router.callback_query(F.data == "menu_pro")
async def handle_pro_menu(event: Message | CallbackQuery):
    """Shows subscription plans, pricing in Telegram Stars, and status in user language."""
    telegram_user_id = event.from_user.id

    async with async_session_factory() as session:
        user = await subscription_service.get_or_create_user(
            session=session,
            telegram_user_id=telegram_user_id
        )
        user_lang = user.language or "uz"
        has_access, status_label = await subscription_service.has_active_access(session, user)

    is_paid = (status_label == "PAID_ACTIVE")
    status_display = {
        "TRIAL_ACTIVE": t("status_trial", user_lang),
        "PAID_ACTIVE": t("status_pro_active", user_lang),
        "EXPIRED": t("status_expired", user_lang)
    }.get(status_label, status_label)

    text = (
        f"{t('pro_title', user_lang)}\n\n"
        f"{t('pro_status_label', user_lang)} <b>{status_display}</b>\n\n"
        f"{t('pro_features', user_lang)}"
    )

    kb = get_pro_inline_keyboard(lang=user_lang, is_active=is_paid)

    if isinstance(event, CallbackQuery):
        await event.message.edit_text(text=text, parse_mode="HTML", reply_markup=kb)
        await event.answer()
    else:
        await event.answer(text=text, parse_mode="HTML", reply_markup=kb)


@subscription_router.callback_query(F.data == "buy_pro_stars")
async def handle_buy_stars_invoice(callback: CallbackQuery):
    """Creates Telegram Stars Invoice for 50 Stars / 30 days subscription."""
    telegram_user_id = callback.from_user.id
    async with async_session_factory() as session:
        user = await subscription_service.get_or_create_user(
            session=session,
            telegram_user_id=telegram_user_id
        )
        user_lang = user.language or "uz"

    invoice_payload = f"rewind_pro:{telegram_user_id}:{uuid.uuid4().hex[:8]}"

    prices = [
        LabeledPrice(label=t("invoice_price_label", user_lang), amount=settings.PRO_SUBSCRIPTION_STARS)
    ]

    try:
        await callback.message.answer_invoice(
            title=t("invoice_title", user_lang),
            description=t("invoice_description", user_lang),
            payload=invoice_payload,
            provider_token="",  # Must be empty string for Telegram Stars (XTR)
            currency="XTR",
            prices=prices,
            start_parameter="pro-subscription"
        )
        await callback.answer()
    except Exception as e:
        logger.error(f"Failed to create Stars invoice: {e}", exc_info=True)
        await callback.answer(t("invoice_error", user_lang), show_alert=True)


@subscription_router.pre_checkout_query()
async def handle_pre_checkout(pre_checkout_query: PreCheckoutQuery):
    """
    Validates invoice payload and price before payment completes.
    Must respond with answer_pre_checkout_query(ok=True) within 10s.
    """
    telegram_user_id = pre_checkout_query.from_user.id
    async with async_session_factory() as session:
        user = await subscription_service.get_or_create_user(
            session=session,
            telegram_user_id=telegram_user_id
        )
        user_lang = user.language or "uz"

    if pre_checkout_query.currency != "XTR":
        await pre_checkout_query.answer(ok=False, error_message=t("pre_checkout_error_currency", user_lang))
        return

    if pre_checkout_query.total_amount != settings.PRO_SUBSCRIPTION_STARS:
        await pre_checkout_query.answer(ok=False, error_message=t("pre_checkout_error_amount", user_lang))
        return

    await pre_checkout_query.answer(ok=True)


@subscription_router.message(F.successful_payment)
async def handle_successful_payment(message: Message):
    """
    FR-38: Processes successful Stars payment and activates/extends the PRO subscription.
    """
    payment_info = message.successful_payment
    charge_id = payment_info.telegram_payment_charge_id
    total_amount = payment_info.total_amount
    is_recurring = getattr(payment_info, "is_recurring", False)
    is_first_recurring = getattr(payment_info, "is_first_recurring", False)
    expiration_date = getattr(payment_info, "subscription_expiration_date", None)

    async with async_session_factory() as session:
        user = await subscription_service.get_or_create_user(
            session=session,
            telegram_user_id=message.from_user.id
        )
        user_lang = user.language or "uz"

        sub = await subscription_service.activate_stars_subscription(
            session=session,
            user=user,
            telegram_payment_charge_id=charge_id,
            amount=total_amount,
            is_recurring=is_recurring,
            is_first_recurring=is_first_recurring,
            expiration_date=expiration_date,
            raw_payload_json=payment_info.model_dump_json()
        )
        await session.commit()

    exp_str = sub.expires_at.strftime("%d.%m.%Y")
    success_text = t("payment_success", user_lang, exp_date=exp_str)
    await message.answer(
        text=success_text,
        parse_mode="HTML"
    )
