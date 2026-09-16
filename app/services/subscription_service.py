import logging
from datetime import datetime, timezone, timedelta
from typing import Optional, Tuple
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.user import User
from app.models.subscription import Subscription, Payment
from app.core.config import settings

logger = logging.getLogger(__name__)


def ensure_utc(dt: Optional[datetime]) -> Optional[datetime]:
    """Ensures datetime is timezone-aware in UTC (fixes SQLite naive datetime issues)."""
    if dt is None:
        return None
    if dt.tzinfo is None:
        return dt.replace(tzinfo=timezone.utc)
    return dt


class SubscriptionService:
    async def get_or_create_user(
        self,
        session: AsyncSession,
        telegram_user_id: int,
        username: Optional[str] = None,
        first_name: Optional[str] = None,
        last_name: Optional[str] = None,
        language: str = "uz"
    ) -> User:
        """Gets existing user or creates a new one."""
        query = select(User).where(User.telegram_user_id == telegram_user_id)
        result = await session.execute(query)
        user = result.scalar_one_or_none()

        if not user:
            user = User(
                telegram_user_id=telegram_user_id,
                username=username,
                first_name=first_name,
                last_name=last_name,
                language=language,
                trial_used=False,
                status="ACTIVE"
            )
            session.add(user)
            await session.flush()
        else:
            # Update profile info if changed
            if username and user.username != username:
                user.username = username
            if first_name and user.first_name != first_name:
                user.first_name = first_name
            if last_name and user.last_name != last_name:
                user.last_name = last_name

        return user

    async def initialize_trial_on_connection(
        self,
        session: AsyncSession,
        user: User
    ) -> bool:
        """
        Activates 72-hour trial if not used previously.
        Per TZ rule: Trial starts strictly when Business Connection is first enabled.
        """
        if not user.trial_used:
            now = datetime.now(timezone.utc)
            user.trial_used = True
            user.trial_started_at = now
            user.trial_expires_at = now + timedelta(hours=settings.TRIAL_HOURS)
            await session.flush()
            logger.info(f"User {user.telegram_user_id} activated 72h trial until {user.trial_expires_at}")
            return True
        return False

    async def has_active_access(
        self,
        session: AsyncSession,
        user: User
    ) -> Tuple[bool, str]:
        """
        Verifies if user has valid active subscription or trial.
        Returns (has_access, status_label).
        """
        # 0. Admin bypass - admins configured in settings or with is_admin/is_super_admin always have active PRO access
        if user.telegram_user_id in settings.ADMIN_USER_IDS or getattr(user, "is_admin", False) or getattr(user, "is_super_admin", False):
            return True, "PAID_ACTIVE"

        now = datetime.now(timezone.utc)

        # 1. Check paid active subscriptions
        query = select(Subscription).where(
            Subscription.user_id == user.id,
            Subscription.status.in_(["ACTIVE", "CANCELED_PENDING_EXPIRY"])
        ).order_by(Subscription.expires_at.desc())

        result = await session.execute(query)
        active_subs = result.scalars().all()
        for sub in active_subs:
            sub_exp = ensure_utc(sub.expires_at)
            if sub_exp and sub_exp > now:
                return True, "PAID_ACTIVE"

        # 2. Check trial
        trial_exp = ensure_utc(user.trial_expires_at)
        if trial_exp and trial_exp > now:
            return True, "TRIAL_ACTIVE"

        return False, "EXPIRED"

    async def grant_free_pro(
        self,
        session: AsyncSession,
        user: User,
        days: int = 30
    ) -> Subscription:
        """Grants or extends free PRO subscription for a user."""
        import uuid
        now = datetime.now(timezone.utc)
        target_exp = now + timedelta(days=days)

        query = select(Subscription).where(
            Subscription.user_id == user.id,
            Subscription.status.in_(["ACTIVE", "CANCELED_PENDING_EXPIRY"])
        ).order_by(Subscription.expires_at.desc())
        result = await session.execute(query)
        sub = result.scalar_one_or_none()

        if sub:
            curr_exp = ensure_utc(sub.expires_at)
            if curr_exp and curr_exp > now:
                sub.expires_at = curr_exp + timedelta(days=days)
            else:
                sub.expires_at = target_exp
            sub.status = "ACTIVE"
        else:
            sub = Subscription(
                user_id=user.id,
                plan_type="PRO",
                status="ACTIVE",
                started_at=now,
                expires_at=target_exp,
                auto_renew=False,
                telegram_charge_id=f"admin_grant_{uuid.uuid4().hex[:8]}"
            )
            session.add(sub)

        await session.flush()
        logger.info(f"Granted free PRO to user {user.telegram_user_id} for {days} days until {sub.expires_at}")
        return sub

    async def revoke_pro(
        self,
        session: AsyncSession,
        user: User
    ) -> bool:
        """Revokes active PRO subscription."""
        now = datetime.now(timezone.utc)
        query = select(Subscription).where(
            Subscription.user_id == user.id,
            Subscription.status == "ACTIVE"
        )
        result = await session.execute(query)
        subs = result.scalars().all()
        for s in subs:
            s.status = "REVOKED"
            s.expires_at = now

        if user.trial_expires_at:
            user.trial_expires_at = now
        await session.flush()
        return True

    async def find_user_by_id_or_username(
        self,
        session: AsyncSession,
        identifier: str
    ) -> Optional[User]:
        """Finds user by telegram_user_id or username."""
        clean_id = identifier.strip().lstrip("@")
        if clean_id.isdigit():
            q = select(User).where(User.telegram_user_id == int(clean_id))
        else:
            q = select(User).where(User.username.ilike(clean_id))
        res = await session.execute(q)
        return res.scalar_one_or_none()

    async def activate_stars_subscription(
        self,
        session: AsyncSession,
        user: User,
        telegram_payment_charge_id: str,
        amount: int,
        is_recurring: bool = True,
        is_first_recurring: bool = True,
        expiration_date: Optional[datetime] = None,
        raw_payload_json: Optional[str] = None
    ) -> Subscription:
        """Activates or renews a PRO subscription upon receiving Telegram Stars payment."""
        now = datetime.now(timezone.utc)

        # Determine expiration: Telegram provided date or default 30 days
        expires_at = expiration_date if expiration_date else now + timedelta(days=settings.PRO_SUBSCRIPTION_PERIOD_DAYS)

        # Create or update subscription
        query = select(Subscription).where(
            Subscription.user_id == user.id,
            Subscription.status.in_(["ACTIVE", "CANCELED_PENDING_EXPIRY"])
        ).order_by(Subscription.expires_at.desc())
        result = await session.execute(query)
        sub = result.scalar_one_or_none()

        if sub:
            sub.expires_at = max(sub.expires_at, expires_at)
            sub.status = "ACTIVE"
            sub.auto_renew = is_recurring
            sub.telegram_charge_id = telegram_payment_charge_id
        else:
            sub = Subscription(
                user_id=user.id,
                plan_type="PRO",
                status="ACTIVE",
                started_at=now,
                expires_at=expires_at,
                auto_renew=is_recurring,
                telegram_charge_id=telegram_payment_charge_id
            )
            session.add(sub)
            await session.flush()

        # Record payment transaction (Idempotent via unique telegram_payment_charge_id)
        payment = Payment(
            user_id=user.id,
            subscription_id=sub.id,
            telegram_payment_charge_id=telegram_payment_charge_id,
            currency="XTR",
            amount=amount,
            is_recurring=is_recurring,
            is_first_recurring=is_first_recurring,
            payment_date=now,
            subscription_expiration_date=expires_at,
            raw_payload_json=raw_payload_json
        )
        session.add(payment)
        await session.flush()

        logger.info(f"User {user.telegram_user_id} successfully subscribed to PRO until {expires_at}")
        return sub

    async def resolve_business_connection(
        self,
        session: AsyncSession,
        bot,
        business_connection_id: str
    ) -> Optional[Tuple["BusinessConnection", User]]:
        """
        Robustly and accurately resolves BusinessConnection and User owner.
        1. Checks database by unique business_connection_id.
        2. If not found in DB, fetches real connection metadata from Telegram Bot API.
        3. Never guesses or defaults to arbitrary user IDs.
        """
        from app.models.business_connection import BusinessConnection

        # 1. Search local DB
        query = (
            select(BusinessConnection, User)
            .join(User, BusinessConnection.user_id == User.id)
            .where(BusinessConnection.business_connection_id == business_connection_id)
        )
        result = await session.execute(query)
        row = result.first()
        if row:
            conn, user = row
            return conn, user

        # 2. Query Telegram Bot API for real owner
        try:
            tg_conn = await bot.get_business_connection(business_connection_id=business_connection_id)
            if not tg_conn or not tg_conn.user:
                logger.warning(f"Business connection {business_connection_id} not found on Telegram API.")
                return None

            user = await self.get_or_create_user(
                session=session,
                telegram_user_id=tg_conn.user.id,
                username=tg_conn.user.username,
                first_name=tg_conn.user.first_name,
                last_name=tg_conn.user.last_name
            )

            now = datetime.now(timezone.utc)
            conn = BusinessConnection(
                business_connection_id=business_connection_id,
                user_id=user.id,
                user_chat_id=tg_conn.user_chat_id,
                connection_date=now,
                is_enabled=tg_conn.is_enabled,
                can_reply=tg_conn.can_reply
            )
            try:
                session.add(conn)
                if tg_conn.is_enabled:
                    await self.initialize_trial_on_connection(session, user)
                await session.flush()
                logger.info(f"Dynamically resolved and created BusinessConnection {business_connection_id} for user {user.telegram_user_id}")
                return conn, user
            except Exception as insert_err:
                logger.warning(f"Could not insert BusinessConnection {business_connection_id}, attempting rollback & re-query: {insert_err}")
                await session.rollback()
                result = await session.execute(query)
                row = result.first()
                if row:
                    return row[0], row[1]
                return None
        except Exception as e:
            logger.warning(f"Could not resolve BusinessConnection {business_connection_id} via Telegram: {e}")
            return None


subscription_service = SubscriptionService()

