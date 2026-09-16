import pytest
from datetime import datetime, timezone
from app.services.subscription_service import subscription_service
from app.services.archive_service import archive_service


@pytest.mark.asyncio
async def test_deleted_messages_marking(test_session):
    """TC-006: Tests marking messages as deleted and retrieving them."""
    user = await subscription_service.get_or_create_user(test_session, 888999000)
    chat = await archive_service.get_or_create_chat(
        test_session, user, "conn_del_test", 11223344
    )
    now = datetime.now(timezone.utc)

    # Save 2 messages
    msg1 = await archive_service.save_business_message(
        session=test_session,
        user=user,
        chat=chat,
        business_connection_id="conn_del_test",
        telegram_message_id=501,
        sender_id=11223344,
        sender_username="user1",
        sender_first_name="User1",
        sender_last_name=None,
        direction="INCOMING",
        message_type="TEXT",
        sent_at=now,
        text="Birinchi xabar"
    )

    msg2 = await archive_service.save_business_message(
        session=test_session,
        user=user,
        chat=chat,
        business_connection_id="conn_del_test",
        telegram_message_id=502,
        sender_id=11223344,
        sender_username="user1",
        sender_first_name="User1",
        sender_last_name=None,
        direction="INCOMING",
        message_type="TEXT",
        sent_at=now,
        text="Ikkinchi xabar"
    )

    assert msg1.is_deleted is False
    assert msg2.is_deleted is False

    # Process deletion of msg1 and an unknown message (e.g. 503)
    found = await archive_service.process_deleted_messages(
        session=test_session,
        business_connection_id="conn_del_test",
        telegram_chat_id=11223344,
        deleted_message_ids=[501, 503]
    )

    assert len(found) == 1
    assert found[0].telegram_message_id == 501
    assert found[0].is_deleted is True
    assert found[0].deleted_at is not None
    assert msg2.is_deleted is False
