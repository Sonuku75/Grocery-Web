"""
Integration tests for Notification Preferences API Endpoints (Module 13)

Validates:
- Matrix retrieval for categories and channels
- Mandatory security alert protection (400 when attempting to disable security alerts)
- Updates for marketing / order preferences
"""

from unittest.mock import AsyncMock, patch
import pytest
from fastapi.testclient import TestClient

from app.api.deps import get_current_user
from app.main import app
from app.models.notification_preference import NotificationPreference
from app.models.user import User


@pytest.fixture
def test_customer():
    return User(
        id="usr-pref-cust-1",
        name="Pref Customer",
        email="pref_cust@cartify.com",
        role="customer",
        is_active=True,
    )


@pytest.fixture(autouse=True)
def bypass_rate_limiter():
    with patch("app.services.rate_limiter.SlidingWindowRateLimiter.check_and_raise", new=AsyncMock()):
        yield


def test_get_preferences_matrix(client: TestClient, test_customer):
    app.dependency_overrides[get_current_user] = lambda: test_customer

    with patch(
        "app.repositories.notification_preference.NotificationPreferenceRepository.get_user_preferences",
        new=AsyncMock(return_value=[]),
    ):
        res = client.get("/api/v1/notification-preferences")
        assert res.status_code == 200
        data = res.json()
        assert data["success"] is True
        prefs = data["data"]["preferences"]
        assert len(prefs) == 16


def test_update_preference_disallow_security_alerts(client: TestClient, test_customer):
    app.dependency_overrides[get_current_user] = lambda: test_customer

    res = client.put(
        "/api/v1/notification-preferences",
        json={
            "category": "SECURITY_ALERTS",
            "channel": "EMAIL",
            "isEnabled": False,
        },
    )
    assert res.status_code == 400
    assert "security alerts are mandatory" in res.json()["error"]["message"].lower()


def test_update_preference_success(client: TestClient, test_customer):
    app.dependency_overrides[get_current_user] = lambda: test_customer

    fake_pref = NotificationPreference(
        user_id=test_customer.id,
        notification_type="PROMOTIONS",
        channel="EMAIL",
        is_enabled=False,
    )

    with patch(
        "app.repositories.notification_preference.NotificationPreferenceRepository.set_preference",
        new=AsyncMock(return_value=fake_pref),
    ):
        res = client.put(
            "/api/v1/notification-preferences",
            json={
                "category": "PROMOTIONS",
                "channel": "EMAIL",
                "isEnabled": False,
            },
        )
        assert res.status_code == 200
        data = res.json()
        assert data["success"] is True
        assert data["data"]["category"] == "PROMOTIONS"
        assert data["data"]["channel"] == "EMAIL"
        assert data["data"]["isEnabled"] is False
