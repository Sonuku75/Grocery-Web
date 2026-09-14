"""
Unit tests for MockPaymentProvider (Module 12)
"""

from decimal import Decimal
import pytest

from app.providers.mock import MockPaymentProvider


@pytest.mark.asyncio
async def test_mock_provider_create_order():
    provider = MockPaymentProvider()
    res = await provider.create_order(
        amount=Decimal("499.00"),
        currency="INR",
        receipt="CRT-ORD-001",
        notes={"test": "true"},
    )
    assert res["provider_order_id"].startswith("mock_order_")
    assert res["amount"] == Decimal("499.00")
    assert res["currency"] == "INR"
    assert res["metadata"]["sandbox"] is True


@pytest.mark.asyncio
async def test_mock_provider_fetch_payment():
    provider = MockPaymentProvider()
    # Success case
    normal_res = await provider.fetch_payment("pay_success_123")
    assert normal_res["status"] == "captured"

    # Simulated failure case
    fail_res = await provider.fetch_payment("pay_fail_123")
    assert fail_res["status"] == "failed"
    assert fail_res["failure_code"] == "MOCK_PAYMENT_FAILED"


def test_mock_provider_verify_signature():
    provider = MockPaymentProvider()
    order_id = "mock_order_12345"
    payment_id = "pay_valid_12345"

    valid_sig = provider.generate_mock_signature(order_id, payment_id)
    assert provider.verify_signature(order_id, payment_id, valid_sig) is True
    assert provider.verify_signature(order_id, payment_id, "mock_valid_signature") is True

    # Bad signature
    assert provider.verify_signature(order_id, payment_id, "tampered_sig") is False
    assert provider.verify_signature(order_id, payment_id, "mock_invalid_signature") is False

    # Failure simulation payment ID
    assert provider.verify_signature(order_id, "pay_fail_123", valid_sig) is False


def test_mock_provider_verify_webhook_signature():
    provider = MockPaymentProvider()
    payload = b'{"event": "payment.captured", "id": "evt_123"}'

    valid_sig = provider.generate_mock_webhook_signature(payload)
    assert provider.verify_webhook_signature(payload, valid_sig) is True
    assert provider.verify_webhook_signature(payload, "mock_webhook_sig") is True
    assert provider.verify_webhook_signature(payload, "invalid_webhook_sig") is False


@pytest.mark.asyncio
async def test_mock_provider_refund():
    provider = MockPaymentProvider()
    res = await provider.initiate_refund(
        provider_payment_id="pay_123",
        amount=Decimal("150.00"),
        currency="INR",
    )
    assert res["provider_refund_id"].startswith("mock_rfnd_")
    assert res["status"] == "processed"
    assert res["amount"] == Decimal("150.00")

    fail_res = await provider.initiate_refund(
        provider_payment_id="pay_refund_fail_123",
        amount=Decimal("150.00"),
        currency="INR",
    )
    assert fail_res["status"] == "failed"
