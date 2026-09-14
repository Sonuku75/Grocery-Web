"""
Integration tests for Notification Delivery Webhook Endpoints (Module 13)

Validates:
- Missing signature header rejection (400)
- Invalid / tampered HMAC signature rejection (400)
- Valid HMAC-SHA256 delivery receipt processing
"""

import hashlib
import hmac
import json
from unittest.mock import AsyncMock, patch
import pytest
from fastapi.testclient import TestClient

from app.core.config import settings
from app.main import app
from app.models.notification_webhook_event import NotificationWebhookEvent


def test_webhook_missing_signature(client: TestClient):
    app.dependency_overrides.clear()
    res = client.post(
        "/api/v1/notification-webhooks/mock_email",
        json={"event_id": "evt-123", "status": "delivered"},
    )
    assert res.status_code == 400
    assert "missing" in res.json()["error"]["message"].lower()


def test_webhook_invalid_signature(client: TestClient):
    app.dependency_overrides.clear()
    body_payload = json.dumps({"event_id": "evt-123", "status": "delivered"}).encode("utf-8")
    res = client.post(
        "/api/v1/notification-webhooks/mock_email",
        content=body_payload,
        headers={
            "Content-Type": "application/json",
            "X-Notification-Signature": "invalid_hex_signature",
        },
    )
    assert res.status_code == 400
    assert "signature" in res.json()["error"]["message"].lower()


def test_webhook_valid_signature_success(client: TestClient):
    app.dependency_overrides.clear()
    payload = {"event_id": "evt-999", "status": "DELIVERED", "provider_message_id": "msg-123"}
    body_payload = json.dumps(payload).encode("utf-8")

    secret = settings.NOTIFICATION_WEBHOOK_SECRET
    sig = hmac.new(secret.encode("utf-8"), body_payload, hashlib.sha256).hexdigest()

    mock_event = NotificationWebhookEvent(
        id="wb-1",
        provider="MOCK_EMAIL",
        provider_event_id="evt-999",
        event_type="delivery_receipt",
        payload=payload,
    )

    with patch(
        "app.repositories.notification_webhook.NotificationWebhookRepository.create_event",
        new=AsyncMock(return_value=mock_event),
    ), patch(
        "app.repositories.notification.NotificationDeliveryRepository.get_by_provider_message_id",
        new=AsyncMock(return_value=None),
    ):
        res = client.post(
            "/api/v1/notification-webhooks/mock_email",
            content=body_payload,
            headers={
                "Content-Type": "application/json",
                "X-Notification-Signature": sig,
            },
        )
        assert res.status_code == 200
        data = res.json()
        assert data["success"] is True
        assert data["data"]["event_id"] == "evt-999"
