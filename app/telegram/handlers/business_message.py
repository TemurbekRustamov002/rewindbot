import logging
import json
import asyncio
import hashlib
import html
from datetime import datetime, timezone
from aiogram import Router
from aiogram.types import Message, BufferedInputFile
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from app.db.session import async_session_factory
from app.services.subscription_service import subscription_service
from app.services.archive_service import archive_service
from app.services.media_service import media_service
from app.services.storage_service import storage_service
from app.services.notification_service import notification_service
from app.models.business_connection import BusinessConnection
from app.models.user import User
from app.models.media import MediaObject
from app.models.message import Message as DBMessage
from app.core.redis import push_media_queue
from app.core.config import settings
from app.core.i18n import t
from app.telegram.bot import bot

logger = logging.getLogger(__name__)
business_message_router = Router(name="business_message_router")


@business_message_router.business_message()
async def handle_business_message(message: Message):
    """
    FR-100: Receives new incoming or outgoing business messages,
    verifies active trial/subscription, saves archive and registers media.
    Also handles Section 28 (View-Once Reply Trigger).
    """
    business_conn_id = message.business_connection_id
    if not business_conn_id:
        return

    telegram_chat_id = message.chat.id
    telegram_message_id = message.message_id
    sender = message.from_user
    sent_at = message.date

    async with async_session_factory() as session:
        # 1. Accurately identify business connection and user owner
        resolved = await subscription_service.resolve_business_connection(
            session=session,
            bot=bot,
            business_connection_id=business_conn_id
        )
        if not resolved:
            return

        conn, user = resolved
        if not conn.is_enabled:
            return

        # 2. Check access (trial or paid active)
        has_access, _ = await subscription_service.has_active_access(session, user)
        if not has_access:
            await notification_service.send_expired_subscription_alert(
                bot=bot,
                user=user,
                business_conn_id=business_conn_id
            )
            return

        # 3. Upsert chat
        chat = await archive_service.get_or_create_chat(
            session=session,
            user=user,
            business_connection_id=business_conn_id,
            telegram_chat_id=telegram_chat_id,
            username=message.chat.username,
            first_name=message.chat.first_name,
            last_name=message.chat.last_name,
            title=message.chat.title
        )

        if chat.is_excluded:
            return

        # 4. Determine message type and media
        msg_type = "TEXT"
        media_info = None

        if message.photo:
            msg_type = "PHOTO"
            # Get largest photo resolution
            photo = message.photo[-1]
            media_info = {
                "file_id": photo.file_id,
                "file_unique_id": photo.file_unique_id,
                "file_size": photo.file_size,
                "mime_type": "image/jpeg",
                "file_name": f"photo_{photo.file_unique_id}.jpg"
            }
        elif message.video:
            msg_type = "VIDEO"
            media_info = {
                "file_id": message.video.file_id,
                "file_unique_id": message.video.file_unique_id,
                "file_size": message.video.file_size,
                "mime_type": message.video.mime_type or "video/mp4",
                "file_name": message.video.file_name or f"video_{message.video.file_unique_id}.mp4"
            }
        elif message.voice:
            msg_type = "VOICE"
            media_info = {
                "file_id": message.voice.file_id,
                "file_unique_id": message.voice.file_unique_id,
                "file_size": message.voice.file_size,
                "mime_type": message.voice.mime_type or "audio/ogg",
                "file_name": f"voice_{message.voice.file_unique_id}.ogg"
            }
        elif message.video_note:
            msg_type = "VIDEO_NOTE"
            media_info = {
                "file_id": message.video_note.file_id,
                "file_unique_id": message.video_note.file_unique_id,
                "file_size": message.video_note.file_size,
                "mime_type": "video/mp4",
                "file_name": f"videonote_{message.video_note.file_unique_id}.mp4"
            }
        elif message.document:
            msg_type = "DOCUMENT"
            media_info = {
                "file_id": message.document.file_id,
                "file_unique_id": message.document.file_unique_id,
                "file_size": message.document.file_size,
                "mime_type": message.document.mime_type,
                "file_name": message.document.file_name
            }
        elif message.audio:
            msg_type = "AUDIO"
            media_info = {
                "file_id": message.audio.file_id,
                "file_unique_id": message.audio.file_unique_id,
                "file_size": message.audio.file_size,
                "mime_type": message.audio.mime_type or "audio/mpeg",
                "file_name": message.audio.file_name or f"audio_{message.audio.file_unique_id}.mp3"
            }
        elif message.animation:
            msg_type = "ANIMATION"
            media_info = {
                "file_id": message.animation.file_id,
                "file_unique_id": message.animation.file_unique_id,
                "file_size": message.animation.file_size,
                "mime_type": message.animation.mime_type or "video/mp4",
                "file_name": message.animation.file_name or f"gif_{message.animation.file_unique_id}.mp4"
            }
        elif message.sticker:
            msg_type = "STICKER"

        direction = "OUTGOING" if (sender and sender.id == user.telegram_user_id) else "INCOMING"

        entities_json = json.dumps([e.model_dump() for e in message.entities]) if message.entities else None

        # 5. Save message in DB
        db_msg = await archive_service.save_business_message(
            session=session,
            user=user,
            chat=chat,
            business_connection_id=business_conn_id,
            telegram_message_id=telegram_message_id,
            sender_id=sender.id if sender else 0,
            sender_username=sender.username if sender else None,
            sender_first_name=sender.first_name if sender else None,
            sender_last_name=sender.last_name if sender else None,
            direction=direction,
            message_type=msg_type,
            sent_at=sent_at,
            text=message.text,
            caption=message.caption,
            entities_json=entities_json,
            reply_to_message_id=message.reply_to_message.message_id if message.reply_to_message else None,
            media_group_id=message.media_group_id
        )

        # 6. Save media object and push to worker queue
        if media_info and db_msg:
            media_obj = await media_service.create_media_object(
                session=session,
                message=db_msg,
                telegram_file_id=media_info["file_id"],
                file_unique_id=media_info["file_unique_id"],
                media_type=msg_type,
                mime_type=media_info.get("mime_type"),
                file_name=media_info.get("file_name"),
                file_size=media_info.get("file_size")
            )
            # Queue for Redis worker
            await push_media_queue({
                "media_id": str(media_obj.id),
                "telegram_file_id": media_info["file_id"]
            })
            # Immediate async background task to guarantee quick download & disk persistence
            m_id = media_obj.id
            f_id = media_info["file_id"]
            f_name = media_info.get("file_name") or f"media_{media_obj.file_unique_id}"

            async def _bg_download(target_media_id, target_file_id, target_file_name):
                try:
                    # 1. Download raw bytes directly from Telegram API
                    file_bytes = await media_service.download_bytes_by_file_id(settings.BOT_TOKEN, target_file_id)
                    if not file_bytes:
                        return

                    # 2. Save raw bytes to local/S3 storage
                    sha256_hash = hashlib.sha256(file_bytes).hexdigest()
                    ext = target_file_name.split(".")[-1] if "." in target_file_name else "dat"
                    now = datetime.now(timezone.utc)
                    storage_key = f"media/{now.year}/{now.month:02d}/{sha256_hash}.{ext}"
                    await storage_service.save_file(file_bytes, storage_key)

                    # 3. Update DB record in background session
                    async with async_session_factory() as bg_s:
                        q = select(MediaObject).where(MediaObject.id == target_media_id)
                        res = await bg_s.execute(q)
                        m = res.scalar_one_or_none()
                        if m:
                            m.storage_key = storage_key
                            m.sha256 = sha256_hash
                            m.file_size = len(file_bytes)
                            m.download_status = "COMPLETED"
                            await bg_s.commit()
                            logger.info(f"Media {m.file_unique_id} successfully saved to {storage_key}")
                except Exception as e:
                    logger.warning(f"Background media download error: {e}")

            asyncio.create_task(_bg_download(m_id, f_id, f_name))

        # 7. Section 28: View-Once Reply Trigger
        # When a reply is made by the business user to any media message in the chat, send media directly to private bot chat
        if message.reply_to_message and direction == "OUTGOING":
            replied_msg = message.reply_to_message
            replied_msg_id = replied_msg.message_id
            direct_media_sent = False

            # Layer 1: Direct extraction if Telegram attached media in reply_to_message payload
            try:
                user_lang = user.language or "uz"
                sender_fallback = t("sender_partner", user_lang)
                r_sender = replied_msg.from_user
                sender_name = html.escape(r_sender.first_name or r_sender.username or sender_fallback) if r_sender else sender_fallback
                caption_text = html.escape(replied_msg.caption or "")
                title = t("view_once_title", user_lang)
                header = f"{title} • 👤 <b>{sender_name}</b>"
                if caption_text:
                    header += f"\n\n<blockquote>{caption_text}</blockquote>"

                if replied_msg.photo:
                    photo = replied_msg.photo[-1]
                    file_bytes = await media_service.download_bytes_by_file_id(settings.BOT_TOKEN, photo.file_id)
                    if file_bytes:
                        input_file = BufferedInputFile(file_bytes, filename=f"view_once_{photo.file_unique_id}.jpg")
                        await bot.send_photo(
                            chat_id=user.telegram_user_id,
                            photo=input_file,
                            caption=header,
                            parse_mode="HTML"
                        )
                        direct_media_sent = True
                elif replied_msg.video:
                    file_bytes = await media_service.download_bytes_by_file_id(settings.BOT_TOKEN, replied_msg.video.file_id)
                    if file_bytes:
                        input_file = BufferedInputFile(file_bytes, filename=f"view_once_{replied_msg.video.file_unique_id}.mp4")
                        await bot.send_video(
                            chat_id=user.telegram_user_id,
                            video=input_file,
                            caption=header,
                            parse_mode="HTML"
                        )
                        direct_media_sent = True
                elif replied_msg.voice:
                    file_bytes = await media_service.download_bytes_by_file_id(settings.BOT_TOKEN, replied_msg.voice.file_id)
                    if file_bytes:
                        input_file = BufferedInputFile(file_bytes, filename=f"view_once_{replied_msg.voice.file_unique_id}.ogg")
                        await bot.send_voice(
                            chat_id=user.telegram_user_id,
                            voice=input_file,
                            caption=header,
                            parse_mode="HTML"
                        )
                        direct_media_sent = True
                elif replied_msg.video_note:
                    file_bytes = await media_service.download_bytes_by_file_id(settings.BOT_TOKEN, replied_msg.video_note.file_id)
                    if file_bytes:
                        input_file = BufferedInputFile(file_bytes, filename=f"view_once_{replied_msg.video_note.file_unique_id}.mp4")
                        await bot.send_message(
                            chat_id=user.telegram_user_id,
                            text=header,
                            parse_mode="HTML"
                        )
                        await bot.send_video_note(
                            chat_id=user.telegram_user_id,
                            video_note=input_file
                        )
                        direct_media_sent = True
            except Exception as e:
                logger.warning(f"Direct reply media extraction fallback to DB: {e}")

            # Layer 2: Database Archive Lookup if not dispatched directly
            if not direct_media_sent:
                orig_q = select(DBMessage).where(
                    DBMessage.business_connection_id == business_conn_id,
                    DBMessage.telegram_chat_id == telegram_chat_id,
                    DBMessage.telegram_message_id == replied_msg_id
                ).options(
                    selectinload(DBMessage.media_objects)
                )
                orig_res = await session.execute(orig_q)
                orig_msg = orig_res.scalar_one_or_none()

                if orig_msg and orig_msg.media_objects:
                    for media in orig_msg.media_objects:
                        await notification_service.send_view_once_media(
                            bot=bot,
                            session=session,
                            user=user,
                            message=orig_msg,
                            media=media
                        )

        await session.commit()


