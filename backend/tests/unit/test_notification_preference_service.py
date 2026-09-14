"""
Unit tests for NotificationPreferenceService (Module 13)

Validates:
- Full preference matrix retrieval
- Enforcement of mandatory security alerts (cannot be disabled)
- Preference updates for regular categories
- is_channel_enabled logic
"""

import pytest
from unittest.mock import AsyncMock, patch

from app.core.errors import BadRequestError
from app.models.notification import NotificationChannel
from app.models.notification_preference import NotificationCategory, NotificationPreference
from app.schemas.notification_preference import UpdateNotificationPreferenceRequest
from app.services.notification_preference_service import NotificationPreferenceService


@pytest.mark.asyncio
async def test_get_user_preferences_defaults():
    mock_db = AsyncMock()
    with patch(
        "app.repositories.notification_preference.NotificationPreferenceRepository.get_user_preferences",
        new=AsyncMock(return_value=[]),
    ):
        resp = await NotificationPreferenceService.get_user_preferences(mock_db, "user-123")
        assert len(resp.preferences) == 16  # 4 categories x 4 channels

        # Check that SECURITY_ALERTS are mandatory and enabled
        sec_prefs = [p for p in resp.preferences if p.category == "SECURITY_ALERTS"]
        assert len(sec_prefs) == 4
        for sp in sec_prefs:
            assert sp.is_mandatory is True
            assert sp.is_enabled is True


@pytest.mark.asyncio
async def test_update_preference_security_alert_rejected():
    mock_db = AsyncMock()
    req = UpdateNotificationPreferenceRequest(
        category="SECURITY_ALERTS",
        channel="EMAIL",
        isEnabled=False,
    )

    with pytest.raises(BadRequestError, match="Security alerts are mandatory and cannot be disabled"):
        await NotificationPreferenceService.update_preference(mock_db, "user-123", req)


@pytest.mark.asyncio
async def test_update_preference_promotions_success():
    mock_db = AsyncMock()
    req = UpdateNotificationPreferenceRequest(
        category="PROMOTIONS",
        channel="SMS",
        isEnabled=False,
    )

    fake_pref = NotificationPreference(
        user_id="user-123",
        notification_type="PROMOTIONS",
        channel="SMS",
        is_enabled=False,
    )

    with patch(
        "app.repositories.notification_preference.NotificationPreferenceRepository.set_preference",
        new=AsyncMock(return_value=fake_pref),
    ):
        res = await NotificationPreferenceService.update_preference(mock_db, "user-123", req)
        assert res.category == "PROMOTIONS"
        assert res.channel == "SMS"
        assert res.is_enabled is False
        assert res.is_mandatory is False


@pytest.mark.asyncio
async def test_is_channel_enabled_security_alerts_always_true():
    mock_db = AsyncMock()
    # Even if DB has False, security alerts must return True
    enabled = await NotificationPreferenceService.is_channel_enabled(
        mock_db, "user-123", "SECURITY_ALERTS", "SMS"
    )
    assert enabled is True
