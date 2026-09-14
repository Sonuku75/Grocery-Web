"""
Unit tests for RefundService validation and balance checking (Module 12)
"""

from decimal import Decimal
from unittest.mock import AsyncMock, patch
import pytest

from app.core.errors import NotFoundError, ValidationError
from app.models.payment import Payment, PaymentStatus
from app.models.user import User
from app.services.refund_service import RefundService


@pytest.fixture
def paid_payment():
    return Payment(
        id="pay-test-1",
        order_id="ord-test-1",
        user_id="usr-test-1",
        provider="MOCK",
        payment_method="UPI",
        amount=Decimal("500.00"),
        currency="INR",
        status=PaymentStatus.PAID.value,
        provider_payment_id="pay_upstream_1",
    )


@pytest.fixture
def admin_user():
    return User(
        id="usr-admin-1",
        name="Admin User",
        email="admin@cartify.com",
        role="admin",
        is_active=True,
    )


@pytest.mark.asyncio
async def test_refund_service_rejects_unpaid_payment(paid_payment, admin_user):
    """Cannot refund a payment that is still PENDING or FAILED."""
    paid_payment.status = PaymentStatus.PENDING.value

    mock_db = AsyncMock()
    with patch("app.repositories.payment.PaymentRepository.get_by_id", new=AsyncMock(return_value=paid_payment)):
        with pytest.raises(ValidationError, match="Only PAID or PARTIALLY_REFUNDED"):
            await RefundService.initiate_refund(
                db=mock_db,
                payment_id="pay-test-1",
                amount=Decimal("100.00"),
                admin_user=admin_user,
            )


@pytest.mark.asyncio
async def test_refund_service_rejects_zero_or_negative_amount(paid_payment, admin_user):
    mock_db = AsyncMock()
    with patch("app.repositories.payment.PaymentRepository.get_by_id", new=AsyncMock(return_value=paid_payment)):
        with pytest.raises(ValidationError, match="strictly greater than zero"):
            await RefundService.initiate_refund(
                db=mock_db,
                payment_id="pay-test-1",
                amount=Decimal("0.00"),
                admin_user=admin_user,
            )


@pytest.mark.asyncio
async def test_refund_service_rejects_amount_exceeding_balance(paid_payment, admin_user):
    """Cannot refund more than remaining balance."""
    mock_db = AsyncMock()
    with patch("app.repositories.payment.PaymentRepository.get_by_id", new=AsyncMock(return_value=paid_payment)):
        with patch(
            "app.repositories.payment.PaymentRefundRepository.get_total_refunded_amount",
            new=AsyncMock(return_value=Decimal("400.00")),
        ):
            # Remaining is 100.00, requesting 100.01 should fail
            with pytest.raises(ValidationError, match="exceeds remaining refundable balance"):
                await RefundService.initiate_refund(
                    db=mock_db,
                    payment_id="pay-test-1",
                    amount=Decimal("150.00"),
                    admin_user=admin_user,
                )
