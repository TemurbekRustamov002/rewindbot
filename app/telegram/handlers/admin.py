import logging
from typing import Optional
from datetime import datetime
from aiogram import Router
from aiogram.types import Message
from aiogram.filters import Command
from sqlalchemy import select, func
from app.db.session import async_session_factory
from app.models.user import User
from app.models.business_connection import BusinessConnection
from app.models.subscription import Subscription, Payment
from app.models.message import Message as DBMessage
from app.services.subscription_service import subscription_service
from app.core.config import settings
from app.core.i18n import t
from app.telegram.bot import bot

logger = logging.getLogger(__name__)
admin_router = Router(name="admin_router")


async def is_super_admin(user_id: int, session) -> bool:
    """Checks if telegram_user_id is a Super Admin."""
    if user_id in settings.ADMIN_USER_IDS:
        return True
    q = select(User).where(User.telegram_user_id == user_id, User.is_super_admin == True)
    res = await session.execute(q)
    return res.scalar_one_or_none() is not None


async def is_admin_user(user_id: int, session) -> bool:
    """Checks if telegram_user_id is an Admin or Super Admin."""
    if await is_super_admin(user_id, session):
        return True
    q = select(User).where(User.telegram_user_id == user_id, User.is_admin == True)
    res = await session.execute(q)
    return res.scalar_one_or_none() is not None


@admin_router.message(Command("admin"))
async def handle_admin_dashboard(message: Message):
    """Admin dashboard and management menu."""
    user_id = message.from_user.id
    async with async_session_factory() as session:
        if not await is_admin_user(user_id, session):
            return

        super_admin = await is_super_admin(user_id, session)

        # Metrics
        total_users = (await session.execute(select(func.count(User.id)))).scalar_one()
        active_conns = (await session.execute(
            select(func.count(BusinessConnection.id)).where(BusinessConnection.is_enabled == True)
        )).scalar_one()

        active_subs = (await session.execute(
            select(func.count(Subscription.id)).where(Subscription.status == "ACTIVE")
        )).scalar_one()
        total_revenue_stars = (await session.execute(
            select(func.sum(Payment.amount))
        )).scalar_one() or 0

        total_messages = (await session.execute(select(func.count(DBMessage.id)))).scalar_one()
        deleted_messages = (await session.execute(
            select(func.count(DBMessage.id)).where(DBMessage.is_deleted == True)
        )).scalar_one()

        admins_count = (await session.execute(
            select(func.count(User.id)).where(User.is_admin == True)
        )).scalar_one()

    role_badge = "👑 <b>Super Admin</b>" if super_admin else "⭐️ <b>Admin</b>"

    text = (
        f"📊 <b>Rewind Admin Boshqaruv Paneli</b> ({role_badge})\n\n"
        f"👥 Jami foydalanuvchilar: <b>{total_users}</b>\n"
        f"⭐️ Adminlar soni: <b>{admins_count + len(settings.ADMIN_USER_IDS)}</b>\n"
        f"🔗 Faol Business ulanishlar: <b>{active_conns}</b>\n\n"
        f"💎 Faol PRO obunachilar: <b>{active_subs}</b>\n"
        f"⭐ Jami tushum (Stars): <b>{total_revenue_stars} XTR</b>\n\n"
        f"📨 Jami xabarlar arxivi: <b>{total_messages}</b>\n"
        f"🗑 O‘chirilgan xabarlar: <b>{deleted_messages}</b>\n\n"
        "<blockquote><b>Boshqaruv buyruqlari:</b>\n"
        "• <code>/give_pro {id/@user} {kunlar}</code> — Tekin PRO berish\n"
        "• <code>/revoke_pro {id/@user}</code> — PRO obunani bekor qilish\n"
        "• <code>/add_admin {id/@user}</code> — Yangi admin tayinlash\n"
        "• <code>/remove_admin {id/@user}</code> — Adminlikni bekor qilish\n"
        "• <code>/admins</code> — Barcha adminlar ro‘yxati\n"
        "• <code>/refund {charge_id}</code> — Stars to‘lovini qaytarish</blockquote>"
    )
    await message.answer(text=text, parse_mode="HTML")


@admin_router.message(Command("give_pro"))
async def handle_give_pro(message: Message):
    """Super Admin command to grant free PRO subscription to any user."""
    sender_id = message.from_user.id
    async with async_session_factory() as session:
        if not await is_super_admin(sender_id, session):
            await message.answer("⚠️ Bu buyruq faqat <b>Super Admin</b> uchun ruxsat etilgan.", parse_mode="HTML")
            return

        args = message.text.split()
        if len(args) < 2:
            await message.answer(
                "ℹ️ <b>Format:</b> <code>/give_pro {user_id_yoki_@username} [kunlar]</code>\n\n"
                "<i>Misol:</i> <code>/give_pro 7728111589 30</code> yoki <code>/give_pro @username 90</code>",
                parse_mode="HTML"
            )
            return

        target_id_str = args[1]
        days = 30
        if len(args) >= 3 and args[2].isdigit():
            days = int(args[2])

        target_user = await subscription_service.find_user_by_id_or_username(session, target_id_str)
        if not target_user:
            await message.answer(f"❌ Foydalanuvchi (<code>{target_id_str}</code>) ma'lumotlar bazasidan topilmadi.", parse_mode="HTML")
            return

        sub = await subscription_service.grant_free_pro(session, target_user, days=days)
        await session.commit()

        exp_str = sub.expires_at.strftime("%d.%m.%Y")
        user_lang = target_user.language or "uz"

        # Notify recipient user
        try:
            user_msg = t("pro_granted_user", user_lang, days=days, exp_date=exp_str)
            await bot.send_message(chat_id=target_user.telegram_user_id, text=user_msg, parse_mode="HTML")
        except Exception as e:
            logger.warning(f"Could not notify recipient user {target_user.telegram_user_id}: {e}")

        # Confirm to Super Admin
        uname = f"@{target_user.username}" if target_user.username else f"ID: {target_user.telegram_user_id}"
        await message.answer(
            f"✅ <b>PRO obuna muvaffaqiyatli berildi!</b>\n\n"
            f"👤 Foydalanuvchi: <b>{uname}</b> (<code>{target_user.telegram_user_id}</code>)\n"
            f"⏳ Berilgan muddat: <b>{days} kun</b>\n"
            f"📅 Amal qilish muddati: <b><code>{exp_str}</code></b>",
            parse_mode="HTML"
        )


@admin_router.message(Command("revoke_pro"))
async def handle_revoke_pro(message: Message):
    """Super Admin command to revoke PRO subscription."""
    sender_id = message.from_user.id
    async with async_session_factory() as session:
        if not await is_super_admin(sender_id, session):
            await message.answer("⚠️ Bu buyruq faqat <b>Super Admin</b> uchun ruxsat etilgan.", parse_mode="HTML")
            return

        args = message.text.split()
        if len(args) < 2:
            await message.answer("ℹ️ <b>Format:</b> <code>/revoke_pro {user_id_yoki_@username}</code>", parse_mode="HTML")
            return

        target_user = await subscription_service.find_user_by_id_or_username(session, args[1])
        if not target_user:
            await message.answer(f"❌ Foydalanuvchi (<code>{args[1]}</code>) topilmadi.", parse_mode="HTML")
            return

        await subscription_service.revoke_pro(session, target_user)
        await session.commit()

        try:
            user_lang = target_user.language or "uz"
            await bot.send_message(chat_id=target_user.telegram_user_id, text=t("pro_revoked_user", user_lang), parse_mode="HTML")
        except Exception:
            pass

        await message.answer(f"✅ Foydalanuvchi (<code>{target_user.telegram_user_id}</code>) PRO obunasi bekor qilindi.", parse_mode="HTML")


@admin_router.message(Command("add_admin"))
async def handle_add_admin(message: Message):
    """Super Admin command to appoint a new Admin."""
    sender_id = message.from_user.id
    async with async_session_factory() as session:
        if not await is_super_admin(sender_id, session):
            await message.answer("⚠️ Bu buyruq faqat <b>Super Admin</b> uchun ruxsat etilgan.", parse_mode="HTML")
            return

        args = message.text.split()
        if len(args) < 2:
            await message.answer(
                "ℹ️ <b>Format:</b> <code>/add_admin {user_id_yoki_@username}</code>",
                parse_mode="HTML"
            )
            return

        target_user = await subscription_service.find_user_by_id_or_username(session, args[1])
        if not target_user:
            await message.answer(f"❌ Foydalanuvchi (<code>{args[1]}</code>) ma'lumotlar bazasidan topilmadi.", parse_mode="HTML")
            return

        target_user.is_admin = True
        await session.commit()

        try:
            user_lang = target_user.language or "uz"
            await bot.send_message(chat_id=target_user.telegram_user_id, text=t("admin_added_user", user_lang), parse_mode="HTML")
        except Exception:
            pass

        uname = f"@{target_user.username}" if target_user.username else f"ID: {target_user.telegram_user_id}"
        await message.answer(
            f"✅ <b>Foydalanuvchi muvaffaqiyatli Admin etib tayinlandi!</b>\n\n"
            f"👤 Admin: <b>{uname}</b> (<code>{target_user.telegram_user_id}</code>)",
            parse_mode="HTML"
        )


@admin_router.message(Command("remove_admin"))
async def handle_remove_admin(message: Message):
    """Super Admin command to remove an Admin."""
    sender_id = message.from_user.id
    async with async_session_factory() as session:
        if not await is_super_admin(sender_id, session):
            await message.answer("⚠️ Bu buyruq faqat <b>Super Admin</b> uchun ruxsat etilgan.", parse_mode="HTML")
            return

        args = message.text.split()
        if len(args) < 2:
            await message.answer("ℹ️ <b>Format:</b> <code>/remove_admin {user_id_yoki_@username}</code>", parse_mode="HTML")
            return

        target_user = await subscription_service.find_user_by_id_or_username(session, args[1])
        if not target_user:
            await message.answer(f"❌ Foydalanuvchi (<code>{args[1]}</code>) topilmadi.", parse_mode="HTML")
            return

        target_user.is_admin = False
        await session.commit()

        try:
            user_lang = target_user.language or "uz"
            await bot.send_message(chat_id=target_user.telegram_user_id, text=t("admin_removed_user", user_lang), parse_mode="HTML")
        except Exception:
            pass

        await message.answer(f"✅ Admin (<code>{target_user.telegram_user_id}</code>) adminlik huquqidan ozod qilindi.", parse_mode="HTML")


@admin_router.message(Command("admins"))
async def handle_list_admins(message: Message):
    """Lists all current Admins and Super Admins."""
    sender_id = message.from_user.id
    async with async_session_factory() as session:
        if not await is_admin_user(sender_id, session):
            return

        # Super Admins
        super_admin_ids = set(settings.ADMIN_USER_IDS)
        db_super_admins = (await session.execute(select(User).where(User.is_super_admin == True))).scalars().all()
        for su in db_super_admins:
            super_admin_ids.add(su.telegram_user_id)

        # Regular Admins
        db_admins = (await session.execute(select(User).where(User.is_admin == True))).scalars().all()

    lines = ["👑 <b>SUPER ADMINLAR:</b>"]
    for sa_id in super_admin_ids:
        lines.append(f"• <code>{sa_id}</code>")

    lines.append("\n⭐️ <b>TAYINLANGAN ADMINLAR:</b>")
    if db_admins:
        for a in db_admins:
            uname = f"@{a.username}" if a.username else f"ID: {a.telegram_user_id}"
            lines.append(f"• <b>{uname}</b> (<code>{a.telegram_user_id}</code>)")
    else:
        lines.append("<i>Tayinlangan adminlar mavjud emas.</i>")

    await message.answer("\n".join(lines), parse_mode="HTML")


@admin_router.message(Command("refund"))
async def handle_admin_refund(message: Message):
    """Admin Telegram Stars refund command."""
    sender_id = message.from_user.id
    async with async_session_factory() as session:
        if not await is_admin_user(sender_id, session):
            return

    args = message.text.split()
    if len(args) < 2:
        await message.answer("Format: <code>/refund {telegram_payment_charge_id}</code>", parse_mode="HTML")
        return

    charge_id = args[1].strip()

    try:
        await bot.refund_star_payment(
            user_id=message.from_user.id,
            telegram_payment_charge_id=charge_id
        )
        async with async_session_factory() as session:
            p_q = select(Payment).where(Payment.telegram_payment_charge_id == charge_id)
            payment = (await session.execute(p_q)).scalar_one_or_none()
            if payment and payment.subscription:
                payment.subscription.status = "REFUNDED"
            await session.commit()

        await message.answer(f"✅ To‘lov ({charge_id}) muvaffaqiyatli qaytarildi (Refund).")
    except Exception as e:
        logger.error(f"Refund error: {e}")
        await message.answer(f"❌ Qaytarishda xatolik: {e}")
