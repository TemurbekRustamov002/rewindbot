import html
import logging
from typing import List, Optional
from aiogram import Bot
from aiogram.types import BufferedInputFile, InlineKeyboardMarkup, InlineKeyboardButton
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.user import User
from app.models.message import Message, MessageVersion
from app.models.settings import UserSettings
from app.models.media import MediaObject
from app.services.storage_service import storage_service
from app.services.media_service import media_service
from app.core.redis import is_notification_sent
from app.core.config import settings as app_settings
from app.core.i18n import t

logger = logging.getLogger(__name__)


class NotificationService:
    async def send_deleted_notification(
        self,
        bot: Bot,
        session: AsyncSession,
        user: User,
        message: Message
    ) -> None:
        """Sends notification to user's private bot chat when a message is deleted."""
        # 1. Deduplication check
        if await is_notification_sent(
            message.business_connection_id,
            message.telegram_chat_id,
            message.telegram_message_id,
            "deleted"
        ):
            return

        user_lang = user.language or "uz"

        # 2. Load user settings
        s_query = select(UserSettings).where(UserSettings.user_id == user.id)
        s_res = await session.execute(s_query)
        user_settings = s_res.scalar_one_or_none()

        if user_settings and not user_settings.notifications_enabled:
            return

        sender_fallback = t("sender_user", user_lang)
        sender_name = html.escape(message.sender_first_name or message.sender_username or sender_fallback)

        # Load message versions and media objects
        msg_query = select(Message).where(Message.id == message.id).options(
            selectinload(Message.versions),
            selectinload(Message.media_objects)
        )
        msg_res = await session.execute(msg_query)
        loaded_msg = msg_res.scalar_one_or_none() or message

        versions_count = len(loaded_msg.versions)
        is_edited_before_delete = versions_count > 1

        # Media Message Notification (PHOTO, VIDEO, VOICE, DOCUMENT, etc.)
        if loaded_msg.media_objects:
            caption_text = html.escape(loaded_msg.caption or "")
            media_type_keys = {
                "PHOTO": "media_photo",
                "VIDEO": "media_video",
                "VOICE": "media_voice",
                "VIDEO_NOTE": "media_video_note",
                "DOCUMENT": "media_document",
                "AUDIO": "media_audio",
                "ANIMATION": "media_animation"
            }
            media_key = media_type_keys.get(loaded_msg.type, "media_generic")
            media_type_label = t(media_key, user_lang)
            title = t("deleted_media_title", user_lang, media_type=media_type_label)
            header = f"{title} • 👤 <b>{sender_name}</b>"
            if caption_text:
                header += f"\n\n<blockquote>{caption_text}</blockquote>"

            for media in loaded_msg.media_objects:
                try:
                    file_bytes = await storage_service.get_file_bytes(media.storage_key) if media.storage_key else None

                    # If not in storage, download raw bytes directly
                    if not file_bytes:
                        file_bytes = await media_service.download_bytes_by_file_id(app_settings.BOT_TOKEN, media.telegram_file_id)

                    if file_bytes:
                        input_file = BufferedInputFile(
                            file_bytes,
                            filename=media.file_name or f"deleted_media_{media.file_unique_id}"
                        )
                        if media.media_type == "PHOTO":
                            await bot.send_photo(
                                chat_id=user.telegram_user_id,
                                photo=input_file,
                                caption=header,
                                parse_mode="HTML"
                            )
                        elif media.media_type == "VIDEO":
                            await bot.send_video(
                                chat_id=user.telegram_user_id,
                                video=input_file,
                                caption=header,
                                parse_mode="HTML"
                            )
                        elif media.media_type in ["VOICE", "AUDIO"]:
                            await bot.send_voice(
                                chat_id=user.telegram_user_id,
                                voice=input_file,
                                caption=header,
                                parse_mode="HTML"
                            )
                        elif media.media_type == "VIDEO_NOTE":
                            await bot.send_message(
                                chat_id=user.telegram_user_id,
                                text=header,
                                parse_mode="HTML"
                            )
                            await bot.send_video_note(
                                chat_id=user.telegram_user_id,
                                video_note=input_file
                            )
                        else:
                            await bot.send_document(
                                chat_id=user.telegram_user_id,
                                document=input_file,
                                caption=header,
                                parse_mode="HTML"
                            )
                    else:
                        # Inform user if bytes could not be fetched
                        err_msg = t("media_fetch_error", user_lang)
                        await bot.send_message(
                            chat_id=user.telegram_user_id,
                            text=f"{header}\n\n{err_msg}",
                            parse_mode="HTML"
                        )
                except Exception as e:
                    logger.error(f"Failed to send deleted media {media.id} to user {user.telegram_user_id}: {e}")

        # Text Message Notification
        elif loaded_msg.type == "TEXT" or loaded_msg.text:
            if user_settings and not user_settings.notify_deleted_text:
                return

            raw_text = loaded_msg.text or ""
            escaped_text = html.escape(raw_text)
            edited_tag = f" {t('deleted_text_edited_note', user_lang)}" if is_edited_before_delete else ""
            title = t("deleted_text_title", user_lang)

            text = (
                f"{title}{edited_tag} • 👤 <b>{sender_name}</b>\n\n"
                f"<blockquote>{escaped_text}</blockquote>"
            )

            try:
                await bot.send_message(
                    chat_id=user.telegram_user_id,
                    text=text,
                    parse_mode="HTML"
                )
            except Exception as e:
                logger.error(f"Failed to send delete text notification to {user.telegram_user_id}: {e}")

    async def send_edit_notification(
        self,
        bot: Bot,
        session: AsyncSession,
        user: User,
        message: Message,
        new_version: MessageVersion
    ) -> None:
        """Sends notification when a message is edited."""
        # 1. Deduplication check
        if await is_notification_sent(
            message.business_connection_id,
            message.telegram_chat_id,
            message.telegram_message_id,
            f"edit_v{new_version.version_number}"
        ):
            return

        user_lang = user.language or "uz"

        s_query = select(UserSettings).where(UserSettings.user_id == user.id)
        s_res = await session.execute(s_query)
        user_settings = s_res.scalar_one_or_none()

        if user_settings and (not user_settings.notifications_enabled or not user_settings.notify_edited_messages):
            return

        # Fetch previous version
        v_query = select(MessageVersion).where(
            MessageVersion.message_id_fk == message.id,
            MessageVersion.version_number == new_version.version_number - 1
        )
        v_res = await session.execute(v_query)
        prev_version = v_res.scalar_one_or_none()

        init_label = t("initial_text", user_lang)
        old_content = html.escape((prev_version.text or prev_version.caption) if prev_version else init_label)
        new_content = html.escape(new_version.text or new_version.caption or "")
        sender_fallback = t("sender_user", user_lang)
        sender_name = html.escape(message.sender_first_name or message.sender_username or sender_fallback)

        title = t("edited_msg_title", user_lang)
        old_label = t("edited_old_label", user_lang)
        new_label = t("edited_new_label", user_lang)

        text = (
            f"{title} • 👤 <b>{sender_name}</b>\n\n"
            f"{old_label}\n<blockquote>{old_content}</blockquote>\n\n"
            f"{new_label}\n<blockquote>{new_content}</blockquote>"
        )

        try:
            await bot.send_message(
                chat_id=user.telegram_user_id,
                text=text,
                parse_mode="HTML"
            )
        except Exception as e:
            logger.error(f"Failed to send edit notification to {user.telegram_user_id}: {e}")

    async def send_view_once_media(
        self,
        bot: Bot,
        session: AsyncSession,
        user: User,
        message: Message,
        media: MediaObject
    ) -> None:
        """Sends view-once media directly to user's private bot chat when triggered via reply."""
        user_lang = user.language or "uz"
        sender_fallback = t("sender_partner", user_lang)
        sender_name = html.escape(message.sender_first_name or message.sender_username or sender_fallback)
        caption_text = html.escape(message.caption or "")

        title = t("view_once_title", user_lang)
        header = f"{title} • 👤 <b>{sender_name}</b>"
        if caption_text:
            header += f"\n\n<blockquote>{caption_text}</blockquote>"

        try:
            file_bytes = await storage_service.get_file_bytes(media.storage_key) if media.storage_key else None

            if not file_bytes:
                file_bytes = await media_service.download_bytes_by_file_id(app_settings.BOT_TOKEN, media.telegram_file_id)

            if file_bytes:
                input_file = BufferedInputFile(
                    file_bytes,
                    filename=media.file_name or f"view_once_{media.file_unique_id}"
                )
                if media.media_type == "PHOTO":
                    await bot.send_photo(
                        chat_id=user.telegram_user_id,
                        photo=input_file,
                        caption=header,
                        parse_mode="HTML"
                    )
                elif media.media_type == "VIDEO":
                    await bot.send_video(
                        chat_id=user.telegram_user_id,
                        video=input_file,
                        caption=header,
                        parse_mode="HTML"
                    )
                elif media.media_type in ["VOICE", "AUDIO"]:
                    await bot.send_voice(
                        chat_id=user.telegram_user_id,
                        voice=input_file,
                        caption=header,
                        parse_mode="HTML"
                    )
                elif media.media_type == "VIDEO_NOTE":
                    await bot.send_message(
                        chat_id=user.telegram_user_id,
                        text=header,
                        parse_mode="HTML"
                    )
                    await bot.send_video_note(
                        chat_id=user.telegram_user_id,
                        video_note=input_file
                    )
                else:
                    await bot.send_document(
                        chat_id=user.telegram_user_id,
                        document=input_file,
                        caption=header,
                        parse_mode="HTML"
                    )
            else:
                logger.warning(f"Could not retrieve raw bytes for view-once media {media.id}")
        except Exception as e:
            logger.error(f"Failed to send view-once media to {user.telegram_user_id}: {e}")

    async def send_expired_subscription_alert(
        self,
        bot: Bot,
        user: User,
        business_conn_id: str
    ) -> None:
        """Sends a clear, throttled alert when an event occurs but user subscription/trial is expired."""
        if await is_notification_sent(
            business_conn_id,
            user.telegram_user_id,
            0,
            "sub_expired_alert"
        ):
            return

        user_lang = user.language or "uz"
        text = t("sub_expired_alert", user_lang)
        try:
            await bot.send_message(
                chat_id=user.telegram_user_id,
                text=text,
                parse_mode="HTML"
            )
            logger.info(f"Delivered subscription expired alert to user {user.telegram_user_id}")
        except Exception as e:
            logger.warning(f"Could not send expired subscription alert to {user.telegram_user_id}: {e}")


notification_service = NotificationService()
