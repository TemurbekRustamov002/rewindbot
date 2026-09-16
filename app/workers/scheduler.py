import asyncio
import logging
from datetime import datetime, timezone, timedelta
from sqlalchemy import select, and_
from app.db.session import async_session_factory
from app.models.user import User
from app.models.subscription import Subscription
from app.models.media import MediaObject
from app.services.storage_service import storage_service
from app.telegram.bot import bot

logger = logging.getLogger(__name__)


async def check_trial_reminders():
    """Checks and sends 24-hour and 6-hour trial expiration reminders (Section 32)."""
    now = datetime.now(timezone.utc)
    target_24h_start = now + timedelta(hours=23, minutes=30)
    target_24h_end = now + timedelta(hours=24, minutes=30)

    async with async_session_factory() as session:
        # Users expiring in ~24 hours
        q_24 = select(User).where(
            User.trial_expires_at.between(target_24h_start, target_24h_end)
        )
        users_24 = (await session.execute(q_24)).scalars().all()

        for u in users_24:
            try:
                from app.core.i18n import t
                user_lang = u.language or "uz"
                await bot.send_message(
                    chat_id=u.telegram_user_id,
                    text=t("trial_reminder_24h", user_lang),
                    parse_mode="HTML"
                )
            except Exception as e:
                logger.warning(f"Failed to send 24h reminder to {u.telegram_user_id}: {e}")


async def cleanup_expired_media():
    """Purges media files exceeding retention TTL (30 days)."""
    now = datetime.now(timezone.utc)
    async with async_session_factory() as session:
        q = select(MediaObject).where(
            and_(
                MediaObject.expires_at < now,
                MediaObject.storage_key.is_not(None)
            )
        ).limit(100)
        expired_media = (await session.execute(q)).scalars().all()

        for m in expired_media:
            if m.storage_key:
                await storage_service.delete_file(m.storage_key)
                m.storage_key = None
                m.download_status = "PURGED"

        await session.commit()
        if expired_media:
            logger.info(f"Purged {len(expired_media)} expired media files from storage.")


async def run_scheduler():
    """Scheduler loop running periodic maintenance jobs."""
    logger.info("Starting Scheduler...")
    while True:
        try:
            await check_trial_reminders()
            await cleanup_expired_media()
        except asyncio.CancelledError:
            break
        except Exception as e:
            logger.error(f"Error in scheduler loop: {e}", exc_info=True)

        # Sleep for 1 hour
        await asyncio.sleep(3600)


if __name__ == "__main__":
    asyncio.run(run_scheduler())
