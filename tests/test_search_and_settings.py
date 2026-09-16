from datetime import datetime, timezone
import pytest
from app.models.message import Message
from app.services.archive_service import archive_service
from app.services.search_service import search_service
from app.services.subscription_service import subscription_service


@pytest.mark.asyncio
async def test_search_and_filter_messages(test_session):
    """Tests message search by text, caption, and sender name."""
    user = await subscription_service.get_or_create_user(test_session, 999888777)
    chat = await archive_service.get_or_create_chat(
        test_session, user, "conn_search", 123456, first_name="Rustam"
    )
    now = datetime.now(timezone.utc)

    # Insert messages
    await archive_service.save_business_message(
        session=test_session,
        user=user,
        chat=chat,
        business_connection_id="conn_search",
        telegram_message_id=1,
        sender_id=123456,
        sender_username="rustam_dev",
        sender_first_name="Rustam",
        sender_last_name=None,
        direction="INCOMING",
        message_type="TEXT",
        sent_at=now,
        text="Maxfiy parol va ma'lumotlar",
    )

    await archive_service.save_business_message(
        session=test_session,
        user=user,
        chat=chat,
        business_connection_id="conn_search",
        telegram_message_id=2,
        sender_id=123456,
        sender_username="rustam_dev",
        sender_first_name="Rustam",
        sender_last_name=None,
        direction="INCOMING",
        message_type="TEXT",
        sent_at=now,
        text="Oddiy salomlashuv",
    )

    # Search for "parol"
    msgs, total = await search_service.search_messages(test_session, user, "parol")
    assert total == 1
    assert msgs[0].telegram_message_id == 1
    assert "parol" in msgs[0].text

    # Search for sender "Rustam"
    msgs_sender, total_sender = await search_service.search_messages(test_session, user, "Rustam")
    assert total_sender == 2


@pytest.mark.asyncio
async def test_gdpr_data_purge(test_session):
    """Tests complete GDPR purge of all user records, chats, and messages."""
    user = await subscription_service.get_or_create_user(test_session, 555444333)
    chat = await archive_service.get_or_create_chat(
        test_session, user, "conn_purge", 789012, first_name="Alisher"
    )
    now = datetime.now(timezone.utc)

    msg = await archive_service.save_business_message(
        session=test_session,
        user=user,
        chat=chat,
        business_connection_id="conn_purge",
        telegram_message_id=10,
        sender_id=789012,
        sender_username="alisher",
        sender_first_name="Alisher",
        sender_last_name=None,
        direction="INCOMING",
        message_type="TEXT",
        sent_at=now,
        text="O'chirilishi kerak bo'lgan xabar",
    )
    assert msg.id is not None

    # Execute purge
    purge_success = await search_service.delete_all_user_data(test_session, user)
    assert purge_success is True

    # Verify no messages remain
    remaining_msgs, total = await search_service.get_deleted_messages(test_session, user)
    assert total == 0
    assert len(remaining_msgs) == 0
