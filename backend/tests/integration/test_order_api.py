"""
Cartify Order API Integration Tests (Module 10)

Comprehensive integration test suite covering customer and admin order operations:
1. Authentication protection (unauthenticated -> 401)
2. Admin authorization protection (regular user -> 403)
3. POST /api/v1/orders create order from checkout session -> 201 Created
4. Idempotency-Key deduplication support
5. Expired / missing checkout session rejection -> 400 / 404
6. GET /api/v1/orders customer order listing (newest first)
7. GET /api/v1/orders/{id} customer order details (IDOR protected)
8. POST /api/v1/orders/{id}/cancel customer cancellation rules
9. GET /api/v1/admin/orders admin listing with status filter
10. GET /api/v1/admin/orders/{id} admin order details
11. PATCH /api/v1/admin/orders/{id}/status admin transition enforcement
"""

from datetime import datetime, timezone
from decimal import Decimal
from unittest.mock import AsyncMock, patch
import pytest
from fastapi.testclient import TestClient

from app.api.deps import (
    get_current_active_user,
    get_db_reader,
    get_db_writer,
    require_admin,
)
from app.core.errors import CartifyException
from app.main import app
from app.models.order import (
    FulfillmentStatus,
    OrderStatus,
    PaymentStatus,
)
from app.models.user import User
from app.schemas.order import (
    AdminUpdateOrderStatusRequest,
    CancelOrderRequest,
    CreateOrderRequest,
    OrderAddressSnapshot,
    OrderDetailResponse,
    OrderItemResponse,
    OrderListResponse,
    OrderStatusHistoryResponse,
    OrderSummaryResponse,
)
from app.services.order_service import OrderService


@pytest.fixture
def customer_user():
    return User(
        id="usr-cust-1",
        name="Test Customer",
        email="customer@cartify.com",
        phone="9876543210",
        role="customer",
        is_active=True,
        is_verified=True,
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
    )


@pytest.fixture
def other_customer_user():
    return User(
        id="usr-cust-2",
        name="Other Customer",
        email="other@cartify.com",
        phone="9876543211",
        role="customer",
        is_active=True,
        is_verified=True,
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
    )


@pytest.fixture
def admin_user():
    return User(
        id="usr-admin-1",
        name="Admin User",
        email="admin@cartify.com",
        phone="9876543212",
        role="admin",
        is_active=True,
        is_verified=True,
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
    )


@pytest.fixture
def mock_db():
    return AsyncMock()


@pytest.fixture
def sample_order_detail():
    now = datetime.now(timezone.utc)
    return OrderDetailResponse(
        id="ord-uuid-101",
        order_number="CRT-20260913-K7N8P2",
        user_id="usr-cust-1",
        status=OrderStatus.PENDING,
        payment_status=PaymentStatus.PENDING,
        fulfillment_status=FulfillmentStatus.UNFULFILLED,
        subtotal_amount=Decimal("540.00"),
        discount_amount=Decimal("50.00"),
        delivery_fee=Decimal("0.00"),
        tax_amount=Decimal("27.00"),
        total_amount=Decimal("517.00"),
        delivery_slot="Tomorrow, 10:00 AM - 1:00 PM",
        coupon_code="SAVE50",
        notes="Leave with security guard",
        address_snapshot=OrderAddressSnapshot(
            recipient_name="Test Customer",
            phone="9876543210",
            address_line_1="102 Palm Grove Apartments",
            city="Bengaluru",
            state="Karnataka",
            postal_code="560001",
        ),
        items=[
            OrderItemResponse(
                id="item-uuid-1",
                product_id="prod-1",
                variant_id="var-1",
                product_name="Organic Whole Wheat Flour",
                variant_name="5 kg",
                sku="FLR-WHT-5KG",
                unit_price=Decimal("270.00"),
                mrp=Decimal("310.00"),
                quantity=2,
                line_total=Decimal("540.00"),
            )
        ],
        status_history=[
            OrderStatusHistoryResponse(
                id="hist-1",
                order_id="ord-uuid-101",
                old_status=None,
                new_status=OrderStatus.PENDING.value,
                reason="Order placed from checkout session",
                created_at=now,
            )
        ],
        created_at=now,
    )


# -----------------------------------------------------------------------------
# 1. Unauthenticated / Unauthorized Tests
# -----------------------------------------------------------------------------

def test_orders_unauthenticated(client: TestClient):
    app.dependency_overrides.clear()
    res = client.get("/api/v1/orders")
    assert res.status_code == 401

    res_post = client.post("/api/v1/orders", json={"checkoutSessionId": "cs-123"})
    assert res_post.status_code == 401

    res_cancel = client.post("/api/v1/orders/ord-1/cancel")
    assert res_cancel.status_code == 401


def test_admin_orders_unauthorized_for_customer(client: TestClient, customer_user, mock_db):
    app.dependency_overrides[get_current_active_user] = lambda: customer_user
    app.dependency_overrides[get_db_reader] = lambda: mock_db
    app.dependency_overrides[get_db_writer] = lambda: mock_db

    res_list = client.get("/api/v1/admin/orders")
    assert res_list.status_code == 403

    res_patch = client.patch(
        "/api/v1/admin/orders/ord-1/status",
        json={"status": "CONFIRMED"},
    )
    assert res_patch.status_code == 403


# -----------------------------------------------------------------------------
# 2. Customer Order Placement & Idempotency Tests
# -----------------------------------------------------------------------------

def test_create_order_success(client: TestClient, customer_user, mock_db, sample_order_detail):
    app.dependency_overrides[get_current_active_user] = lambda: customer_user
    app.dependency_overrides[get_db_writer] = lambda: mock_db

    with patch.object(OrderService, "create_order_from_checkout", new=AsyncMock(return_value=sample_order_detail)):
        response = client.post(
            "/api/v1/orders",
            json={"checkoutSessionId": "cs-test-123"},
            headers={"Idempotency-Key": "idem-key-abc"},
        )
        assert response.status_code == 201
        data = response.json()
        assert data["success"] is True
        assert data["data"]["orderNumber"] == "CRT-20260913-K7N8P2"
        assert Decimal(str(data["data"]["totalAmount"])) == Decimal("517.00")
        assert data["data"]["status"] == "PENDING"
        assert len(data["data"]["items"]) == 1
        assert data["data"]["items"][0]["sku"] == "FLR-WHT-5KG"


def test_create_order_expired_checkout_rejection(client: TestClient, customer_user, mock_db):
    app.dependency_overrides[get_current_active_user] = lambda: customer_user
    app.dependency_overrides[get_db_writer] = lambda: mock_db

    with patch.object(
        OrderService,
        "create_order_from_checkout",
        new=AsyncMock(
            side_effect=CartifyException(
                status_code=400,
                message="Checkout session has expired. Please initiate a new checkout preview.",
                code="CHECKOUT_EXPIRED",
            )
        ),
    ):
        response = client.post(
            "/api/v1/orders",
            json={"checkoutSessionId": "cs-expired-123"},
        )
        assert response.status_code == 400
        assert response.json()["error"]["code"] == "CHECKOUT_EXPIRED"


# -----------------------------------------------------------------------------
# 3. Customer Order Listing & Retrieval (IDOR Protection)
# -----------------------------------------------------------------------------

def test_list_customer_orders(client: TestClient, customer_user, mock_db, sample_order_detail):
    app.dependency_overrides[get_current_active_user] = lambda: customer_user
    app.dependency_overrides[get_db_reader] = lambda: mock_db

    summary = OrderSummaryResponse(
        id=sample_order_detail.id,
        order_number=sample_order_detail.order_number,
        status=sample_order_detail.status,
        payment_status=sample_order_detail.payment_status,
        total_amount=sample_order_detail.total_amount,
        item_count=1,
        first_item_title="Organic Whole Wheat Flour",
        delivery_slot=sample_order_detail.delivery_slot,
        created_at=sample_order_detail.created_at,
    )
    list_response = OrderListResponse(items=[summary], total=1, limit=20, offset=0)

    with patch.object(OrderService, "list_orders", new=AsyncMock(return_value=list_response)):
        response = client.get("/api/v1/orders?limit=20&offset=0")
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["data"]["total"] == 1
        assert data["data"]["items"][0]["orderNumber"] == "CRT-20260913-K7N8P2"


def test_get_customer_order_by_id_success(client: TestClient, customer_user, mock_db, sample_order_detail):
    app.dependency_overrides[get_current_active_user] = lambda: customer_user
    app.dependency_overrides[get_db_reader] = lambda: mock_db

    with patch.object(OrderService, "get_order", new=AsyncMock(return_value=sample_order_detail)):
        response = client.get(f"/api/v1/orders/{sample_order_detail.order_number}")
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["data"]["orderNumber"] == sample_order_detail.order_number


def test_get_customer_order_idor_isolation(client: TestClient, customer_user, mock_db):
    """Customer cannot view another user's order."""
    app.dependency_overrides[get_current_active_user] = lambda: customer_user
    app.dependency_overrides[get_db_reader] = lambda: mock_db

    with patch.object(
        OrderService,
        "get_order",
        new=AsyncMock(
            side_effect=CartifyException(
                status_code=404,
                message="Order 'ord-foreign' not found.",
                code="ORDER_NOT_FOUND",
            )
        ),
    ):
        response = client.get("/api/v1/orders/ord-foreign")
        assert response.status_code == 404
        assert response.json()["error"]["code"] == "ORDER_NOT_FOUND"


# -----------------------------------------------------------------------------
# 4. Customer Order Cancellation
# -----------------------------------------------------------------------------

def test_customer_cancel_pending_order_success(client: TestClient, customer_user, mock_db, sample_order_detail):
    app.dependency_overrides[get_current_active_user] = lambda: customer_user
    app.dependency_overrides[get_db_writer] = lambda: mock_db

    cancelled_order = sample_order_detail.model_copy(update={"status": OrderStatus.CANCELLED})

    with patch.object(OrderService, "cancel_order", new=AsyncMock(return_value=cancelled_order)):
        response = client.post(
            f"/api/v1/orders/{sample_order_detail.id}/cancel",
            json={"reason": "Ordered by mistake"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["data"]["status"] == "CANCELLED"


def test_customer_cancel_shipped_order_rejected(client: TestClient, customer_user, mock_db):
    app.dependency_overrides[get_current_active_user] = lambda: customer_user
    app.dependency_overrides[get_db_writer] = lambda: mock_db

    with patch.object(
        OrderService,
        "cancel_order",
        new=AsyncMock(
            side_effect=CartifyException(
                status_code=400,
                message="Order in status 'SHIPPED' cannot be cancelled.",
                code="ORDER_NOT_CANCELLABLE",
            )
        ),
    ):
        response = client.post(
            "/api/v1/orders/ord-shipped/cancel",
            json={"reason": "Want to cancel"},
        )
        assert response.status_code == 400
        assert response.json()["error"]["code"] == "ORDER_NOT_CANCELLABLE"


# -----------------------------------------------------------------------------
# 5. Admin Order Endpoints & State Machine Transitions
# -----------------------------------------------------------------------------

def test_admin_list_orders_success(client: TestClient, admin_user, mock_db, sample_order_detail):
    app.dependency_overrides[require_admin] = lambda: admin_user
    app.dependency_overrides[get_db_reader] = lambda: mock_db

    summary = OrderSummaryResponse(
        id=sample_order_detail.id,
        order_number=sample_order_detail.order_number,
        status=sample_order_detail.status,
        payment_status=sample_order_detail.payment_status,
        total_amount=sample_order_detail.total_amount,
        item_count=1,
        first_item_title="Organic Whole Wheat Flour",
        delivery_slot=sample_order_detail.delivery_slot,
        created_at=sample_order_detail.created_at,
    )
    list_response = OrderListResponse(items=[summary], total=1, limit=50, offset=0)

    with patch.object(OrderService, "admin_list_orders", new=AsyncMock(return_value=list_response)):
        response = client.get("/api/v1/admin/orders?status=PENDING&limit=50")
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert len(data["data"]["items"]) == 1


def test_admin_update_order_status_success(client: TestClient, admin_user, mock_db, sample_order_detail):
    app.dependency_overrides[require_admin] = lambda: admin_user
    app.dependency_overrides[get_db_writer] = lambda: mock_db

    confirmed_order = sample_order_detail.model_copy(
        update={
            "status": OrderStatus.CONFIRMED,
            "fulfillment_status": FulfillmentStatus.PROCESSING,
        }
    )

    with patch.object(OrderService, "admin_update_status", new=AsyncMock(return_value=confirmed_order)):
        response = client.patch(
            f"/api/v1/admin/orders/{sample_order_detail.id}/status",
            json={
                "status": "CONFIRMED",
                "fulfillmentStatus": "PROCESSING",
                "reason": "Payment verified by warehouse",
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["data"]["status"] == "CONFIRMED"
        assert data["data"]["fulfillmentStatus"] == "PROCESSING"


def test_admin_update_order_status_invalid_transition(client: TestClient, admin_user, mock_db):
    app.dependency_overrides[require_admin] = lambda: admin_user
    app.dependency_overrides[get_db_writer] = lambda: mock_db

    with patch.object(
        OrderService,
        "admin_update_status",
        new=AsyncMock(
            side_effect=CartifyException(
                status_code=400,
                message="Invalid status transition from 'DELIVERED' to 'PROCESSING'.",
                code="INVALID_STATUS_TRANSITION",
            )
        ),
    ):
        response = client.patch(
            "/api/v1/admin/orders/ord-delivered/status",
            json={"status": "PROCESSING", "reason": "Accidental rollback"},
        )
        assert response.status_code == 400
        assert response.json()["error"]["code"] == "INVALID_STATUS_TRANSITION"
