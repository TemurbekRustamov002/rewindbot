import asyncio
import json
import logging
import uuid
from app.core.redis import get_redis_client
from app.core.config import settings
from app.db.session import async_session_factory
from app.services.media_service import media_service

logger = logging.getLogger(__name__)


async def run_media_worker():
    """Continuous background worker listening for media download jobs on Redis queue."""
    logger.info("Starting Media Worker...")
    r = get_redis_client()

    while True:
        try:
            # Blocking pop with timeout
            item = await r.brpop("queue:media_downloads", timeout=5)
            if item:
                _, data_str = item
                data = json.loads(data_str)
                media_id = uuid.UUID(data["media_id"])

                async with async_session_factory() as session:
                    await media_service.download_and_store_media(
                        session=session,
                        media_id=media_id,
                        bot_token=settings.BOT_TOKEN
                    )
                    await session.commit()
        except asyncio.CancelledError:
            logger.info("Media Worker cancelled.")
            break
        except Exception as e:
            logger.error(f"Error in Media Worker loop: {e}", exc_info=True)
            await asyncio.sleep(2)


if __name__ == "__main__":
    asyncio.run(run_media_worker())
