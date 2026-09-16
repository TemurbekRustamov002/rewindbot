import pytest
from datetime import datetime, timezone
from unittest.mock import AsyncMock
from app.services.subscription_service import subscription_service
from app.services.archive_service import archive_service
from app.services.media_service import media_service
from app.services.notification_service import notification_service
from app.models.message import Message, MessageVersion


@pytest.mark.asyncio
async def test_concurrent_message_save_idempotence(test_session):
    """Verifies that saving the same business message twice does not raise IntegrityError."""
    user = await subscription_service.get_or_create_user(test_session, 333444555)
    chat = await archive_service.get_or_create_chat(
        test_session, user, "conn_concurrent", 999111
    )
    now = datetime.now(timezone.utc)

    # 1. First save
    msg1 = await archive_service.save_business_message(
        session=test_session,
        user=user,
        chat=chat,
        business_connection_id="conn_concurrent",
        telegram_message_id=5001,
        sender_id=999111,
        sender_username="test_user",
        sender_first_name="Test",
        sender_last_name=None,
        direction="INCOMING",
        message_type="PHOTO",
        sent_at=now,
        text=None,
        caption="Rasm sarlavhasi"
    )
    assert msg1 is not None

    # 2. Second concurrent save of same message
    msg2 = await archive_service.save_business_message(
        session=test_session,
        user=user,
        chat=chat,
        business_connection_id="conn_concurrent",
        telegram_message_id=5001,
        sender_id=999111,
        sender_username="test_user",
        sender_first_name="Test",
        sender_last_name=None,
        direction="INCOMING",
        message_type="PHOTO",
        sent_at=now,
        text=None,
        caption="Rasm sarlavhasi yangilandi"
    )
    assert msg2 is not None
    assert msg2.id == msg1.id
    assert msg2.caption == "Rasm sarlavhasi yangilandi"


@pytest.mark.asyncio
async def test_edit_with_unix_timestamp(test_session):
    """Verifies that record_message_edit handles integer unix timestamps without SQLite DateTime errors."""
    user = await subscription_service.get_or_create_user(test_session, 444333222)
    chat = await archive_service.get_or_create_chat(
        test_session, user, "conn_timestamp_test", 112244
    )

    # Save original message with integer unix timestamp (e.g. 1789063969)
    unix_ts = 1789063969
    msg = await archive_service.save_business_message(
        session=test_session,
        user=user,
        chat=chat,
        business_connection_id="conn_timestamp_test",
        telegram_message_id=7001,
        sender_id=112244,
        sender_username="editor",
        sender_first_name="Editor",
        sender_last_name=None,
        direction="INCOMING",
        message_type="TEXT",
        sent_at=unix_ts,
        text="Eski matn"
    )
    assert isinstance(msg.sent_at, datetime)

    # Record edit with integer unix timestamp
    new_v = await archive_service.record_message_edit(
        session=test_session,
        business_connection_id="conn_timestamp_test",
        telegram_chat_id=112244,
        telegram_message_id=7001,
        new_text="Yangi tahrirlangan matn",
        new_caption=None,
        new_entities_json=None,
        edit_date=1789064000,
        user=user
    )
    assert new_v is not None
    assert isinstance(new_v.telegram_edit_date, datetime)
    assert new_v.text == "Yangi tahrirlangan matn"


@pytest.mark.asyncio
async def test_view_once_media_reply_notification(test_session, monkeypatch):
    """Verifies sending view-once media when user replies to media message."""
    user = await subscription_service.get_or_create_user(test_session, 888777666)
    chat = await archive_service.get_or_create_chat(
        test_session, user, "conn_viewonce", 112233
    )
    now = datetime.now(timezone.utc)

    # Save original photo message
    orig_msg = await archive_service.save_business_message(
        session=test_session,
        user=user,
        chat=chat,
        business_connection_id="conn_viewonce",
        telegram_message_id=6001,
        sender_id=112233,
        sender_username="partner",
        sender_first_name="Suhbatdosh",
        sender_last_name=None,
        direction="INCOMING",
        message_type="PHOTO",
        sent_at=now
    )

    media_obj = await media_service.create_media_object(
        session=test_session,
        message=orig_msg,
        telegram_file_id="tg_photo_file_123",
        file_unique_id="uniq_photo_123",
        media_type="PHOTO",
        file_name="view_once.jpg"
    )

    # Mock download_bytes_by_file_id to simulate successful direct download
    fake_bytes = b"\xff\xd8\xff\xe0\x00\x10JFIF\x00\x01\x01\x01\x00`\x00`\x00\x00\xff\xdb\x00C\x00"
    monkeypatch.setattr(
        media_service,
        "download_bytes_by_file_id",
        AsyncMock(return_value=fake_bytes)
    )

    # Mock Bot
    mock_bot = AsyncMock()
    await notification_service.send_view_once_media(
        bot=mock_bot,
        session=test_session,
        user=user,
        message=orig_msg,
        media=media_obj
    )

    # Verify photo was sent to user's private bot chat
    mock_bot.send_photo.assert_called_once()
    call_kwargs = mock_bot.send_photo.call_args.kwargs
    assert call_kwargs["chat_id"] == 888777666
    assert "View-Once" in call_kwargs["caption"]


@pytest.mark.asyncio
async def test_view_once_voice_reply_notification(test_session, monkeypatch):
    """Verifies sending view-once voice audio when user replies to voice message."""
    user = await subscription_service.get_or_create_user(test_session, 888777666)
    chat = await archive_service.get_or_create_chat(
        test_session, user, "conn_viewonce_voice", 112233
    )
    now = datetime.now(timezone.utc)

    orig_msg = await archive_service.save_business_message(
        session=test_session,
        user=user,
        chat=chat,
        business_connection_id="conn_viewonce_voice",
        telegram_message_id=6002,
        sender_id=112233,
        sender_username="partner",
        sender_first_name="Suhbatdosh",
        sender_last_name=None,
        direction="INCOMING",
        message_type="VOICE",
        sent_at=now
    )

    media_obj = await media_service.create_media_object(
        session=test_session,
        message=orig_msg,
        telegram_file_id="tg_voice_file_123",
        file_unique_id="uniq_voice_123",
        media_type="VOICE",
        file_name="voice.ogg"
    )

    fake_voice_bytes = b"OggS\x00\x02\x00\x00\x00\x00\x00\x00\x00\x00"
    monkeypatch.setattr(
        media_service,
        "download_bytes_by_file_id",
        AsyncMock(return_value=fake_voice_bytes)
    )

    mock_bot = AsyncMock()
    await notification_service.send_view_once_media(
        bot=mock_bot,
        session=test_session,
        user=user,
        message=orig_msg,
        media=media_obj
    )

    mock_bot.send_voice.assert_called_once()
    call_kwargs = mock_bot.send_voice.call_args.kwargs
    assert call_kwargs["chat_id"] == 888777666
    assert "View-Once" in call_kwargs["caption"]


@pytest.mark.asyncio
async def test_view_once_videonote_reply_notification(test_session, monkeypatch):
    """Verifies sending view-once video note (round video) when user replies."""
    user = await subscription_service.get_or_create_user(test_session, 888777666)
    chat = await archive_service.get_or_create_chat(
        test_session, user, "conn_viewonce_vnote", 112233
    )
    now = datetime.now(timezone.utc)

    orig_msg = await archive_service.save_business_message(
        session=test_session,
        user=user,
        chat=chat,
        business_connection_id="conn_viewonce_vnote",
        telegram_message_id=6003,
        sender_id=112233,
        sender_username="partner",
        sender_first_name="Suhbatdosh",
        sender_last_name=None,
        direction="INCOMING",
        message_type="VIDEO_NOTE",
        sent_at=now
    )

    media_obj = await media_service.create_media_object(
        session=test_session,
        message=orig_msg,
        telegram_file_id="tg_vnote_file_123",
        file_unique_id="uniq_vnote_123",
        media_type="VIDEO_NOTE",
        file_name="videonote.mp4"
    )

    fake_video_bytes = b"\x00\x00\x00 ftypisom\x00\x00\x02\x00isomiso2avc1mp41"
    monkeypatch.setattr(
        media_service,
        "download_bytes_by_file_id",
        AsyncMock(return_value=fake_video_bytes)
    )

    mock_bot = AsyncMock()
    await notification_service.send_view_once_media(
        bot=mock_bot,
        session=test_session,
        user=user,
        message=orig_msg,
        media=media_obj
    )

    mock_bot.send_video_note.assert_called_once()
    mock_bot.send_message.assert_called_once()
    msg_kwargs = mock_bot.send_message.call_args.kwargs
    assert msg_kwargs["chat_id"] == 888777666
    assert "View-Once" in msg_kwargs["text"]
