import pytest
from datetime import datetime, timezone, timedelta
from app.services.subscription_service import subscription_service


@pytest.mark.asyncio
async def test_stars_subscription_activation_and_access(test_session):
    """TC-011 & TC-012: Tests 50 Stars subscription activation and recurring renewal."""
    user = await subscription_service.get_or_create_user(test_session, 333444555)

    # Initial state: no access
    has_access, status = await subscription_service.has_active_access(test_session, user)
    assert has_access is False
    assert status == "EXPIRED"

    # User purchases PRO for 50 Stars
    now = datetime.now(timezone.utc)
    expiration = now + timedelta(days=30)
    sub = await subscription_service.activate_stars_subscription(
        session=test_session,
        user=user,
        telegram_payment_charge_id="charge_stars_12345",
        amount=50,
        is_recurring=True,
        is_first_recurring=True,
        expiration_date=expiration
    )

    assert sub.status == "ACTIVE"
    assert sub.auto_renew is True
    assert sub.expires_at == expiration

    # Access is now PAID_ACTIVE
    has_access, status = await subscription_service.has_active_access(test_session, user)
    assert has_access is True
    assert status == "PAID_ACTIVE"


@pytest.mark.asyncio
async def test_canceled_subscription_retains_access_until_expiry(test_session):
    """TC-013: Canceled auto-renewal keeps service active until current period ends."""
    user = await subscription_service.get_or_create_user(test_session, 777888111)

    now = datetime.now(timezone.utc)
    expiration = now + timedelta(days=15)

    sub = await subscription_service.activate_stars_subscription(
        session=test_session,
        user=user,
        telegram_payment_charge_id="charge_stars_99999",
        amount=50,
        is_recurring=True,
        expiration_date=expiration
    )

    # User cancels auto-renewal
    sub.status = "CANCELED_PENDING_EXPIRY"
    sub.auto_renew = False
    await test_session.flush()

    # User still has active access until expiration date
    has_access, status = await subscription_service.has_active_access(test_session, user)
    assert has_access is True
    assert status == "PAID_ACTIVE"
