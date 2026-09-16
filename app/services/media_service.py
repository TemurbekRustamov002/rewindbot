import hashlib
import logging
import uuid
from datetime import datetime, timezone, timedelta
from typing import Optional
import httpx
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.message import Message
from app.models.media import MediaObject
from app.services.storage_service import storage_service
from app.core.config import settings

logger = logging.getLogger(__name__)


class MediaService:
    async def create_media_object(
        self,
        session: AsyncSession,
        message: Message,
        telegram_file_id: str,
        file_unique_id: str,
        media_type: str,
        mime_type: Optional[str] = None,
        file_name: Optional[str] = None,
        file_size: Optional[int] = None,
    ) -> MediaObject:
        """Registers a media object metadata entry in DB."""
        now = datetime.now(timezone.utc)
        expires_at = now + timedelta(days=settings.MEDIA_RETENTION_DAYS)

        media = MediaObject(
            message_id_fk=message.id,
            telegram_file_id=telegram_file_id,
            file_unique_id=file_unique_id,
            media_type=media_type,
            mime_type=mime_type,
            file_name=file_name,
            file_size=file_size,
            download_status="PENDING",
            expires_at=expires_at
        )
        session.add(media)
        await session.flush()
        return media

    async def download_bytes_by_file_id(self, bot_token: str, telegram_file_id: str) -> Optional[bytes]:
        """Directly downloads raw file bytes from Telegram given a file_id (supports SelfDestructingPhoto/Video)."""
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                get_file_url = f"https://api.telegram.org/bot{bot_token}/getFile?file_id={telegram_file_id}"
                resp = await client.get(get_file_url)
                resp_json = resp.json()
                if not resp_json.get("ok"):
                    logger.warning(f"Telegram getFile error for {telegram_file_id}: {resp_json}")
                    return None
                file_path = resp_json["result"]["file_path"]
                download_url = f"https://api.telegram.org/file/bot{bot_token}/{file_path}"
                file_resp = await client.get(download_url)
                if file_resp.status_code == 200:
                    return file_resp.content
        except Exception as e:
            logger.error(f"Error downloading file bytes for {telegram_file_id}: {e}")
        return None

    async def download_and_store_media(
        self,
        session: AsyncSession,
        media_id: uuid.UUID,
        bot_token: str
    ) -> bool:
        """
        Downloads the media file from Telegram Bot API getFile endpoint
        and securely saves it to storage with deduplication.
        """
        query = select(MediaObject).where(MediaObject.id == media_id)
        result = await session.execute(query)
        media = result.scalar_one_or_none()

        if not media:
            return False

        # Limit check for standard bot API (20MB)
        if media.file_size and media.file_size > 20 * 1024 * 1024:
            media.download_status = "SKIPPED"
            media.error_message = "File exceeds standard 20MB Bot API limit"
            await session.flush()
            return False

        media.download_attempts += 1

        try:
            async with httpx.AsyncClient(timeout=60.0) as client:
                # 1. getFile
                get_file_url = f"https://api.telegram.org/bot{bot_token}/getFile?file_id={media.telegram_file_id}"
                resp = await client.get(get_file_url)
                resp_json = resp.json()

                if not resp_json.get("ok"):
                    media.error_message = f"Telegram getFile error: {resp_json.get('description')}"
                    if media.download_attempts >= 5:
                        media.download_status = "FAILED"
                    await session.flush()
                    return False

                file_path = resp_json["result"]["file_path"]

                # 2. Download file content
                download_url = f"https://api.telegram.org/file/bot{bot_token}/{file_path}"
                file_resp = await client.get(download_url)

                if file_resp.status_code != 200:
                    media.error_message = f"Download failed with status {file_resp.status_code}"
                    if media.download_attempts >= 5:
                        media.download_status = "FAILED"
                    await session.flush()
                    return False

                file_bytes = file_resp.content
                sha256_hash = hashlib.sha256(file_bytes).hexdigest()

                # 3. Storage key structure: users/{user_id}/{year}/{month}/{sha256}.ext
                ext = file_path.split(".")[-1] if "." in file_path else "dat"
                now = datetime.now(timezone.utc)
                storage_key = f"media/{now.year}/{now.month:02d}/{sha256_hash}.{ext}"

                await storage_service.save_file(file_bytes, storage_key)

                media.storage_key = storage_key
                media.sha256 = sha256_hash
                media.file_size = len(file_bytes)
                media.download_status = "COMPLETED"
                await session.flush()

                logger.info(f"Media {media.file_unique_id} successfully saved to {storage_key}")
                return True

        except Exception as e:
            logger.error(f"Error downloading media {media.id}: {e}")
            media.error_message = str(e)
            if media.download_attempts >= 5:
                media.download_status = "FAILED"
            await session.flush()
            return False


media_service = MediaService()
