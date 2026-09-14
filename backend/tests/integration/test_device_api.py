"""
Integration tests for Push Device Registration API Endpoints (Module 13)

Validates:
- Device token masking (never returns unmasked tokens)
- Registration of iOS/Android/Web push devices
- Device listing with active status
- IDOR protections on device deactivation
"""

from datetime import datetime, timezone
from unittest.mock import AsyncMock, patch
import pytest
from fastapi.testclient import TestClient

from app.api.deps import get_current_user
from app.main import app
from app.models.user import User
from app.models.user_device import UserDevice


@pytest.fixture
def test_customer():
    return User(
        id="usr-device-cust-1",
        name="Device Customer",
        email="device_cust@cartify.com",
        role="customer",
        is_active=True,
    )


@pytest.fixture(autouse=True)
def bypass_rate_limiter():
    with patch("app.services.rate_limiter.SlidingWindowRateLimiter.check_and_raise", new=AsyncMock()):
        yield


def test_register_device_token_masked(client: TestClient, test_customer):
    app.dependency_overrides[get_current_user] = lambda: test_customer

    raw_token = "fcm_token_super_secret_abcdef1234567890"
    mock_device = UserDevice(
        id="dev-101",
        user_id=test_customer.id,
        platform="ANDROID",
        device_token=raw_token,
        app_version="1.0.0",
        is_active=True,
        last_seen_at=datetime.now(timezone.utc),
        created_at=datetime.now(timezone.utc),
    )

    with patch(
        "app.repositories.user_device.UserDeviceRepository.register_device",
        new=AsyncMock(return_value=mock_device),
    ):
        res = client.post(
            "/api/v1/devices",
            json={
                "platform": "ANDROID",
                "deviceToken": raw_token,
                "appVersion": "1.0.0",
            },
        )
        assert res.status_code == 201
        data = res.json()
        assert data["success"] is True
        # Assert raw token is NEVER exposed
        assert raw_token not in str(data)
        assert "maskedToken" in data["data"]
        assert "..." in data["data"]["maskedToken"]


def test_list_devices(client: TestClient, test_customer):
    app.dependency_overrides[get_current_user] = lambda: test_customer

    mock_device = UserDevice(
        id="dev-102",
        user_id=test_customer.id,
        platform="IOS",
        device_token="apns_token_secret_1234567890",
        app_version="1.2.0",
        is_active=True,
        last_seen_at=datetime.now(timezone.utc),
        created_at=datetime.now(timezone.utc),
    )

    with patch(
        "app.repositories.user_device.UserDeviceRepository.list_for_user",
        new=AsyncMock(return_value=[mock_device]),
    ):
        res = client.get("/api/v1/devices")
        assert res.status_code == 200
        data = res.json()
        assert data["success"] is True
        assert len(data["data"]["items"]) == 1
        assert "apns_token_secret_1234567890" not in str(data)


def test_deactivate_device_idor_protected(client: TestClient, test_customer):
    app.dependency_overrides[get_current_user] = lambda: test_customer

    with patch(
        "app.repositories.user_device.UserDeviceRepository.deactivate_device",
        new=AsyncMock(return_value=False),
    ):
        res = client.delete("/api/v1/devices/dev-not-owned")
        assert res.status_code == 404
