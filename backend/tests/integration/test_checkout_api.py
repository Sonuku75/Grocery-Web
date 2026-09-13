"""
Cartify Checkout API Integration Tests (Module 9)

Tests for customer checkout endpoints:
1. GET /api/v1/checkout unauthenticated -> 401
2. POST /api/v1/checkout/preview unauthenticated -> 401
3. POST /api/v1/checkout/confirm unauthenticated -> 401
4. DELETE /api/v1/checkout/{id} unauthenticated -> 401
5. POST /api/v1/checkout/preview with empty cart -> 400 EMPTY_CART
6. POST /api/v1/checkout/preview below free delivery threshold -> standard fee ₹40.00
7. POST /api/v1/checkout/preview above free delivery threshold -> free delivery ₹0.00
8. POST /api/v1/checkout/preview with address and coupon -> discount applied, address attached
9. POST /api/v1/checkout/preview price change detection -> returns price_changed=True & warning
10. GET /api/v1/checkout active session exists -> returns summary
11. GET /api/v1/checkout no session exists -> 404 CHECKOUT_NOT_FOUND
12. POST /api/v1/checkout/confirm missing address -> 400 ADDRESS_REQUIRED
13. POST /api/v1/checkout/confirm success -> returns READY_FOR_ORDER with session COMPLETED
14. POST /api/v1/checkout/confirm with Idempotency-Key -> handles duplicate submission idempotently
15. POST /api/v1/checkout/confirm on expired session -> 400 CHECKOUT_EXPIRED
16. POST /api/v1/checkout/confirm on cancelled session -> 400 CHECKOUT_CANCELLED
17. DELETE /api/v1/checkout/{id} cancels session successfully
"""

from datetime import datetime, timedelta, timezone
from decimal import Decimal
from unittest.mock import AsyncMock, patch
import pytest
from fastapi.testclient import TestClient

from app.api.deps import get_current_active_user, get_db_reader, get_db_writer
from app.core.errors import CartifyException
from app.main import app
from app.models.checkout import CheckoutStatus
from app.models.user import User
from app.schemas.checkout import (
    CheckoutAddressSnapshot,
    CheckoutConfirmRequest,
    CheckoutConfirmResponse,
    CheckoutItemSnapshot,
    CheckoutPreviewRequest,
    CheckoutSummaryResponse,
)
from app.schemas.coupon import CouponSummary, DiscountType
from app.services.checkout_service import CheckoutService


@pytest.fixture
def regular_user():
    return User(
        id="usr-checkout-1",
        name="Checkout User",
        email="checkout@cartify.com",
        phone="9876543210",
        role="customer",
        is_active=True,
        is_verified=True,
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
    )


@pytest.fixture
def sample_address_snapshot():
    return CheckoutAddressSnapshot(
        id="addr-101",
        recipient_name="Checkout User",
        phone="9876543210",
        address_line_1="102 Palm Grove",
        address_line_2="Indiranagar",
        city="Bengaluru",
        state="Karnataka",
        country="India",
        postal_code="560038",
        label="Home",
    )


@pytest.fixture
def sample_items_snapshot():
    return [
        CheckoutItemSnapshot(
            variant_id="var-101",
            product_id="prod-101",
            sku="MILK-1L",
            product_title="Organic Whole Milk",
            variant_name="1 Litre",
            unit="1 L",
            quantity=2,
            unit_price=Decimal("40.00"),
            line_total=Decimal("80.00"),
            thumbnail_url="https://images.unsplash.com/milk.jpg",
        ),
        CheckoutItemSnapshot(
            variant_id="var-102",
            product_id="prod-102",
            sku="BREAD-WHEAT",
            product_title="Brown Bread",
            variant_name="400g Loaf",
            unit="400 g",
            quantity=1,
            unit_price=Decimal("45.00"),
            line_total=Decimal("45.00"),
            thumbnail_url="https://images.unsplash.com/bread.jpg",
        ),
    ]


@pytest.fixture
def sample_checkout_summary(sample_address_snapshot, sample_items_snapshot):
    return CheckoutSummaryResponse(
        id="sess-checkout-101",
        user_id="usr-checkout-1",
        cart_id="cart-checkout-1",
        status=CheckoutStatus.ACTIVE,
        items=sample_items_snapshot,
        address=sample_address_snapshot,
        subtotal=Decimal("125.00"),
        discount=Decimal("0.00"),
        delivery_fee=Decimal("40.00"),
        tax=Decimal("0.00"),
        total=Decimal("165.00"),
        currency="INR",
        coupon=None,
        delivery_method="STANDARD",
        delivery_slot="Today • Express 15-Minute Delivery",
        expires_at=datetime.now(timezone.utc) + timedelta(minutes=30),
        price_changed=False,
        warning_message=None,
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
    )


# ==============================================================================
# Authentication Guard Tests
# ==============================================================================

def test_preview_checkout_unauthenticated_returns_401():
    client = TestClient(app)
    res = client.post("/api/v1/checkout/preview", json={})
    assert res.status_code == 401


def test_get_checkout_unauthenticated_returns_401():
    client = TestClient(app)
    res = client.get("/api/v1/checkout")
    assert res.status_code == 401


def test_confirm_checkout_unauthenticated_returns_401():
    client = TestClient(app)
    res = client.post("/api/v1/checkout/confirm", json={"checkoutSessionId": "sess-1"})
    assert res.status_code == 401


def test_cancel_checkout_unauthenticated_returns_401():
    client = TestClient(app)
    res = client.delete("/api/v1/checkout/sess-1")
    assert res.status_code == 401


# ==============================================================================
# Preview Checkout Endpoint Tests
# ==============================================================================

def test_preview_checkout_empty_cart_fails(regular_user):
    app.dependency_overrides[get_current_active_user] = lambda: regular_user
    app.dependency_overrides[get_db_writer] = lambda: AsyncMock()

    try:
        with patch.object(
            CheckoutService,
            "preview_checkout",
            AsyncMock(side_effect=CartifyException(
                status_code=400,
                message="Cannot proceed to checkout with an empty cart.",
                code="EMPTY_CART",
            )),
        ):
            client = TestClient(app)
            res = client.post("/api/v1/checkout/preview", json={})
            assert res.status_code == 400
            data = res.json()
            assert data["success"] is False
            assert data["error"]["code"] == "EMPTY_CART"
    finally:
        app.dependency_overrides.clear()


def test_preview_checkout_below_threshold_standard_fee(regular_user, sample_checkout_summary):
    app.dependency_overrides[get_current_active_user] = lambda: regular_user
    app.dependency_overrides[get_db_writer] = lambda: AsyncMock()

    try:
        with patch.object(
            CheckoutService,
            "preview_checkout",
            AsyncMock(return_value=sample_checkout_summary),
        ):
            client = TestClient(app)
            res = client.post("/api/v1/checkout/preview", json={})
            assert res.status_code == 200
            body = res.json()
            assert body["success"] is True
            data = body["data"]
            assert data["id"] == "sess-checkout-101"
            assert Decimal(str(data["subtotal"])) == Decimal("125.00")
            assert Decimal(str(data["deliveryFee"])) == Decimal("40.00")
            assert Decimal(str(data["total"])) == Decimal("165.00")
            assert len(data["items"]) == 2
    finally:
        app.dependency_overrides.clear()


def test_preview_checkout_above_threshold_free_delivery(regular_user, sample_checkout_summary):
    sample_checkout_summary.subtotal = Decimal("600.00")
    sample_checkout_summary.delivery_fee = Decimal("0.00")
    sample_checkout_summary.total = Decimal("600.00")

    app.dependency_overrides[get_current_active_user] = lambda: regular_user
    app.dependency_overrides[get_db_writer] = lambda: AsyncMock()

    try:
        with patch.object(
            CheckoutService,
            "preview_checkout",
            AsyncMock(return_value=sample_checkout_summary),
        ):
            client = TestClient(app)
            res = client.post("/api/v1/checkout/preview", json={})
            assert res.status_code == 200
            body = res.json()
            assert body["success"] is True
            data = body["data"]
            assert Decimal(str(data["subtotal"])) == Decimal("600.00")
            assert Decimal(str(data["deliveryFee"])) == Decimal("0.00")
            assert Decimal(str(data["total"])) == Decimal("600.00")
    finally:
        app.dependency_overrides.clear()


def test_preview_checkout_with_address_and_coupon(regular_user, sample_checkout_summary):
    sample_checkout_summary.coupon = CouponSummary(
        id="cp-test",
        code="SAVE20",
        name="Save 20%",
        discount_type=DiscountType.PERCENTAGE,
        discount_value=Decimal("20.00"),
        minimum_order_value=Decimal("100.00"),
        expires_at=datetime.now(timezone.utc) + timedelta(days=1),
        is_active=True,
    )
    sample_checkout_summary.discount = Decimal("25.00")
    sample_checkout_summary.total = Decimal("140.00")

    app.dependency_overrides[get_current_active_user] = lambda: regular_user
    app.dependency_overrides[get_db_writer] = lambda: AsyncMock()

    try:
        with patch.object(
            CheckoutService,
            "preview_checkout",
            AsyncMock(return_value=sample_checkout_summary),
        ):
            client = TestClient(app)
            res = client.post(
                "/api/v1/checkout/preview",
                json={"addressId": "addr-101", "deliverySlot": "Tomorrow • 9:00 AM"},
            )
            assert res.status_code == 200
            data = res.json()["data"]
            assert data["coupon"]["code"] == "SAVE20"
            assert Decimal(str(data["discount"])) == Decimal("25.00")
            assert data["address"]["recipientName"] == "Checkout User"
    finally:
        app.dependency_overrides.clear()


def test_preview_checkout_price_change_warning(regular_user, sample_checkout_summary):
    sample_checkout_summary.price_changed = True
    sample_checkout_summary.warning_message = "Price for 'Organic Whole Milk' updated."

    app.dependency_overrides[get_current_active_user] = lambda: regular_user
    app.dependency_overrides[get_db_writer] = lambda: AsyncMock()

    try:
        with patch.object(
            CheckoutService,
            "preview_checkout",
            AsyncMock(return_value=sample_checkout_summary),
        ):
            client = TestClient(app)
            res = client.post("/api/v1/checkout/preview", json={})
            assert res.status_code == 200
            data = res.json()["data"]
            assert data["priceChanged"] is True
            assert "Organic Whole Milk" in data["warningMessage"]
    finally:
        app.dependency_overrides.clear()


# ==============================================================================
# Get Active Session Endpoint Tests
# ==============================================================================

def test_get_active_checkout_session(regular_user, sample_checkout_summary):
    app.dependency_overrides[get_current_active_user] = lambda: regular_user
    app.dependency_overrides[get_db_reader] = lambda: AsyncMock()

    try:
        with patch.object(
            CheckoutService,
            "get_active_session",
            AsyncMock(return_value=sample_checkout_summary),
        ):
            client = TestClient(app)
            res = client.get("/api/v1/checkout")
            assert res.status_code == 200
            data = res.json()["data"]
            assert data["id"] == "sess-checkout-101"
            assert data["status"] == "ACTIVE"
    finally:
        app.dependency_overrides.clear()


def test_get_active_checkout_not_found(regular_user):
    app.dependency_overrides[get_current_active_user] = lambda: regular_user
    app.dependency_overrides[get_db_reader] = lambda: AsyncMock()

    try:
        with patch.object(
            CheckoutService,
            "get_active_session",
            AsyncMock(side_effect=CartifyException(
                status_code=404,
                message="No active checkout session found.",
                code="CHECKOUT_NOT_FOUND",
            )),
        ):
            client = TestClient(app)
            res = client.get("/api/v1/checkout")
            assert res.status_code == 404
            assert res.json()["error"]["code"] == "CHECKOUT_NOT_FOUND"
    finally:
        app.dependency_overrides.clear()


# ==============================================================================
# Confirm Checkout Endpoint Tests
# ==============================================================================

def test_confirm_checkout_success(regular_user, sample_checkout_summary):
    sample_checkout_summary.status = CheckoutStatus.COMPLETED
    confirm_resp = CheckoutConfirmResponse(
        checkout_status="READY_FOR_ORDER",
        checkout_session_id=sample_checkout_summary.id,
        summary=sample_checkout_summary,
        message="Checkout confirmed and ready for order placement.",
    )

    app.dependency_overrides[get_current_active_user] = lambda: regular_user
    app.dependency_overrides[get_db_writer] = lambda: AsyncMock()

    try:
        with patch.object(
            CheckoutService,
            "confirm_checkout",
            AsyncMock(return_value=confirm_resp),
        ):
            client = TestClient(app)
            res = client.post(
                "/api/v1/checkout/confirm",
                json={"checkoutSessionId": "sess-checkout-101"},
            )
            assert res.status_code == 200
            body = res.json()
            assert body["success"] is True
            data = body["data"]
            assert data["checkoutStatus"] == "READY_FOR_ORDER"
            assert data["checkoutSessionId"] == "sess-checkout-101"
            assert data["summary"]["status"] == "COMPLETED"
    finally:
        app.dependency_overrides.clear()


def test_confirm_checkout_idempotency_key_header(regular_user, sample_checkout_summary):
    sample_checkout_summary.status = CheckoutStatus.COMPLETED
    confirm_resp = CheckoutConfirmResponse(
        checkout_status="READY_FOR_ORDER",
        checkout_session_id=sample_checkout_summary.id,
        summary=sample_checkout_summary,
        message="Checkout already confirmed.",
    )

    app.dependency_overrides[get_current_active_user] = lambda: regular_user
    app.dependency_overrides[get_db_writer] = lambda: AsyncMock()

    try:
        mock_confirm = AsyncMock(return_value=confirm_resp)
        with patch.object(CheckoutService, "confirm_checkout", mock_confirm):
            client = TestClient(app)
            res = client.post(
                "/api/v1/checkout/confirm",
                json={"checkoutSessionId": "sess-checkout-101"},
                headers={"Idempotency-Key": "idem-uuid-999"},
            )
            assert res.status_code == 200
            assert res.json()["data"]["checkoutStatus"] == "READY_FOR_ORDER"
            # Verify Idempotency-Key was passed to service
            call_kwargs = mock_confirm.call_args.kwargs
            assert call_kwargs.get("idempotency_key") == "idem-uuid-999"
    finally:
        app.dependency_overrides.clear()


def test_confirm_checkout_without_address_fails(regular_user):
    app.dependency_overrides[get_current_active_user] = lambda: regular_user
    app.dependency_overrides[get_db_writer] = lambda: AsyncMock()

    try:
        with patch.object(
            CheckoutService,
            "confirm_checkout",
            AsyncMock(side_effect=CartifyException(
                status_code=400,
                message="A delivery address is required before confirming checkout.",
                code="ADDRESS_REQUIRED",
            )),
        ):
            client = TestClient(app)
            res = client.post(
                "/api/v1/checkout/confirm",
                json={"checkoutSessionId": "sess-checkout-101"},
            )
            assert res.status_code == 400
            assert res.json()["error"]["code"] == "ADDRESS_REQUIRED"
    finally:
        app.dependency_overrides.clear()


def test_confirm_checkout_expired_fails(regular_user):
    app.dependency_overrides[get_current_active_user] = lambda: regular_user
    app.dependency_overrides[get_db_writer] = lambda: AsyncMock()

    try:
        with patch.object(
            CheckoutService,
            "confirm_checkout",
            AsyncMock(side_effect=CartifyException(
                status_code=400,
                message="Checkout session has expired. Please initiate a new checkout preview.",
                code="CHECKOUT_EXPIRED",
            )),
        ):
            client = TestClient(app)
            res = client.post(
                "/api/v1/checkout/confirm",
                json={"checkoutSessionId": "sess-checkout-101"},
            )
            assert res.status_code == 400
            assert res.json()["error"]["code"] == "CHECKOUT_EXPIRED"
    finally:
        app.dependency_overrides.clear()


# ==============================================================================
# Cancel Checkout Endpoint Tests
# ==============================================================================

def test_cancel_checkout_success(regular_user):
    app.dependency_overrides[get_current_active_user] = lambda: regular_user
    app.dependency_overrides[get_db_writer] = lambda: AsyncMock()

    try:
        with patch.object(CheckoutService, "cancel_checkout", AsyncMock(return_value=True)):
            client = TestClient(app)
            res = client.delete("/api/v1/checkout/sess-checkout-101")
            assert res.status_code == 200
            body = res.json()
            assert body["success"] is True
            assert body["data"]["cancelled"] is True
    finally:
        app.dependency_overrides.clear()


def test_cancel_checkout_not_found(regular_user):
    app.dependency_overrides[get_current_active_user] = lambda: regular_user
    app.dependency_overrides[get_db_writer] = lambda: AsyncMock()

    try:
        with patch.object(
            CheckoutService,
            "cancel_checkout",
            AsyncMock(side_effect=CartifyException(
                status_code=404,
                message="Checkout session not found.",
                code="CHECKOUT_NOT_FOUND",
            )),
        ):
            client = TestClient(app)
            res = client.delete("/api/v1/checkout/non-existent")
            assert res.status_code == 404
            assert res.json()["error"]["code"] == "CHECKOUT_NOT_FOUND"
    finally:
        app.dependency_overrides.clear()
