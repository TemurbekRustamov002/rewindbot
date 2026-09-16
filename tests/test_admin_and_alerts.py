import pytest
from unittest.mock import AsyncMock
from datetime import datetime, timezone, timedelta
from app.services.subscription_service import subscription_service
from app.services.notification_service import notification_service
from app.telegram.handlers.admin import is_super_admin, is_admin_user
from app.models.user import User


@pytest.mark.asyncio
async def test_admin_and_pro_granting(test_session):
    # 1. Create a super admin user
    super_admin_user = await subscription_service.get_or_create_user(
        test_session,
        telegram_user_id=7728111589,
        username="superadmin"
    )
    super_admin_user.is_super_admin = True
    await test_session.flush()

    assert await is_super_admin(7728111589, test_session) is True
    assert await is_admin_user(7728111589, test_session) is True

    # 2. Create regular user
    regular_user = await subscription_service.get_or_create_user(
        test_session,
        telegram_user_id=123456789,
        username="john_doe"
    )
    await test_session.flush()

    assert await is_super_admin(123456789, test_session) is False
    assert await is_admin_user(123456789, test_session) is False

    # 3. Appoint regular user as Admin
    regular_user.is_admin = True
    await test_session.flush()

    assert await is_admin_user(123456789, test_session) is True
    assert await is_super_admin(123456789, test_session) is False

    # 4. Grant Free PRO to regular user
    sub = await subscription_service.grant_free_pro(test_session, regular_user, days=30)
    assert sub is not None
    assert sub.status == "ACTIVE"
    assert sub.expires_at > datetime.now(timezone.utc)

    has_access, status_label = await subscription_service.has_active_access(test_session, regular_user)
    assert has_access is True
    assert status_label == "PAID_ACTIVE"

    # 5. Revoke PRO
    await subscription_service.revoke_pro(test_session, regular_user)
    regular_user.is_admin = False
    await test_session.flush()

    has_access_revoked, status_revoked = await subscription_service.has_active_access(test_session, regular_user)
    assert has_access_revoked is False
    assert status_revoked == "EXPIRED"


@pytest.mark.asyncio
async def test_expired_subscription_alert(test_session):
    mock_bot = AsyncMock()

    user = await subscription_service.get_or_create_user(
        test_session,
        telegram_user_id=987654321,
        language="uz"
    )
    user.trial_used = True
    user.trial_expires_at = datetime.now(timezone.utc) - timedelta(days=1)
    await test_session.flush()

    await notification_service.send_expired_subscription_alert(
        bot=mock_bot,
        user=user,
        business_conn_id="test_expired_conn"
    )

    assert mock_bot.send_message.called
    sent_text = mock_bot.send_message.call_args[1]["text"]
    assert "PRO Obuna / Sinov muddati tugagan" in sent_text
