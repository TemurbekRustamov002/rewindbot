import pytest
from unittest.mock import AsyncMock
from datetime import datetime, timezone
from app.services.subscription_service import subscription_service
from app.services.archive_service import archive_service
from app.services.notification_service import notification_service
from app.models.message import MessageVersion


@pytest.mark.asyncio
async def test_notifications_multilingual(test_session):
    mock_bot = AsyncMock()

    for lang in ["uz", "ru", "en"]:
        # Create user with specific language
        user = await subscription_service.get_or_create_user(
            test_session,
            telegram_user_id=1000 + len(lang),
            language=lang
        )
        user.language = lang
        await test_session.flush()

        chat = await archive_service.get_or_create_chat(
            test_session, user, f"conn_{lang}", 55500 + len(lang)
        )
        now = datetime.now(timezone.utc)

        # 1. Save text message and test deleted notification
        msg = await archive_service.save_business_message(
            session=test_session,
            user=user,
            chat=chat,
            business_connection_id=f"conn_{lang}",
            telegram_message_id=900 + len(lang),
            sender_id=55500 + len(lang),
            sender_username="friend",
            sender_first_name="Friend",
            sender_last_name=None,
            direction="INCOMING",
            message_type="TEXT",
            sent_at=now,
            text="Hello world"
        )
        await test_session.flush()

        # Call send_deleted_notification
        await notification_service.send_deleted_notification(
            bot=mock_bot,
            session=test_session,
            user=user,
            message=msg
        )

        assert mock_bot.send_message.called
        last_call_args = mock_bot.send_message.call_args[1]
        sent_text = last_call_args["text"]

        if lang == "uz":
            assert "O‘chirilgan xabar" in sent_text
        elif lang == "ru":
            assert "Удаленное сообщение" in sent_text
        elif lang == "en":
            assert "Deleted Message" in sent_text

        # 2. Test edit notification
        new_version = MessageVersion(
            message_id_fk=msg.id,
            version_number=2,
            text="Updated text",
            content_hash="hash123",
            telegram_edit_date=now
        )
        test_session.add(new_version)
        await test_session.flush()

        await notification_service.send_edit_notification(
            bot=mock_bot,
            session=test_session,
            user=user,
            message=msg,
            new_version=new_version
        )

        edit_call_args = mock_bot.send_message.call_args[1]
        edit_text = edit_call_args["text"]

        if lang == "uz":
            assert "Tahrirlangan xabar" in edit_text
        elif lang == "ru":
            assert "Отредактированное сообщение" in edit_text
        elif lang == "en":
            assert "Edited Message" in edit_text
