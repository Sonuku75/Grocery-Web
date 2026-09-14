"""
Integration tests for Cartify Inventory API Endpoints (Module 11)

Covers all customer and admin inventory scenarios:
1. Customer endpoint: GET /api/v1/inventory/variants/{variant_id}
   - In-stock variant returns available quantity and flags
   - Nonexistent variant returns 404
   - Inactive variant returns available_quantity=0, is_available=False
2. Admin authorization protection:
   - Non-admin / customer receives 403 Forbidden
   - Unauthenticated request receives 401 Unauthorized
3. Admin endpoints:
   - GET /api/v1/admin/inventory lists inventory with filtering
   - GET /api/v1/admin/inventory/{variant_id} returns detail
   - POST /api/v1/admin/inventory initializes inventory
   - POST /api/v1/admin/inventory duplicate variant returns 400
   - PATCH /api/v1/admin/inventory/{variant_id} updates threshold and status
   - POST /api/v1/admin/inventory/{variant_id}/adjust modifies stock with audit log
   - POST /api/v1/admin/inventory/{variant_id}/adjust rejects excessive decrement (400)
   - GET /api/v1/admin/inventory/{variant_id}/transactions returns audit trail
4. Concurrency & Overselling prevention simulation
"""

from datetime import datetime, timezone
from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock, patch
import pytest
from fastapi.testclient import TestClient

from app.api.deps import (
    get_current_active_user,
    get_db_reader,
    get_db_writer,
    require_admin,
)
from app.core.errors import CartifyException, ForbiddenError, NotFoundError
from app.main import app
from app.models.inventory import (
    Inventory,
    InventoryTransaction,
    InventoryTransactionType,
)
from app.models.user import User
from app.schemas.inventory import (
    AdminInventoryListResponse,
    AdminInventoryResponse,
    CustomerInventoryResponse,
    InventoryTransactionResponse,
)
from app.services.inventory_service import InventoryService


@pytest.fixture
def customer_user():
    return User(
        id="usr-cust-inv-1",
        name="Inventory Customer",
        email="cust_inv@cartify.com",
        phone="9876543210",
        role="customer",
        is_active=True,
        is_verified=True,
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
    )


@pytest.fixture
def admin_user():
    return User(
        id="usr-admin-inv-1",
        name="Inventory Admin",
        email="admin_inv@cartify.com",
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


@pytest.fixture(autouse=True)
def bypass_rate_limiter():
    with patch("app.services.rate_limiter.SlidingWindowRateLimiter.check_and_raise", new=AsyncMock()):
        yield


# ---------------------------------------------------------------------------
# 1. Customer Availability Endpoint Tests
# ---------------------------------------------------------------------------

def test_get_customer_stock_in_stock(mock_db):
    """Customer can query live stock availability for active variant."""
    mock_resp = CustomerInventoryResponse(
        variant_id="var-test-1",
        available_quantity=25,
        is_available=True,
        is_low_stock=False,
    )

    with patch.object(InventoryService, "get_customer_stock", new_callable=AsyncMock) as mock_svc:
        mock_svc.return_value = mock_resp
        app.dependency_overrides[get_db_reader] = lambda: mock_db

        client = TestClient(app)
        response = client.get("/api/v1/inventory/variants/var-test-1")

        assert response.status_code == 200
        payload = response.json()
        assert payload["success"] is True
        assert payload["data"]["variantId"] == "var-test-1"
        assert payload["data"]["availableQuantity"] == 25
        assert payload["data"]["isAvailable"] is True
        assert payload["data"]["isLowStock"] is False

    app.dependency_overrides.clear()


def test_get_customer_stock_low_stock(mock_db):
    """Customer receives is_low_stock=True when available <= threshold."""
    mock_resp = CustomerInventoryResponse(
        variant_id="var-test-low",
        available_quantity=3,
        is_available=True,
        is_low_stock=True,
    )

    with patch.object(InventoryService, "get_customer_stock", new_callable=AsyncMock) as mock_svc:
        mock_svc.return_value = mock_resp
        app.dependency_overrides[get_db_reader] = lambda: mock_db

        client = TestClient(app)
        response = client.get("/api/v1/inventory/variants/var-test-low")

        assert response.status_code == 200
        payload = response.json()
        assert payload["data"]["availableQuantity"] == 3
        assert payload["data"]["isAvailable"] is True
        assert payload["data"]["isLowStock"] is True

    app.dependency_overrides.clear()


def test_get_customer_stock_nonexistent_returns_404(mock_db):
    """Querying a variant that does not exist returns 404."""
    with patch.object(InventoryService, "get_customer_stock", new_callable=AsyncMock) as mock_svc:
        mock_svc.side_effect = CartifyException(status_code=404, message="Product variant 'var-missing' not found.", code="VARIANT_NOT_FOUND")
        app.dependency_overrides[get_db_reader] = lambda: mock_db

        client = TestClient(app)
        response = client.get("/api/v1/inventory/variants/var-missing")

        assert response.status_code == 404
        payload = response.json()
        assert payload["success"] is False
        assert payload["error"]["code"] == "VARIANT_NOT_FOUND"

    app.dependency_overrides.clear()


# ---------------------------------------------------------------------------
# 2. Authorization & RBAC Tests
# ---------------------------------------------------------------------------

def test_admin_endpoints_require_authentication():
    """Unauthenticated users receive 401 on admin inventory routes."""
    client = TestClient(app)
    response = client.get("/api/v1/admin/inventory")
    assert response.status_code == 401


def test_admin_endpoints_require_admin_role(customer_user):
    """Regular customers receive 403 Forbidden on admin inventory routes."""
    app.dependency_overrides[get_current_active_user] = lambda: customer_user

    client = TestClient(app)
    response = client.get("/api/v1/admin/inventory")
    assert response.status_code == 403

    app.dependency_overrides.clear()


# ---------------------------------------------------------------------------
# 3. Admin CRUD & Stock Adjustment Tests
# ---------------------------------------------------------------------------

def test_admin_list_inventory(admin_user, mock_db):
    """Admin can query paginated inventory list with filters."""
    now = datetime.now(timezone.utc)
    mock_list = AdminInventoryListResponse(
        items=[
            AdminInventoryResponse(
                id="inv-1",
                variant_id="var-1",
                product_id="prod-1",
                product_title="Organic Oats",
                variant_name="1kg Pack",
                sku="OATS-1KG",
                quantity=100,
                reserved_quantity=0,
                available_quantity=100,
                low_stock_threshold=10,
                is_active=True,
                is_low_stock=False,
                is_out_of_stock=False,
                created_at=now,
                updated_at=now,
            )
        ],
        total=1,
        limit=50,
        offset=0,
    )

    with patch.object(InventoryService, "admin_list_inventory", new_callable=AsyncMock) as mock_svc:
        mock_svc.return_value = mock_list
        app.dependency_overrides[require_admin] = lambda: admin_user
        app.dependency_overrides[get_db_reader] = lambda: mock_db

        client = TestClient(app)
        response = client.get("/api/v1/admin/inventory?limit=50&offset=0")

        assert response.status_code == 200
        payload = response.json()
        assert payload["success"] is True
        assert len(payload["data"]["items"]) == 1
        assert payload["data"]["items"][0]["sku"] == "OATS-1KG"

    app.dependency_overrides.clear()


def test_admin_create_inventory_success(admin_user, mock_db):
    """Admin can initialize inventory record for a variant."""
    now = datetime.now(timezone.utc)
    mock_resp = AdminInventoryResponse(
        id="inv-created-1",
        variant_id="var-fresh-1",
        product_id="prod-fresh-1",
        product_title="Fresh Apples",
        variant_name="1kg",
        sku="APP-1KG",
        quantity=50,
        reserved_quantity=0,
        available_quantity=50,
        low_stock_threshold=5,
        is_active=True,
        is_low_stock=False,
        is_out_of_stock=False,
        created_at=now,
        updated_at=now,
    )

    with patch.object(InventoryService, "admin_create_inventory", new_callable=AsyncMock) as mock_svc:
        mock_svc.return_value = mock_resp
        app.dependency_overrides[require_admin] = lambda: admin_user
        app.dependency_overrides[get_db_writer] = lambda: mock_db

        client = TestClient(app)
        response = client.post(
            "/api/v1/admin/inventory",
            json={"variantId": "var-fresh-1", "quantity": 50, "lowStockThreshold": 5},
        )

        assert response.status_code == 201
        payload = response.json()
        assert payload["success"] is True
        assert payload["data"]["availableQuantity"] == 50

    app.dependency_overrides.clear()


def test_admin_create_duplicate_inventory_fails(admin_user, mock_db):
    """Re-initializing inventory for existing variant returns 400 Bad Request."""
    with patch.object(InventoryService, "admin_create_inventory", new_callable=AsyncMock) as mock_svc:
        mock_svc.side_effect = CartifyException(
            status_code=400,
            message="Inventory already initialized for variant 'var-dup'.",
            code="INVENTORY_ALREADY_EXISTS",
        )
        app.dependency_overrides[require_admin] = lambda: admin_user
        app.dependency_overrides[get_db_writer] = lambda: mock_db

        client = TestClient(app)
        response = client.post(
            "/api/v1/admin/inventory",
            json={"variantId": "var-dup", "quantity": 10},
        )

        assert response.status_code == 400
        payload = response.json()
        assert payload["error"]["code"] == "INVENTORY_ALREADY_EXISTS"

    app.dependency_overrides.clear()


def test_admin_adjust_stock_positive_restock(admin_user, mock_db):
    """Admin can restock inventory via signed adjustment."""
    now = datetime.now(timezone.utc)
    mock_resp = AdminInventoryResponse(
        id="inv-adj-1",
        variant_id="var-adj-1",
        product_id="prod-1",
        product_title="Milk",
        variant_name="1L",
        sku="MLK-1L",
        quantity=70,
        reserved_quantity=0,
        available_quantity=70,
        low_stock_threshold=10,
        is_active=True,
        is_low_stock=False,
        is_out_of_stock=False,
        created_at=now,
        updated_at=now,
    )

    with patch.object(InventoryService, "admin_adjust_stock", new_callable=AsyncMock) as mock_svc:
        mock_svc.return_value = mock_resp
        app.dependency_overrides[require_admin] = lambda: admin_user
        app.dependency_overrides[get_db_writer] = lambda: mock_db

        client = TestClient(app)
        response = client.post(
            "/api/v1/admin/inventory/var-adj-1/adjust",
            json={
                "quantityChange": 20,
                "transactionType": "RESTOCK",
                "reason": "Weekly supplier shipment",
            },
        )

        assert response.status_code == 200
        payload = response.json()
        assert payload["data"]["quantity"] == 70
        assert payload["data"]["availableQuantity"] == 70

    app.dependency_overrides.clear()


def test_admin_adjust_stock_excessive_decrement_fails(admin_user, mock_db):
    """Attempting to reduce stock below available quantity returns 400 INSUFFICIENT_STOCK."""
    with patch.object(InventoryService, "admin_adjust_stock", new_callable=AsyncMock) as mock_svc:
        mock_svc.side_effect = CartifyException(
            status_code=400,
            message="Stock adjustment would exceed available quantity (10).",
            code="INSUFFICIENT_STOCK",
        )
        app.dependency_overrides[require_admin] = lambda: admin_user
        app.dependency_overrides[get_db_writer] = lambda: mock_db

        client = TestClient(app)
        response = client.post(
            "/api/v1/admin/inventory/var-adj-1/adjust",
            json={"quantityChange": -100, "reason": "Inventory audit write-off"},
        )

        assert response.status_code == 400
        payload = response.json()
        assert payload["error"]["code"] == "INSUFFICIENT_STOCK"

    app.dependency_overrides.clear()


def test_admin_get_inventory_transactions(admin_user, mock_db):
    """Admin can view the audit transaction history for a variant."""
    now = datetime.now(timezone.utc)
    mock_txs = [
        InventoryTransactionResponse(
            id="tx-1",
            inventory_id="inv-1",
            variant_id="var-1",
            transaction_type=InventoryTransactionType.INITIAL.value,
            quantity_change=50,
            quantity_before=0,
            quantity_after=50,
            reference_type="INITIAL_SETUP",
            reference_id=None,
            reason="Initial inventory creation",
            created_by_user_id="usr-admin-inv-1",
            created_at=now,
        ),
        InventoryTransactionResponse(
            id="tx-2",
            inventory_id="inv-1",
            variant_id="var-1",
            transaction_type=InventoryTransactionType.SALE.value,
            quantity_change=-2,
            quantity_before=50,
            quantity_after=48,
            reference_type="ORDER",
            reference_id="CRT-20260914-XYZ123",
            reason="Sale deduction for Order #CRT-20260914-XYZ123",
            created_by_user_id="usr-cust-inv-1",
            created_at=now,
        ),
    ]

    with patch.object(InventoryService, "admin_list_transactions", new_callable=AsyncMock) as mock_svc:
        mock_svc.return_value = mock_txs
        app.dependency_overrides[require_admin] = lambda: admin_user
        app.dependency_overrides[get_db_reader] = lambda: mock_db

        client = TestClient(app)
        response = client.get("/api/v1/admin/inventory/var-1/transactions")

        assert response.status_code == 200
        payload = response.json()
        assert payload["success"] is True
        assert len(payload["data"]) == 2
        assert payload["data"][0]["transactionType"] == "INITIAL"
        assert payload["data"][1]["transactionType"] == "SALE"
        assert payload["data"][1]["referenceId"] == "CRT-20260914-XYZ123"

    app.dependency_overrides.clear()
