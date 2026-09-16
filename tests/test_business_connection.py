import pytest
from datetime import datetime, timezone, timedelta
from app.services.subscription_service import subscription_service


@pytest.mark.asyncio
async def test_user_creation_and_trial_activation(test_session):
    """TC-001 & TC-002: Tests user creation and 72-hour trial activation upon business connection."""
    user = await subscription_service.get_or_create_user(
        session=test_session,
        telegram_user_id=123456789,
        username="testuser",
        first_name="Test",
        last_name="User"
    )
    assert user.telegram_user_id == 123456789
    assert user.trial_used is False
    assert user.trial_expires_at is None

    # First business connection activates trial
    activated = await subscription_service.initialize_trial_on_connection(test_session, user)
    assert activated is True
    assert user.trial_used is True
    assert user.trial_expires_at is not None

    has_access, status = await subscription_service.has_active_access(test_session, user)
    assert has_access is True
    assert status == "TRIAL_ACTIVE"


@pytest.mark.asyncio
async def test_reconnect_does_not_grant_new_trial(test_session):
    """TC-003: Tests that disconnecting and reconnecting does not grant a new 72-hour trial."""
    user = await subscription_service.get_or_create_user(
        session=test_session,
        telegram_user_id=987654321
    )
    # First activation
    await subscription_service.initialize_trial_on_connection(test_session, user)

    # Manually expire trial
    user.trial_expires_at = datetime.now(timezone.utc) - timedelta(hours=1)
    await test_session.flush()

    # Reconnection attempt
    re_activated = await subscription_service.initialize_trial_on_connection(test_session, user)
    assert re_activated is False  # Cannot get another trial

    has_access, status = await subscription_service.has_active_access(test_session, user)
    assert has_access is False
    assert status == "EXPIRED"
