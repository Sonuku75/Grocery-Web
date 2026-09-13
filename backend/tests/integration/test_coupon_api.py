"""
Integration tests for Cartify Coupons API (Module 8)

Covers customer and administrative coupon endpoints:
1. Public list available coupons (GET /api/v1/coupons)
2. Validate coupon unauthenticated returns 401
3. Validate coupon valid returns discount preview
4. Validate coupon invalid returns valid=False
5. Apply coupon unauthenticated returns 401
6. Apply coupon to empty cart returns 400 (EMPTY_CART)
7. Apply coupon successfully attaches to cart
8. Apply coupon below minimum order value returns 400
9. Remove applied coupon from cart (DELETE /api/v1/cart/coupon)
10. Admin create coupon by regular customer returns 403
11. Admin create coupon by admin succeeds (201)
12. Admin list coupons with stats (GET /api/v1/admin/coupons)
13. Admin update coupon (PATCH /api/v1/admin/coupons/{id})
"""

from datetime import datetime, timedelta, timezone
from decimal import Decimal
from unittest.mock import AsyncMock, patch
import pytest
from fastapi.testclient import TestClient

from app.api.deps import get_current_active_user, get_db_reader, get_db_writer, require_admin
from app.core.errors import CartifyException, NotFoundError
from app.main import app
from app.models.coupon import Coupon
from app.models.user import User
from app.schemas.cart import (
    CartItemResponse,
    CartProductSummary,
    CartResponse,
    CartVariantSummary,
)
from app.schemas.coupon import (
    CouponDetailResponse,
    CouponListResponse,
    CouponSummary,
    DiscountType,
)
from app.services.cart_service import CartService
from app.services.coupon_service import CouponService


@pytest.fixture
def regular_user():
    return User(
        id="usr-regular-1",
        name="Regular Customer",
        email="customer@cartify.com",
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
        id="usr-admin-1",
        name="Admin User",
        email="admin@cartify.com",
        phone="9876543211",
        role="admin",
        is_active=True,
        is_verified=True,
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
    )


@pytest.fixture
def sample_coupon_summary():
    return CouponSummary(
        id="coup-test-1",
        code="SAVE20",
        name="Save 20% Off",
        description="20% off on grocery staples",
        discount_type=DiscountType.PERCENTAGE,
        discount_value=Decimal("20.00"),
        minimum_order_value=Decimal("400.00"),
        maximum_discount=Decimal("200.00"),
        expires_at=datetime.now(timezone.utc) + timedelta(days=30),
        is_active=True,
    )


@pytest.fixture
def mock_active_cart(regular_user, sample_coupon_summary):
    return CartResponse(
        id="cart-test-1",
        user_id=regular_user.id,
        items=[
            CartItemResponse(
                id="item-1",
                cart_id="cart-test-1",
                product_id="prod-1",
                variant_id="var-1",
                quantity=3,
                unit_price=Decimal("200.00"),
                line_total=Decimal("600.00"),
                product=CartProductSummary(
                    id="prod-1",
                    title="Basmati Rice",
                    name="Basmati Rice",
                    slug="basmati-rice",
                    thumbnail_url="https://images.unsplash.com/rice.jpg",
                    is_active=True,
                ),
                variant=CartVariantSummary(
                    id="var-1",
                    product_id="prod-1",
                    sku="RICE-5KG",
                    name="5 KG Bag",
                    unit="5 kg",
                    price=Decimal("200.00"),
                    mrp=Decimal("250.00"),
                    stock_quantity=99,
                    is_active=True,
                ),
                created_at=datetime.now(timezone.utc),
                updated_at=datetime.now(timezone.utc),
            )
        ],
        item_count=3,
        subtotal=Decimal("600.00"),
        discount=Decimal("120.00"),
        delivery_fee=Decimal("0.00"),
        tax=Decimal("0.00"),
        total=Decimal("480.00"),
        applied_coupon=sample_coupon_summary,
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
    )


# ==============================================================================
# 1: GET /api/v1/coupons (Public)
# ==============================================================================

def test_list_public_coupons(sample_coupon_summary):
    app.dependency_overrides[get_db_reader] = lambda: AsyncMock()
    try:
        mock_list_resp = CouponListResponse(items=[sample_coupon_summary], total=1)
        with patch.object(CouponService, "get_public_coupons", AsyncMock(return_value=mock_list_resp)):
            with TestClient(app) as client:
                res = client.get("/api/v1/coupons")
                assert res.status_code == 200
                data = res.json()
                assert data["success"] is True
                assert len(data["data"]["items"]) == 1
                assert data["data"]["items"][0]["code"] == "SAVE20"
                assert Decimal(str(data["data"]["items"][0]["discountValue"])) == Decimal("20.00")
    finally:
        app.dependency_overrides.clear()


# ==============================================================================
# 2, 3, 4: POST /api/v1/cart/coupon/validate
# ==============================================================================

def test_validate_cart_coupon_unauthenticated():
    with TestClient(app) as client:
        res = client.post("/api/v1/cart/coupon/validate", json={"code": "SAVE20"})
        assert res.status_code == 401


def test_validate_cart_coupon_valid(regular_user, mock_active_cart, sample_coupon_summary):
    app.dependency_overrides[get_current_active_user] = lambda: regular_user
    app.dependency_overrides[get_db_reader] = lambda: AsyncMock()
    try:
        mock_coupon_model = Coupon(
            id="coup-test-1",
            code="SAVE20",
            name="Save 20% Off",
            discount_type="PERCENTAGE",
            discount_value=Decimal("20.00"),
            minimum_order_value=Decimal("400.00"),
            maximum_discount=Decimal("200.00"),
            starts_at=datetime.now(timezone.utc) - timedelta(days=1),
            expires_at=datetime.now(timezone.utc) + timedelta(days=30),
            is_active=True,
        )
        with patch.object(CartService, "get_cart", AsyncMock(return_value=mock_active_cart)), \
             patch.object(CouponService, "validate_coupon", AsyncMock(return_value=(True, "Coupon applied successfully!", mock_coupon_model, Decimal("120.00")))):
            with TestClient(app) as client:
                res = client.post("/api/v1/cart/coupon/validate", json={"code": "SAVE20"})
                assert res.status_code == 200
                data = res.json()
                assert data["success"] is True
                assert data["data"]["valid"] is True
                assert data["data"]["code"] == "SAVE20"
                assert Decimal(str(data["data"]["discount"])) == Decimal("120.00")
                assert data["data"]["coupon"]["code"] == "SAVE20"
    finally:
        app.dependency_overrides.clear()


def test_validate_cart_coupon_invalid(regular_user, mock_active_cart):
    app.dependency_overrides[get_current_active_user] = lambda: regular_user
    app.dependency_overrides[get_db_reader] = lambda: AsyncMock()
    try:
        with patch.object(CartService, "get_cart", AsyncMock(return_value=mock_active_cart)), \
             patch.object(CouponService, "validate_coupon", AsyncMock(return_value=(False, "Coupon code not found.", None, Decimal("0.00")))):
            with TestClient(app) as client:
                res = client.post("/api/v1/cart/coupon/validate", json={"code": "BADCODE"})
                assert res.status_code == 200
                data = res.json()
                assert data["success"] is True
                assert data["data"]["valid"] is False
                assert Decimal(str(data["data"]["discount"])) == Decimal("0.00")
    finally:
        app.dependency_overrides.clear()


# ==============================================================================
# 5, 6, 7, 8: POST /api/v1/cart/coupon (Apply Coupon)
# ==============================================================================

def test_apply_coupon_unauthenticated():
    with TestClient(app) as client:
        res = client.post("/api/v1/cart/coupon", json={"code": "SAVE20"})
        assert res.status_code == 401


def test_apply_coupon_to_empty_cart_fails(regular_user):
    app.dependency_overrides[get_current_active_user] = lambda: regular_user
    app.dependency_overrides[get_db_writer] = lambda: AsyncMock()
    try:
        with patch.object(
            CartService,
            "apply_coupon",
            AsyncMock(side_effect=CartifyException(status_code=400, message="Cannot apply coupon to an empty cart.", code="EMPTY_CART")),
        ):
            with TestClient(app) as client:
                res = client.post("/api/v1/cart/coupon", json={"code": "SAVE20"})
                assert res.status_code == 400
                data = res.json()
                assert data["success"] is False
                assert data["error"]["code"] == "EMPTY_CART"
    finally:
        app.dependency_overrides.clear()


def test_apply_coupon_success(regular_user, mock_active_cart):
    app.dependency_overrides[get_current_active_user] = lambda: regular_user
    app.dependency_overrides[get_db_writer] = lambda: AsyncMock()
    try:
        with patch.object(CartService, "apply_coupon", AsyncMock(return_value=mock_active_cart)):
            with TestClient(app) as client:
                res = client.post("/api/v1/cart/coupon", json={"code": "SAVE20"})
                assert res.status_code == 200
                data = res.json()
                assert data["success"] is True
                assert Decimal(str(data["data"]["discount"])) == Decimal("120.00")
                assert Decimal(str(data["data"]["total"])) == Decimal("480.00")
                assert data["data"]["appliedCoupon"]["code"] == "SAVE20"
    finally:
        app.dependency_overrides.clear()


def test_apply_coupon_below_minimum_fails(regular_user):
    app.dependency_overrides[get_current_active_user] = lambda: regular_user
    app.dependency_overrides[get_db_writer] = lambda: AsyncMock()
    try:
        with patch.object(
            CartService,
            "apply_coupon",
            AsyncMock(side_effect=CartifyException(status_code=400, message="Cart subtotal is below minimum.", code="INVALID_COUPON")),
        ):
            with TestClient(app) as client:
                res = client.post("/api/v1/cart/coupon", json={"code": "SAVE20"})
                assert res.status_code == 400
                data = res.json()
                assert data["success"] is False
                assert data["error"]["code"] == "INVALID_COUPON"
    finally:
        app.dependency_overrides.clear()


# ==============================================================================
# 9: DELETE /api/v1/cart/coupon (Remove Coupon)
# ==============================================================================

def test_remove_coupon_success(regular_user, mock_active_cart):
    app.dependency_overrides[get_current_active_user] = lambda: regular_user
    app.dependency_overrides[get_db_writer] = lambda: AsyncMock()
    mock_active_cart.applied_coupon = None
    mock_active_cart.discount = Decimal("0.00")
    mock_active_cart.total = Decimal("600.00")
    try:
        with patch.object(CartService, "remove_coupon", AsyncMock(return_value=mock_active_cart)):
            with TestClient(app) as client:
                res = client.delete("/api/v1/cart/coupon")
                assert res.status_code == 200
                data = res.json()
                assert data["success"] is True
                assert data["data"]["appliedCoupon"] is None
                assert Decimal(str(data["data"]["discount"])) == Decimal("0.00")
                assert Decimal(str(data["data"]["total"])) == Decimal("600.00")
    finally:
        app.dependency_overrides.clear()


# ==============================================================================
# 10, 11, 12, 13: Admin Coupon Endpoints
# ==============================================================================

def test_admin_create_coupon_non_admin_forbidden(regular_user):
    app.dependency_overrides[get_current_active_user] = lambda: regular_user
    try:
        with TestClient(app) as client:
            res = client.post(
                "/api/v1/admin/coupons",
                json={
                    "code": "TEST50",
                    "name": "Test 50",
                    "discountType": "PERCENTAGE",
                    "discountValue": "50.00",
                    "startsAt": datetime.now(timezone.utc).isoformat(),
                    "expiresAt": (datetime.now(timezone.utc) + timedelta(days=10)).isoformat(),
                },
            )
            assert res.status_code == 403
    finally:
        app.dependency_overrides.clear()


def test_admin_create_coupon_admin_success(admin_user):
    app.dependency_overrides[get_current_active_user] = lambda: admin_user
    app.dependency_overrides[require_admin] = lambda: admin_user
    app.dependency_overrides[get_db_writer] = lambda: AsyncMock()

    now = datetime.now(timezone.utc)
    mock_detail = CouponDetailResponse(
        id="coup-admin-1",
        code="TEST50",
        name="Test 50",
        discount_type=DiscountType.PERCENTAGE,
        discount_value=Decimal("50.00"),
        minimum_order_value=Decimal("100.00"),
        maximum_discount=Decimal("250.00"),
        starts_at=now,
        expires_at=now + timedelta(days=10),
        usage_limit=100,
        per_user_usage_limit=2,
        used_count=0,
        is_active=True,
    )
    try:
        with patch.object(CouponService, "admin_create_coupon", AsyncMock(return_value=mock_detail)):
            with TestClient(app) as client:
                res = client.post(
                    "/api/v1/admin/coupons",
                    json={
                        "code": "TEST50",
                        "name": "Test 50",
                        "discountType": "PERCENTAGE",
                        "discountValue": "50.00",
                        "minimumOrderValue": "100.00",
                        "maximumDiscount": "250.00",
                        "startsAt": now.isoformat(),
                        "expiresAt": (now + timedelta(days=10)).isoformat(),
                        "usageLimit": 100,
                        "perUserUsageLimit": 2,
                    },
                )
                assert res.status_code == 201
                data = res.json()
                assert data["success"] is True
                assert data["data"]["code"] == "TEST50"
                assert data["data"]["usedCount"] == 0
    finally:
        app.dependency_overrides.clear()


def test_admin_list_coupons(admin_user):
    app.dependency_overrides[get_current_active_user] = lambda: admin_user
    app.dependency_overrides[require_admin] = lambda: admin_user
    app.dependency_overrides[get_db_reader] = lambda: AsyncMock()

    now = datetime.now(timezone.utc)
    mock_detail = CouponDetailResponse(
        id="coup-admin-1",
        code="TEST50",
        name="Test 50",
        discount_type=DiscountType.PERCENTAGE,
        discount_value=Decimal("50.00"),
        starts_at=now,
        expires_at=now + timedelta(days=10),
        used_count=3,
        is_active=True,
    )
    try:
        with patch.object(CouponService, "admin_list_coupons", AsyncMock(return_value=([mock_detail], 1))):
            with TestClient(app) as client:
                res = client.get("/api/v1/admin/coupons")
                assert res.status_code == 200
                data = res.json()
                assert data["success"] is True
                assert data["data"]["total"] == 1
                assert len(data["data"]["items"]) == 1
                assert data["data"]["items"][0]["code"] == "TEST50"
    finally:
        app.dependency_overrides.clear()


def test_admin_update_coupon(admin_user):
    app.dependency_overrides[get_current_active_user] = lambda: admin_user
    app.dependency_overrides[require_admin] = lambda: admin_user
    app.dependency_overrides[get_db_writer] = lambda: AsyncMock()

    now = datetime.now(timezone.utc)
    mock_detail = CouponDetailResponse(
        id="coup-admin-1",
        code="TEST50",
        name="Updated Name",
        discount_type=DiscountType.PERCENTAGE,
        discount_value=Decimal("50.00"),
        starts_at=now,
        expires_at=now + timedelta(days=10),
        used_count=3,
        is_active=False,
    )
    try:
        with patch.object(CouponService, "admin_update_coupon", AsyncMock(return_value=mock_detail)):
            with TestClient(app) as client:
                res = client.patch(
                    "/api/v1/admin/coupons/coup-admin-1",
                    json={"name": "Updated Name", "isActive": False},
                )
                assert res.status_code == 200
                data = res.json()
                assert data["success"] is True
                assert data["data"]["name"] == "Updated Name"
                assert data["data"]["isActive"] is False
    finally:
        app.dependency_overrides.clear()
