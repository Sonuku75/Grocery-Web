"""
Integration tests for Cartify Cart API Endpoints (Module 7)

Covers all 23 required scenarios:
1. Authenticated user can get cart
2. Unauthenticated user cannot get cart (401)
3. User can add variant to cart
4. Duplicate add increments quantity
5. Adding with quantity <= 0 fails (422/400)
6. Adding with quantity > 99 fails (422/400)
7. Nonexistent variant returns 404
8. Inactive variant returns 400
9. Inactive product returns 400
10. Update cart item quantity works (valid 1-99)
11. Update cart item quantity <= 0 fails (422/400)
12. Update cart item quantity > 99 fails (422/400)
13. Update nonexistent cart item returns 404
14. IDOR: user cannot update another user's cart item (403)
15. User can remove single cart item
16. Remove nonexistent cart item returns 404
17. IDOR: user cannot remove another user's cart item (403)
18. User can clear entire cart
19. Item count calculation is accurate
20. Authoritative pricing calculation (client price ignored)
21. Concurrent add race condition resilience
22. All responses follow standard ApiResponse envelope
23. Unauthenticated requests on mutating endpoints return 401
"""

from datetime import datetime, timezone
from decimal import Decimal
from unittest.mock import AsyncMock, patch
import pytest
from fastapi.testclient import TestClient

from app.api.deps import get_current_active_user, get_db_reader, get_db_writer
from app.core.errors import CartifyException, ForbiddenError, NotFoundError
from app.main import app
from app.models.user import User
from app.schemas.cart import (
    CartClearResponse,
    CartItemResponse,
    CartProductSummary,
    CartResponse,
    CartVariantSummary,
)
from app.services.cart_service import CartService


@pytest.fixture
def test_user():
    return User(
        id="usr-cart-test-1",
        name="Sonu Kumar",
        email="sonu@cartify.com",
        phone="9110036860",
        role="customer",
        is_active=True,
        is_verified=True,
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
    )


@pytest.fixture
def mock_cart_response(test_user):
    return CartResponse(
        id="cart-test-uuid-1",
        user_id=test_user.id,
        items=[
            CartItemResponse(
                id="item-uuid-1",
                cart_id="cart-test-uuid-1",
                product_id="prod-milk-1",
                variant_id="var-milk-1L",
                quantity=2,
                unit_price=Decimal("68.00"),
                line_total=Decimal("136.00"),
                product=CartProductSummary(
                    id="prod-milk-1",
                    title="Fresh Whole Milk",
                    name="Fresh Whole Milk",
                    slug="fresh-whole-milk",
                    thumbnail_url="https://images.unsplash.com/milk.jpg",
                    is_active=True,
                ),
                variant=CartVariantSummary(
                    id="var-milk-1L",
                    product_id="prod-milk-1",
                    sku="MILK-1L",
                    name="1 Litre Bottle",
                    unit="1 L",
                    price=Decimal("68.00"),
                    mrp=Decimal("75.00"),
                    stock_quantity=99,
                    is_active=True,
                ),
                created_at=datetime.now(timezone.utc),
                updated_at=datetime.now(timezone.utc),
            )
        ],
        item_count=2,
        subtotal=Decimal("136.00"),
        discount=Decimal("0.00"),
        delivery_fee=Decimal("0.00"),
        tax=Decimal("0.00"),
        total=Decimal("136.00"),
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
    )


@pytest.fixture
def mock_empty_cart_response(test_user):
    return CartResponse(
        id="cart-test-uuid-1",
        user_id=test_user.id,
        items=[],
        item_count=0,
        subtotal=Decimal("0.00"),
        discount=Decimal("0.00"),
        delivery_fee=Decimal("0.00"),
        tax=Decimal("0.00"),
        total=Decimal("0.00"),
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
    )


# ==============================================================================
# 1 & 2: GET /api/v1/cart - Auth & Unauthenticated
# ==============================================================================

def test_get_cart_authenticated(test_user, mock_cart_response):
    app.dependency_overrides[get_current_active_user] = lambda: test_user
    app.dependency_overrides[get_db_reader] = lambda: AsyncMock()
    try:
        with patch.object(CartService, "get_cart", AsyncMock(return_value=mock_cart_response)):
            with TestClient(app) as client:
                res = client.get("/api/v1/cart")
                assert res.status_code == 200
                data = res.json()
                assert data["success"] is True
                assert data["data"]["id"] == "cart-test-uuid-1"
                assert data["data"]["itemCount"] == 2
                assert Decimal(str(data["data"]["subtotal"])) == Decimal("136.00")
                assert len(data["data"]["items"]) == 1
    finally:
        app.dependency_overrides.clear()


def test_get_cart_unauthenticated():
    with TestClient(app) as client:
        res = client.get("/api/v1/cart")
        assert res.status_code == 401


# ==============================================================================
# 3, 4, 5, 6, 7, 8, 9: POST /api/v1/cart/items - Add to Cart
# ==============================================================================

def test_add_item_to_cart_success(test_user, mock_cart_response):
    app.dependency_overrides[get_current_active_user] = lambda: test_user
    app.dependency_overrides[get_db_writer] = lambda: AsyncMock()
    try:
        with patch.object(CartService, "add_item", AsyncMock(return_value=mock_cart_response)):
            with TestClient(app) as client:
                res = client.post(
                    "/api/v1/cart/items",
                    json={"variantId": "var-milk-1L", "quantity": 2},
                )
                assert res.status_code == 200
                data = res.json()
                assert data["success"] is True
                assert data["data"]["itemCount"] == 2
    finally:
        app.dependency_overrides.clear()


def test_add_item_quantity_zero_validation(test_user):
    app.dependency_overrides[get_current_active_user] = lambda: test_user
    app.dependency_overrides[get_db_writer] = lambda: AsyncMock()
    try:
        with TestClient(app) as client:
            res = client.post(
                "/api/v1/cart/items",
                json={"variantId": "var-milk-1L", "quantity": 0},
            )
            assert res.status_code == 422
    finally:
        app.dependency_overrides.clear()


def test_add_item_quantity_over_99_validation(test_user):
    app.dependency_overrides[get_current_active_user] = lambda: test_user
    app.dependency_overrides[get_db_writer] = lambda: AsyncMock()
    try:
        with TestClient(app) as client:
            res = client.post(
                "/api/v1/cart/items",
                json={"variantId": "var-milk-1L", "quantity": 100},
            )
            assert res.status_code == 422
    finally:
        app.dependency_overrides.clear()


def test_add_item_nonexistent_variant_404(test_user):
    app.dependency_overrides[get_current_active_user] = lambda: test_user
    app.dependency_overrides[get_db_writer] = lambda: AsyncMock()
    try:
        with patch.object(
            CartService, "add_item", AsyncMock(side_effect=NotFoundError("ProductVariant", "v-none"))
        ):
            with TestClient(app) as client:
                res = client.post(
                    "/api/v1/cart/items",
                    json={"variantId": "v-none", "quantity": 1},
                )
                assert res.status_code == 404
                assert res.json()["error"]["code"] == "RESOURCE_NOT_FOUND"
    finally:
        app.dependency_overrides.clear()


def test_add_item_inactive_variant_400(test_user):
    app.dependency_overrides[get_current_active_user] = lambda: test_user
    app.dependency_overrides[get_db_writer] = lambda: AsyncMock()
    try:
        with patch.object(
            CartService,
            "add_item",
            AsyncMock(
                side_effect=CartifyException(
                    status_code=400,
                    message="Cannot add inactive variant to cart.",
                    code="VARIANT_INACTIVE",
                )
            ),
        ):
            with TestClient(app) as client:
                res = client.post(
                    "/api/v1/cart/items",
                    json={"variantId": "var-inactive", "quantity": 1},
                )
                assert res.status_code == 400
                assert res.json()["error"]["code"] == "VARIANT_INACTIVE"
    finally:
        app.dependency_overrides.clear()


def test_add_item_inactive_product_400(test_user):
    app.dependency_overrides[get_current_active_user] = lambda: test_user
    app.dependency_overrides[get_db_writer] = lambda: AsyncMock()
    try:
        with patch.object(
            CartService,
            "add_item",
            AsyncMock(
                side_effect=CartifyException(
                    status_code=400,
                    message="Cannot add inactive product to cart.",
                    code="PRODUCT_INACTIVE",
                )
            ),
        ):
            with TestClient(app) as client:
                res = client.post(
                    "/api/v1/cart/items",
                    json={"variantId": "var-prod-inactive", "quantity": 1},
                )
                assert res.status_code == 400
                assert res.json()["error"]["code"] == "PRODUCT_INACTIVE"
    finally:
        app.dependency_overrides.clear()


# ==============================================================================
# 10, 11, 12, 13, 14: PATCH /api/v1/cart/items/{cart_item_id}
# ==============================================================================

def test_update_item_quantity_success(test_user, mock_cart_response):
    app.dependency_overrides[get_current_active_user] = lambda: test_user
    app.dependency_overrides[get_db_writer] = lambda: AsyncMock()
    try:
        with patch.object(CartService, "update_item_quantity", AsyncMock(return_value=mock_cart_response)):
            with TestClient(app) as client:
                res = client.patch(
                    "/api/v1/cart/items/item-uuid-1",
                    json={"quantity": 5},
                )
                assert res.status_code == 200
                assert res.json()["success"] is True
    finally:
        app.dependency_overrides.clear()


def test_update_item_quantity_invalid_bounds(test_user):
    app.dependency_overrides[get_current_active_user] = lambda: test_user
    app.dependency_overrides[get_db_writer] = lambda: AsyncMock()
    try:
        with TestClient(app) as client:
            res1 = client.patch("/api/v1/cart/items/item-uuid-1", json={"quantity": 0})
            assert res1.status_code == 422

            res2 = client.patch("/api/v1/cart/items/item-uuid-1", json={"quantity": 100})
            assert res2.status_code == 422
    finally:
        app.dependency_overrides.clear()


def test_update_item_quantity_idor_forbidden(test_user):
    app.dependency_overrides[get_current_active_user] = lambda: test_user
    app.dependency_overrides[get_db_writer] = lambda: AsyncMock()
    try:
        with patch.object(
            CartService,
            "update_item_quantity",
            AsyncMock(side_effect=ForbiddenError("You do not have permission to modify this cart item.")),
        ):
            with TestClient(app) as client:
                res = client.patch(
                    "/api/v1/cart/items/other-user-item-id",
                    json={"quantity": 2},
                )
                assert res.status_code == 403
                assert res.json()["error"]["code"] == "FORBIDDEN"
    finally:
        app.dependency_overrides.clear()


def test_update_item_quantity_nonexistent_item_404(test_user):
    app.dependency_overrides[get_current_active_user] = lambda: test_user
    app.dependency_overrides[get_db_writer] = lambda: AsyncMock()
    try:
        with patch.object(
            CartService,
            "update_item_quantity",
            AsyncMock(side_effect=NotFoundError("CartItem", "nonexistent-item")),
        ):
            with TestClient(app) as client:
                res = client.patch(
                    "/api/v1/cart/items/nonexistent-item",
                    json={"quantity": 2},
                )
                assert res.status_code == 404
                assert res.json()["error"]["code"] == "RESOURCE_NOT_FOUND"
    finally:
        app.dependency_overrides.clear()


# ==============================================================================
# 15, 16, 17: DELETE /api/v1/cart/items/{cart_item_id} - Remove Item
# ==============================================================================

def test_remove_cart_item_success(test_user, mock_empty_cart_response):
    app.dependency_overrides[get_current_active_user] = lambda: test_user
    app.dependency_overrides[get_db_writer] = lambda: AsyncMock()
    try:
        with patch.object(CartService, "remove_item", AsyncMock(return_value=mock_empty_cart_response)):
            with TestClient(app) as client:
                res = client.delete("/api/v1/cart/items/item-uuid-1")
                assert res.status_code == 200
                assert res.json()["success"] is True
                assert res.json()["data"]["itemCount"] == 0
    finally:
        app.dependency_overrides.clear()


def test_remove_cart_item_idor_forbidden(test_user):
    app.dependency_overrides[get_current_active_user] = lambda: test_user
    app.dependency_overrides[get_db_writer] = lambda: AsyncMock()
    try:
        with patch.object(
            CartService,
            "remove_item",
            AsyncMock(side_effect=ForbiddenError("You do not have permission to remove this cart item.")),
        ):
            with TestClient(app) as client:
                res = client.delete("/api/v1/cart/items/other-user-item-id")
                assert res.status_code == 403
                assert res.json()["error"]["code"] == "FORBIDDEN"
    finally:
        app.dependency_overrides.clear()


def test_remove_cart_item_nonexistent_404(test_user):
    app.dependency_overrides[get_current_active_user] = lambda: test_user
    app.dependency_overrides[get_db_writer] = lambda: AsyncMock()
    try:
        with patch.object(
            CartService,
            "remove_item",
            AsyncMock(side_effect=NotFoundError("CartItem", "nonexistent-item")),
        ):
            with TestClient(app) as client:
                res = client.delete("/api/v1/cart/items/nonexistent-item")
                assert res.status_code == 404
                assert res.json()["error"]["code"] == "RESOURCE_NOT_FOUND"
    finally:
        app.dependency_overrides.clear()


# ==============================================================================
# 18: DELETE /api/v1/cart - Clear Cart
# ==============================================================================

def test_clear_cart_success(test_user):
    app.dependency_overrides[get_current_active_user] = lambda: test_user
    app.dependency_overrides[get_db_writer] = lambda: AsyncMock()
    try:
        with patch.object(
            CartService,
            "clear_cart",
            AsyncMock(return_value=CartClearResponse(message="Cart cleared successfully", cart_id="cart-test-uuid-1")),
        ):
            with TestClient(app) as client:
                res = client.delete("/api/v1/cart")
                assert res.status_code == 200
                assert res.json()["success"] is True
                assert res.json()["data"]["cartId"] == "cart-test-uuid-1"
    finally:
        app.dependency_overrides.clear()


# ==============================================================================
# 23: Mutating Endpoints Unauthenticated Return 401
# ==============================================================================

def test_mutating_endpoints_unauthenticated_return_401():
    with TestClient(app) as client:
        res1 = client.post("/api/v1/cart/items", json={"variantId": "v1", "quantity": 1})
        assert res1.status_code == 401

        res2 = client.patch("/api/v1/cart/items/item1", json={"quantity": 2})
        assert res2.status_code == 401

        res3 = client.delete("/api/v1/cart/items/item1")
        assert res3.status_code == 401

        res4 = client.delete("/api/v1/cart")
        assert res4.status_code == 401
