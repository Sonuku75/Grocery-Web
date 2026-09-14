"""
Integration tests for Payment Webhook Ingestion & Deduplication (Module 12)
"""

import json
from datetime import datetime, timezone
from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock, patch
import pytest
from fastapi.testclient import TestClient

from app.api.deps import get_db_writer
from app.main import app
from app.models.order import Order, OrderStatus, PaymentStatus as OrderPaymentStatus
from app.models.payment import Payment, PaymentStatus, PaymentWebhookEvent, WebhookProcessingStatus
from app.providers.mock import MockPaymentProvider


@pytest.fixture(autouse=True)
def bypass_rate_limiter():
    with patch("app.services.rate_limiter.SlidingWindowRateLimiter.check_and_raise", new=AsyncMock()):
        yield


def test_webhook_invalid_signature_rejected(client: TestClient):
    """Webhook with tampered/invalid signature is rejected with 400."""
    app.dependency_overrides.clear()
    payload = json.dumps({"event": "payment.captured", "id": "evt_1"}).encode("utf-8")

    res = client.post(
        "/api/v1/payments/webhooks/mock",
        content=payload,
        headers={"Content-Type": "application/json", "X-Mock-Signature": "invalid_sig"},
    )
    assert res.status_code == 400
    assert "signature" in res.json()["error"]["message"].lower()


def test_webhook_successful_payment_captured(client: TestClient):
    """Valid webhook processes event and updates payment and order to PAID."""
    mock_db = AsyncMock()
    app.dependency_overrides[get_db_writer] = lambda: mock_db

    provider = MockPaymentProvider()
    payload_dict = {
        "event": "payment.captured",
        "id": "evt_captured_100",
        "payload": {
            "payment": {
                "entity": {
                    "id": "pay_upstream_999",
                    "order_id": "mock_order_555",
                    "amount": 50000,
                    "currency": "INR",
                }
            }
        },
    }
    payload_bytes = json.dumps(payload_dict).encode("utf-8")
    sig = provider.generate_mock_webhook_signature(payload_bytes)

    payment = Payment(
        id="pay-hook-1",
        order_id="ord-hook-1",
        user_id="usr-1",
        provider="MOCK",
        payment_method="UPI",
        amount=Decimal("500.00"),
        currency="INR",
        provider_order_id="mock_order_555",
        status=PaymentStatus.PENDING.value,
    )
    order = Order(
        id="ord-hook-1",
        order_number="CRT-ORD-555",
        user_id="usr-1",
        status=OrderStatus.PENDING.value,
        payment_status=OrderPaymentStatus.PENDING.value,
        subtotal=Decimal("450.00"),
        total_amount=Decimal("500.00"),
    )

    with patch(
        "app.repositories.payment.PaymentWebhookRepository.get_event",
        new=AsyncMock(return_value=None),
    ):
        mock_event = PaymentWebhookEvent(
            id="wh-evt-1",
            provider="MOCK",
            provider_event_id="evt_captured_100",
            event_type="payment.captured",
            payload_hash="sha256hash",
            payload=payload_dict,
            processing_status=WebhookProcessingStatus.PROCESSING.value,
        )
        with patch(
            "app.repositories.payment.PaymentWebhookRepository.create_event",
            new=AsyncMock(return_value=mock_event),
        ):
            with patch(
                "app.repositories.payment.PaymentRepository.get_by_provider_order_id",
                new=AsyncMock(return_value=payment),
            ):
                with patch("app.repositories.payment.PaymentRepository.update_payment_status") as mock_update:
                    def _do_update(db, payment, new_status, **kwargs):
                        payment.status = new_status
                        return payment
                    mock_update.side_effect = _do_update

                    with patch("app.services.payment_service.select") as mock_select:
                        mock_res = MagicMock()
                        mock_res.scalar_one_or_none.return_value = order
                        mock_db.execute.return_value = mock_res

                        with patch("app.repositories.payment.PaymentWebhookRepository.update_event_status", new=AsyncMock()):
                            res = client.post(
                                "/api/v1/payments/webhooks/mock",
                                content=payload_bytes,
                                headers={"Content-Type": "application/json", "X-Mock-Signature": sig},
                            )
                            assert res.status_code == 200
                            data = res.json()["data"]
                            assert data["status"] == "processed"
                            assert data["event_id"] == "evt_captured_100"
                            assert payment.status == PaymentStatus.PAID.value
                            assert order.payment_status == OrderPaymentStatus.PAID.value


def test_webhook_duplicate_event_idempotency(client: TestClient):
    """Duplicate delivery of an already-recorded webhook event is ignored gracefully."""
    mock_db = AsyncMock()
    app.dependency_overrides[get_db_writer] = lambda: mock_db

    provider = MockPaymentProvider()
    payload_dict = {"event": "payment.captured", "id": "evt_duplicate_999"}
    payload_bytes = json.dumps(payload_dict).encode("utf-8")
    sig = provider.generate_mock_webhook_signature(payload_bytes)

    existing_event = PaymentWebhookEvent(
        id="evt-existing-1",
        provider="MOCK",
        provider_event_id="evt_duplicate_999",
        event_type="payment.captured",
        payload_hash="hash",
        payload=payload_dict,
        processing_status=WebhookProcessingStatus.PROCESSED.value,
    )

    with patch(
        "app.repositories.payment.PaymentWebhookRepository.get_event",
        new=AsyncMock(return_value=existing_event),
    ):
        res = client.post(
            "/api/v1/payments/webhooks/mock",
            content=payload_bytes,
            headers={"Content-Type": "application/json", "X-Mock-Signature": sig},
        )
        assert res.status_code == 200
        data = res.json()["data"]
        assert data["status"] == "ignored"
        assert data["reason"] == "duplicate_event"


def test_webhook_payload_exceeds_max_bytes_rejected(client: TestClient):
    """Payloads exceeding maximum size limit are rejected with 400."""
    oversized_bytes = b"x" * 70000  # Default limit is 65536
    res = client.post(
        "/api/v1/payments/webhooks/mock",
        content=oversized_bytes,
        headers={"Content-Type": "application/json", "X-Mock-Signature": "sig"},
    )
    assert res.status_code == 400
    assert "maximum" in res.json()["error"]["message"].lower()
