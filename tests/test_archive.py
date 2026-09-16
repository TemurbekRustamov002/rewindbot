import pytest
from datetime import datetime, timezone
from app.services.subscription_service import subscription_service
from app.services.archive_service import archive_service
from sqlalchemy import select
from app.models.message import MessageVersion


@pytest.mark.asyncio
async def test_message_archive_and_versioning(test_session):
    """TC-004 & TC-005: Tests saving incoming business message and recording multi-edit version history."""
    user = await subscription_service.get_or_create_user(test_session, 111222333)
    chat = await archive_service.get_or_create_chat(
        session=test_session,
        user=user,
        business_connection_id="conn_123",
        telegram_chat_id=555666777,
        first_name="Aziz"
    )

    now = datetime.now(timezone.utc)

    # 1. Save original message (Version 1)
    msg = await archive_service.save_business_message(
        session=test_session,
        user=user,
        chat=chat,
        business_connection_id="conn_123",
        telegram_message_id=101,
        sender_id=555666777,
        sender_username="aziz",
        sender_first_name="Aziz",
        sender_last_name=None,
        direction="INCOMING",
        message_type="TEXT",
        sent_at=now,
        text="Bugun soat 18:00"
    )

    assert msg.text == "Bugun soat 18:00"
    assert msg.is_deleted is False

    # Check v1 created
    v_q = select(MessageVersion).where(MessageVersion.message_id_fk == msg.id)
    versions = (await test_session.execute(v_q)).scalars().all()
    assert len(versions) == 1
    assert versions[0].version_number == 1
    assert versions[0].text == "Bugun soat 18:00"

    # 2. First Edit (Version 2)
    v2 = await archive_service.record_message_edit(
        session=test_session,
        business_connection_id="conn_123",
        telegram_chat_id=555666777,
        telegram_message_id=101,
        new_text="Bugun soat 19:00",
        new_caption=None,
        new_entities_json=None,
        edit_date=now
    )
    assert v2 is not None
    assert v2.version_number == 2
    assert v2.text == "Bugun soat 19:00"

    # 3. Second Edit (Version 3)
    v3 = await archive_service.record_message_edit(
        session=test_session,
        business_connection_id="conn_123",
        telegram_chat_id=555666777,
        telegram_message_id=101,
        new_text="Ertaga soat 19:00",
        new_caption=None,
        new_entities_json=None,
        edit_date=now
    )
    assert v3 is not None
    assert v3.version_number == 3
    assert v3.text == "Ertaga soat 19:00"

    # Verify all 3 versions preserved without overwriting history
    v_all = (await test_session.execute(v_q.order_by(MessageVersion.version_number))).scalars().all()
    assert len(v_all) == 3
    assert [v.text for v in v_all] == ["Bugun soat 18:00", "Bugun soat 19:00", "Ertaga soat 19:00"]


@pytest.mark.asyncio
async def test_duplicate_edit_skipped(test_session):
    """TC-014: Duplicate identical edit events do not create unnecessary versions."""
    user = await subscription_service.get_or_create_user(test_session, 444555666)
    chat = await archive_service.get_or_create_chat(
        test_session, user, "conn_abc", 777888999
    )
    now = datetime.now(timezone.utc)

    await archive_service.save_business_message(
        session=test_session,
        user=user,
        chat=chat,
        business_connection_id="conn_abc",
        telegram_message_id=202,
        sender_id=777888999,
        sender_username="user2",
        sender_first_name="User2",
        sender_last_name=None,
        direction="INCOMING",
        message_type="TEXT",
        sent_at=now,
        text="Hello"
    )

    # Re-sending identical text edit
    duplicate_v = await archive_service.record_message_edit(
        session=test_session,
        business_connection_id="conn_abc",
        telegram_chat_id=777888999,
        telegram_message_id=202,
        new_text="Hello",
        new_caption=None,
        new_entities_json=None,
        edit_date=now
    )
    assert duplicate_v is None  # Skipped because content hash is identical
