"""
Integration tests for Customer Notifications API Endpoints (Module 13)

Validates:
- Authentication enforcement (401 for unauthenticated requests)
- Customer notification listing with unread counts
- IDOR protections on mark as read and delete (cannot read/delete other user's notification)
- Mark all notifications read
"""

from datetime import datetime, timezone
from unittest.mock import AsyncMock, patch
import pytest
from fastapi.testclient import TestClient

from app.api.deps import get_current_user, get_db_reader, get_db_writer
from app.main import app
from app.models.notification import Notification, NotificationPriority, NotificationStatus
from app.models.user import User


@pytest.fixture
def test_customer():
    return User(
        id="usr-notif-cust-1",
        name="Notification Customer",
        email="cust_notif@cartify.com",
        phone="9876543210",
        role="customer",
        is_active=True,
    )


@pytest.fixture
def other_customer():
    return User(
        id="usr-notif-cust-2",
        name="Other Customer",
        email="other_notif@cartify.com",
        role="customer",
        is_active=True,
    )


@pytest.fixture(autouse=True)
def bypass_rate_limiter():
    with patch("app.services.rate_limiter.SlidingWindowRateLimiter.check_and_raise", new=AsyncMock()):
        yield


def test_list_notifications_unauthenticated(client: TestClient):
    app.dependency_overrides.clear()
    res = client.get("/api/v1/notifications")
    assert res.status_code == 401


def test_list_notifications_success(client: TestClient, test_customer):
    app.dependency_overrides[get_current_user] = lambda: test_customer

    mock_notif = Notification(
        id="notif-101",
        user_id=test_customer.id,
        type="ORDER_CREATED",
        title="Order Placed",
        body="Your order CRT-1234 has been placed.",
        priority=NotificationPriority.MEDIUM.value,
        status=NotificationStatus.UNREAD.value,
        data={},
        created_at=datetime.now(timezone.utc),
    )

    with patch(
        "app.repositories.notification.NotificationRepository.list_for_user",
        new=AsyncMock(return_value=([mock_notif], 1, 1, None)),
    ):
        res = client.get("/api/v1/notifications")
        assert res.status_code == 200
        data = res.json()
        assert data["success"] is True
        assert data["data"]["total"] == 1
        assert data["data"]["unreadCount"] == 1
        assert len(data["data"]["items"]) == 1
        assert data["data"]["items"][0]["id"] == "notif-101"
        assert data["data"]["items"][0]["title"] == "Order Placed"


def test_get_unread_count(client: TestClient, test_customer):
    app.dependency_overrides[get_current_user] = lambda: test_customer

    with patch(
        "app.repositories.notification.NotificationRepository.count_unread",
        new=AsyncMock(return_value=5),
    ):
        res = client.get("/api/v1/notifications/unread-count")
        assert res.status_code == 200
        data = res.json()
        assert data["success"] is True
        assert data["data"]["unreadCount"] == 5


def test_mark_as_read_idor_protected(client: TestClient, test_customer):
    app.dependency_overrides[get_current_user] = lambda: test_customer

    # When querying notification that does not belong to test_customer, repository returns None
    with patch(
        "app.repositories.notification.NotificationRepository.mark_as_read",
        new=AsyncMock(return_value=None),
    ):
        res = client.patch("/api/v1/notifications/notif-other-user/read")
        assert res.status_code == 404
        assert "not found" in res.json()["error"]["message"].lower()


def test_mark_as_read_success(client: TestClient, test_customer):
    app.dependency_overrides[get_current_user] = lambda: test_customer

    mock_notif = Notification(
        id="notif-101",
        user_id=test_customer.id,
        type="ORDER_CREATED",
        title="Order Placed",
        body="Body",
        priority=NotificationPriority.MEDIUM.value,
        status=NotificationStatus.READ.value,
        data={},
        created_at=datetime.now(timezone.utc),
        read_at=datetime.now(timezone.utc),
    )

    with patch(
        "app.repositories.notification.NotificationRepository.mark_as_read",
        new=AsyncMock(return_value=mock_notif),
    ):
        res = client.patch("/api/v1/notifications/notif-101/read")
        assert res.status_code == 200
        data = res.json()
        assert data["success"] is True
        assert data["data"]["status"] == "READ"


def test_mark_all_as_read(client: TestClient, test_customer):
    app.dependency_overrides[get_current_user] = lambda: test_customer

    with patch(
        "app.repositories.notification.NotificationRepository.mark_all_as_read",
        new=AsyncMock(return_value=3),
    ):
        res = client.post("/api/v1/notifications/read-all")
        assert res.status_code == 200
        data = res.json()
        assert data["success"] is True
        assert data["data"]["updatedCount"] == 3


def test_delete_notification_idor_protected(client: TestClient, test_customer):
    app.dependency_overrides[get_current_user] = lambda: test_customer

    with patch(
        "app.repositories.notification.NotificationRepository.delete_notification",
        new=AsyncMock(return_value=False),
    ):
        res = client.delete("/api/v1/notifications/notif-other-user")
        assert res.status_code == 404
