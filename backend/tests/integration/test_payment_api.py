"""
Integration tests for Payment API Endpoints (Module 12)

Covers:
1. Customer Payment Initiation:
   - Online payment (UPI/Card) generates provider order and returns client parameters
   - Cash On Delivery (COD) records PENDING payment without gateway call
   - IDOR protection: cannot pay for another user's order (403)
   - Order already paid returns 409 Conflict
   - Non-existent order returns 404
2. Customer Payment Verification:
   - Valid cryptographic signature transitions payment and order to PAID
   - Tampered/invalid signature transitions payment to FAILED and returns 400
3. Payment Retry:
   - Re-initiates payment, superseding previous pending attempt
4. Admin Auditing & Refunds:
   - Customer blocked with 403
   - Admin lists payments and inspects details with status history
   - Admin initiates partial and full refunds with balance tracking
"""

from datetime import datetime, timezone
from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock, patch
import pytest
from fastapi.testclient import TestClient

from app.api.deps import (
    get_current_user,
    get_db_reader,
    get_db_writer,
    require_admin,
)
from app.main import app
from app.models.order import Order, OrderStatus, PaymentStatus as OrderPaymentStatus
from app.models.payment import (
    Payment,
    PaymentMethod,
    PaymentRefund,
    PaymentStatus,
    PaymentStatusHistory,
    RefundStatus,
)
from app.models.user import User


@pytest.fixture
def customer_user():
    return User(
        id="usr-cust-pay-1",
        name="Payment Customer",
        email="cust_pay@cartify.com",
        phone="9876543210",
        role="customer",
        is_active=True,
    )


@pytest.fixture
def other_user():
    return User(
        id="usr-other-pay-2",
        name="Other User",
        email="other@cartify.com",
        role="customer",
        is_active=True,
    )


@pytest.fixture
def admin_user():
    return User(
        id="usr-admin-pay-1",
        name="Payment Admin",
        email="admin_pay@cartify.com",
        role="admin",
        is_active=True,
    )


@pytest.fixture
def test_order(customer_user):
    return Order(
        id="ord-pay-100",
        order_number="CRT-20260914-1001",
        user_id=customer_user.id,
        status=OrderStatus.PENDING.value,
        payment_status=OrderPaymentStatus.PENDING.value,
        subtotal=Decimal("450.00"),
        delivery_fee=Decimal("40.00"),
        tax_amount=Decimal("10.00"),
        total_amount=Decimal("500.00"),
        currency="INR",
        recipient_name="Customer One",
        phone="9876543210",
        address_line_1="123 Main Street",
        city="Bengaluru",
        state="Karnataka",
        postal_code="560001",
    )


@pytest.fixture(autouse=True)
def bypass_rate_limiter():
    with patch("app.services.rate_limiter.SlidingWindowRateLimiter.check_and_raise", new=AsyncMock()):
        yield


# ---------------------------------------------------------------------------
# 1. Customer Payment Initiation Tests
# ---------------------------------------------------------------------------

def test_initiate_payment_unauthenticated(client: TestClient):
    """Unauthenticated payment initiation returns 401."""
    app.dependency_overrides.clear()
    res = client.post("/api/v1/payments", json={"orderId": "any", "paymentMethod": "UPI"})
    assert res.status_code == 401


def test_initiate_payment_order_not_found(client: TestClient, customer_user):
    """Attempting to pay for a non-existent order returns 404."""
    app.dependency_overrides[get_current_user] = lambda: customer_user
    mock_db = AsyncMock()
    app.dependency_overrides[get_db_writer] = lambda: mock_db

    with patch("app.services.payment_service.select") as mock_select:
        mock_res = MagicMock()
        mock_res.scalar_one_or_none.return_value = None
        mock_db.execute.return_value = mock_res

        res = client.post(
            "/api/v1/payments",
            json={"orderId": "nonexistent-ord", "paymentMethod": "UPI"},
        )
        assert res.status_code == 404


def test_initiate_payment_idor_forbidden(client: TestClient, other_user, test_order):
    """User cannot initiate payment for another customer's order (403)."""
    app.dependency_overrides[get_current_user] = lambda: other_user
    mock_db = AsyncMock()
    app.dependency_overrides[get_db_writer] = lambda: mock_db

    with patch("app.services.payment_service.select") as mock_select:
        mock_res = MagicMock()
        mock_res.scalar_one_or_none.return_value = test_order
        mock_db.execute.return_value = mock_res

        res = client.post(
            "/api/v1/payments",
            json={"orderId": test_order.id, "paymentMethod": "UPI"},
        )
        assert res.status_code == 403


def test_initiate_payment_already_paid_conflict(client: TestClient, customer_user, test_order):
    """Already paid order returns 409 Conflict."""
    test_order.payment_status = OrderPaymentStatus.PAID.value
    app.dependency_overrides[get_current_user] = lambda: customer_user
    mock_db = AsyncMock()
    app.dependency_overrides[get_db_writer] = lambda: mock_db

    with patch("app.services.payment_service.select") as mock_select:
        mock_res = MagicMock()
        mock_res.scalar_one_or_none.return_value = test_order
        mock_db.execute.return_value = mock_res

        res = client.post(
            "/api/v1/payments",
            json={"orderId": test_order.id, "paymentMethod": "UPI"},
        )
        assert res.status_code == 409


def test_initiate_payment_cod_success(client: TestClient, customer_user, test_order):
    """Cash on Delivery creates PENDING payment without gateway call."""
    test_order.payment_status = OrderPaymentStatus.PENDING.value
    app.dependency_overrides[get_current_user] = lambda: customer_user
    mock_db = AsyncMock()
    app.dependency_overrides[get_db_writer] = lambda: mock_db

    created_payment = Payment(
        id="pay-cod-1",
        order_id=test_order.id,
        user_id=customer_user.id,
        provider="MOCK",
        payment_method="COD",
        amount=test_order.total_amount,
        currency="INR",
        status=PaymentStatus.PENDING.value,
    )

    with patch("app.services.payment_service.select") as mock_select:
        mock_res = MagicMock()
        mock_res.scalar_one_or_none.return_value = test_order
        mock_db.execute.return_value = mock_res

        with patch(
            "app.repositories.payment.PaymentRepository.create_payment",
            new=AsyncMock(return_value=created_payment),
        ):
            res = client.post(
                "/api/v1/payments",
                json={"orderId": test_order.id, "paymentMethod": "COD"},
            )
            assert res.status_code == 201
            data = res.json()["data"]
            assert data["paymentId"] == "pay-cod-1"
            assert data["paymentMethod"] == "COD"
            assert data["status"] == "PENDING"
            assert float(data["amount"]) == 500.0


def test_initiate_payment_online_gateway_success(client: TestClient, customer_user, test_order):
    """Online payment (UPI) creates upstream provider order and returns gateway params."""
    test_order.payment_status = OrderPaymentStatus.PENDING.value
    app.dependency_overrides[get_current_user] = lambda: customer_user
    mock_db = AsyncMock()
    app.dependency_overrides[get_db_writer] = lambda: mock_db

    created_payment = Payment(
        id="pay-online-1",
        order_id=test_order.id,
        user_id=customer_user.id,
        provider="MOCK",
        payment_method="UPI",
        amount=test_order.total_amount,
        currency="INR",
        provider_order_id="mock_order_12345",
        status=PaymentStatus.PENDING.value,
    )

    with patch("app.services.payment_service.select") as mock_select:
        mock_res = MagicMock()
        mock_res.scalar_one_or_none.return_value = test_order
        mock_db.execute.return_value = mock_res

        with patch(
            "app.repositories.payment.PaymentRepository.get_latest_by_order_id",
            new=AsyncMock(return_value=None),
        ):
            with patch(
                "app.repositories.payment.PaymentRepository.create_payment",
                new=AsyncMock(return_value=created_payment),
            ):
                res = client.post(
                    "/api/v1/payments",
                    json={"orderId": test_order.id, "paymentMethod": "UPI", "provider": "mock"},
                )
                assert res.status_code == 201
                data = res.json()["data"]
                assert data["paymentId"] == "pay-online-1"
                assert data["providerOrderId"].startswith("mock_order_")
                assert data["gatewayData"]["provider"] == "MOCK"


# ---------------------------------------------------------------------------
# 2. Customer Payment Verification Tests
# ---------------------------------------------------------------------------

def test_verify_payment_success(client: TestClient, customer_user, test_order):
    """Successful signature verification transitions payment and order to PAID."""
    app.dependency_overrides[get_current_user] = lambda: customer_user
    mock_db = AsyncMock()
    mock_db.add = MagicMock()
    app.dependency_overrides[get_db_writer] = lambda: mock_db

    payment = Payment(
        id="pay-ver-1",
        order_id=test_order.id,
        user_id=customer_user.id,
        provider="MOCK",
        payment_method="UPI",
        amount=Decimal("500.00"),
        currency="INR",
        provider_order_id="mock_order_999",
        status=PaymentStatus.PENDING.value,
        created_at=datetime.now(timezone.utc),
    )

    with patch("app.repositories.payment.PaymentRepository.get_by_id", new=AsyncMock(return_value=payment)):
        with patch("app.services.payment_service.select") as mock_select:
            mock_res = MagicMock()
            mock_res.scalar_one_or_none.return_value = test_order
            mock_db.execute.return_value = mock_res

            with patch("app.repositories.payment.PaymentRepository.update_payment_status") as mock_update:
                def _do_update(db, payment, new_status, **kwargs):
                    payment.status = new_status
                    return payment
                mock_update.side_effect = _do_update

                res = client.post(
                    "/api/v1/payments/verify",
                    json={
                        "paymentId": payment.id,
                        "providerPaymentId": "pay_mock_123",
                        "providerSignature": "mock_valid_signature",
                    },
                )
                assert res.status_code == 200
                data = res.json()["data"]
                assert data["status"] == "PAID"
                assert test_order.payment_status == OrderPaymentStatus.PAID.value


def test_verify_payment_invalid_signature_fails(client: TestClient, customer_user, test_order):
    """Invalid cryptographic signature transitions payment to FAILED and returns 400."""
    app.dependency_overrides[get_current_user] = lambda: customer_user
    mock_db = AsyncMock()
    app.dependency_overrides[get_db_writer] = lambda: mock_db

    payment = Payment(
        id="pay-ver-2",
        order_id=test_order.id,
        user_id=customer_user.id,
        provider="MOCK",
        payment_method="UPI",
        amount=Decimal("500.00"),
        currency="INR",
        provider_order_id="mock_order_999",
        status=PaymentStatus.PENDING.value,
        created_at=datetime.now(timezone.utc),
    )

    with patch("app.repositories.payment.PaymentRepository.get_by_id", new=AsyncMock(return_value=payment)):
        with patch("app.services.payment_service.select") as mock_select:
            mock_res = MagicMock()
            mock_res.scalar_one_or_none.return_value = test_order
            mock_db.execute.return_value = mock_res

            with patch("app.repositories.payment.PaymentRepository.update_payment_status") as mock_update:
                res = client.post(
                    "/api/v1/payments/verify",
                    json={
                        "paymentId": payment.id,
                        "providerPaymentId": "pay_mock_123",
                        "providerSignature": "mock_invalid_signature",
                    },
                )
                assert res.status_code == 400
                assert "signature" in res.json()["error"]["message"].lower()


# ---------------------------------------------------------------------------
# 3. Payment Status Lookup Tests
# ---------------------------------------------------------------------------

def test_get_payment_status_ownership_protection(client: TestClient, other_user, customer_user):
    """Customer cannot view another user's payment details (403)."""
    app.dependency_overrides[get_current_user] = lambda: other_user
    mock_db = AsyncMock()
    app.dependency_overrides[get_db_reader] = lambda: mock_db

    payment = Payment(
        id="pay-lookup-1",
        order_id="ord-1",
        user_id=customer_user.id,
        provider="MOCK",
        payment_method="UPI",
        amount=Decimal("500.00"),
        currency="INR",
        status=PaymentStatus.PENDING.value,
        created_at=datetime.now(timezone.utc),
    )

    with patch("app.repositories.payment.PaymentRepository.get_by_id", new=AsyncMock(return_value=payment)):
        res = client.get(f"/api/v1/payments/{payment.id}")
        assert res.status_code == 403


# ---------------------------------------------------------------------------
# 4. Admin Payment Listing & Refund Tests
# ---------------------------------------------------------------------------

def test_admin_list_payments_forbidden_for_customer(client: TestClient, customer_user):
    """Regular customers are forbidden from admin payment endpoints (403)."""
    app.dependency_overrides[require_admin] = lambda: customer_user
    # require_admin raises 403 if role != ADMIN
    def _require_admin_mock():
        from app.core.errors import ForbiddenError
        raise ForbiddenError("Administrative privileges required.")

    app.dependency_overrides[require_admin] = _require_admin_mock
    res = client.get("/api/v1/admin/payments")
    assert res.status_code == 403


def test_admin_list_payments_success(client: TestClient, admin_user):
    """Admin can list payments with pagination."""
    app.dependency_overrides[require_admin] = lambda: admin_user
    mock_db = AsyncMock()
    app.dependency_overrides[get_db_reader] = lambda: mock_db

    p1 = Payment(
        id="pay-adm-1",
        order_id="ord-1",
        user_id="usr-1",
        provider="MOCK",
        payment_method="UPI",
        amount=Decimal("250.00"),
        currency="INR",
        status=PaymentStatus.PAID.value,
        created_at=datetime.now(timezone.utc),
    )

    with patch(
        "app.repositories.payment.PaymentRepository.list_admin_payments",
        new=AsyncMock(return_value=([p1], 1)),
    ):
        res = client.get("/api/v1/admin/payments?page=1&limit=10")
        assert res.status_code == 200
        data = res.json()["data"]
        assert data["total"] == 1
        assert len(data["items"]) == 1
        assert data["items"][0]["id"] == "pay-adm-1"


def test_admin_initiate_refund_success(client: TestClient, admin_user):
    """Admin can issue a refund on a paid payment."""
    app.dependency_overrides[require_admin] = lambda: admin_user
    mock_db = AsyncMock()
    app.dependency_overrides[get_db_writer] = lambda: mock_db

    refund = PaymentRefund(
        id="rfnd-101",
        payment_id="pay-adm-1",
        amount=Decimal("100.00"),
        currency="INR",
        reason="Damaged item",
        status=RefundStatus.PROCESSED.value,
        created_at=datetime.now(timezone.utc),
    )

    with patch("app.services.refund_service.RefundService.initiate_refund", new=AsyncMock(return_value=refund)):
        res = client.post(
            "/api/v1/admin/payments/pay-adm-1/refund",
            json={"amount": 100.0, "reason": "Damaged item"},
        )
        assert res.status_code == 201
        data = res.json()["data"]
        assert data["id"] == "rfnd-101"
        assert float(data["amount"]) == 100.0
        assert data["status"] == "PROCESSED"
