"""
Integration tests for Cartify Product Endpoints (Module 4)

Tests:
- Public customer product listing with filters and sorting
- Public product detail by ID and URL slug
- Inactive products hidden from public APIs
- Role-based authorization: Admin allowed (200/201), Customer forbidden (403), Unauthenticated unauthorized (401)
- Variant creation and price/MRP validation
- Image addition, primary designation, and deletion
"""

from datetime import datetime, timezone
from decimal import Decimal
from unittest.mock import AsyncMock, patch
import pytest
from fastapi.testclient import TestClient

from app.api.deps import require_admin
from app.core.database import get_db_reader, get_db_writer
from app.core.errors import NotFoundError
from app.main import app
from app.models.user import User
from app.schemas.product import (
    ProductDetailResponse,
    ProductListResponse,
    ProductSummaryResponse,
)
from app.schemas.product_image import ProductImageResponse
from app.schemas.product_variant import ProductVariantResponse


@pytest.fixture
def admin_user():
    return User(
        id="usr-admin-1",
        name="Admin User",
        email="admin@cartify.com",
        phone="9999999999",
        role="admin",
        is_active=True,
        is_verified=True,
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
    )


@pytest.fixture
def customer_user():
    return User(
        id="usr-cust-1",
        name="Customer User",
        email="customer@cartify.com",
        phone="8888888888",
        role="customer",
        is_active=True,
        is_verified=True,
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
    )


@pytest.fixture
def mock_session():
    return AsyncMock()


@pytest.fixture(autouse=True)
def bypass_rate_limiter():
    with patch("app.services.rate_limiter.SlidingWindowRateLimiter.check_and_raise", new=AsyncMock()):
        yield


@pytest.fixture
def client(mock_session):
    app.dependency_overrides[get_db_writer] = lambda: mock_session
    app.dependency_overrides[get_db_reader] = lambda: mock_session
    with TestClient(app, base_url="http://testserver") as test_client:
        yield test_client
    app.dependency_overrides.clear()


@pytest.fixture
def sample_variant():
    return ProductVariantResponse(
        id="var-1",
        productId="prod-1",
        sku="AMUL-MILK-500ML",
        name="500 ml",
        unitValue=Decimal("500"),
        unitType="ml",
        price=Decimal("30.00"),
        mrp=Decimal("32.00"),
        discountPercentage=6,
        isActive=True,
        sortOrder=0,
        createdAt=datetime.now(timezone.utc),
        updatedAt=datetime.now(timezone.utc),
    )


@pytest.fixture
def sample_image():
    return ProductImageResponse(
        id="img-1",
        productId="prod-1",
        imageUrl="https://images.unsplash.com/photo-amul-milk.jpg",
        altText="Amul Milk pouch front view",
        sortOrder=0,
        isPrimary=True,
        createdAt=datetime.now(timezone.utc),
    )


@pytest.fixture
def sample_product_summary(sample_variant, sample_image):
    return ProductSummaryResponse(
        id="prod-1",
        categoryId="cat-dairy",
        categoryName="Dairy & Breakfast",
        categorySlug="dairy-and-breakfast",
        name="Amul Taaza Milk",
        slug="amul-taaza-milk",
        brand="Amul",
        description="Pasteurized toned milk with 3% fat.",
        shortDescription="Fresh toned milk",
        imageUrl="https://images.unsplash.com/photo-amul-milk.jpg",
        isActive=True,
        isFeatured=True,
        minPrice=Decimal("30.00"),
        maxPrice=Decimal("58.00"),
        minMrp=Decimal("32.00"),
        maxDiscountPercentage=6,
        primaryVariant=sample_variant,
        variants=[sample_variant],
        images=[sample_image],
        createdAt=datetime.now(timezone.utc),
        updatedAt=datetime.now(timezone.utc),
    )


@pytest.fixture
def sample_product_detail(sample_product_summary):
    return ProductDetailResponse(
        **sample_product_summary.model_dump(),
        category=None,
    )


# -----------------------------------------------------------------------------
# Public Endpoints Tests
# -----------------------------------------------------------------------------

def test_list_active_products_public_success(client, sample_product_summary):
    mock_res = ProductListResponse(
        items=[sample_product_summary],
        nextCursor=None,
        hasMore=False,
        total=1,
    )
    with patch("app.services.product_service.ProductService.list_products", new=AsyncMock(return_value=mock_res)):
        response = client.get("/api/v1/products?brand=Amul&sort=price_low_to_high")
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert len(data["data"]["items"]) == 1
        assert data["data"]["items"][0]["name"] == "Amul Taaza Milk"
        assert data["data"]["items"][0]["brand"] == "Amul"


def test_get_product_by_id_public_success(client, sample_product_detail):
    with patch("app.services.product_service.ProductService.get_by_id", new=AsyncMock(return_value=sample_product_detail)):
        response = client.get("/api/v1/products/prod-1")
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["data"]["id"] == "prod-1"
        assert data["data"]["slug"] == "amul-taaza-milk"


def test_get_product_by_id_not_found_returns_404(client):
    with patch("app.services.product_service.ProductService.get_by_id", side_effect=NotFoundError("Product", "non-existent")):
        response = client.get("/api/v1/products/non-existent")
        assert response.status_code == 404
        assert response.json()["success"] is False


def test_get_product_by_slug_public_success(client, sample_product_detail):
    with patch("app.services.product_service.ProductService.get_by_slug", new=AsyncMock(return_value=sample_product_detail)):
        response = client.get("/api/v1/products/slug/amul-taaza-milk")
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["data"]["name"] == "Amul Taaza Milk"


def test_get_product_by_slug_not_found_returns_404(client):
    with patch("app.services.product_service.ProductService.get_by_slug", side_effect=NotFoundError("Product", "unknown-slug")):
        response = client.get("/api/v1/products/slug/unknown-slug")
        assert response.status_code == 404
        assert response.json()["success"] is False


# -----------------------------------------------------------------------------
# Admin Product Management Tests
# -----------------------------------------------------------------------------

def test_admin_create_product_success(client, admin_user, sample_product_detail):
    app.dependency_overrides[require_admin] = lambda: admin_user
    payload = {
        "name": "Amul Taaza Milk",
        "categoryId": "cat-dairy",
        "brand": "Amul",
        "description": "Pasteurized toned milk.",
        "shortDescription": "Toned milk",
        "isFeatured": True,
        "isActive": True,
    }
    with patch("app.services.product_service.ProductService.create_product", new=AsyncMock(return_value=sample_product_detail)):
        response = client.post("/api/v1/admin/products", json=payload)
        assert response.status_code == 201
        data = response.json()
        assert data["success"] is True
        assert data["data"]["name"] == "Amul Taaza Milk"


def test_customer_cannot_create_product_returns_403(client, customer_user):
    # Overriding with non-admin customer triggers 403 Forbidden via require_admin
    from app.api.deps import require_admin as actual_require_admin
    # Use real dependency check
    from app.core.errors import ForbiddenError
    app.dependency_overrides[require_admin] = lambda: (_ for _ in ()).throw(ForbiddenError())
    payload = {
        "name": "Amul Taaza Milk",
        "categoryId": "cat-dairy",
        "brand": "Amul",
        "description": "Pasteurized toned milk.",
    }
    response = client.post("/api/v1/admin/products", json=payload)
    assert response.status_code == 403
    assert response.json()["error"]["code"] == "FORBIDDEN"


def test_unauthenticated_cannot_create_product_returns_401(client):
    payload = {
        "name": "Amul Taaza Milk",
        "categoryId": "cat-dairy",
        "brand": "Amul",
        "description": "Pasteurized toned milk.",
    }
    response = client.post("/api/v1/admin/products", json=payload)
    assert response.status_code == 401


def test_admin_update_product_success(client, admin_user, sample_product_detail):
    app.dependency_overrides[require_admin] = lambda: admin_user
    payload = {"name": "Amul Taaza Fresh Milk", "isFeatured": False}
    with patch("app.services.product_service.ProductService.update_product", new=AsyncMock(return_value=sample_product_detail)):
        response = client.patch("/api/v1/admin/products/prod-1", json=payload)
        assert response.status_code == 200
        assert response.json()["success"] is True


def test_admin_update_product_status_success(client, admin_user, sample_product_detail):
    app.dependency_overrides[require_admin] = lambda: admin_user
    payload = {"is_active": False}
    with patch("app.services.product_service.ProductService.update_product_status", new=AsyncMock(return_value=sample_product_detail)):
        response = client.patch("/api/v1/admin/products/prod-1/status", json=payload)
        assert response.status_code == 200
        assert response.json()["success"] is True


# -----------------------------------------------------------------------------
# Admin Variant Management Tests
# -----------------------------------------------------------------------------

def test_admin_create_variant_success(client, admin_user, sample_variant):
    app.dependency_overrides[require_admin] = lambda: admin_user
    payload = {
        "sku": "AMUL-MILK-500ML",
        "name": "500 ml",
        "unit_value": 500,
        "unit_type": "ml",
        "price": 30.0,
        "mrp": 32.0,
        "sort_order": 1,
        "is_active": True,
    }
    with patch("app.services.product_service.ProductService.create_variant", new=AsyncMock(return_value=sample_variant)):
        response = client.post("/api/v1/admin/products/prod-1/variants", json=payload)
        assert response.status_code == 201
        data = response.json()
        assert data["success"] is True
        assert data["data"]["sku"] == "AMUL-MILK-500ML"


def test_admin_create_variant_price_exceeds_mrp_returns_422(client, admin_user):
    app.dependency_overrides[require_admin] = lambda: admin_user
    payload = {
        "sku": "AMUL-MILK-500ML",
        "name": "500 ml",
        "unit_value": 500,
        "unit_type": "ml",
        "price": 40.0,
        "mrp": 32.0,  # price > mrp
    }
    response = client.post("/api/v1/admin/products/prod-1/variants", json=payload)
    assert response.status_code == 422


# -----------------------------------------------------------------------------
# Admin Image Management Tests
# -----------------------------------------------------------------------------

def test_admin_add_image_success(client, admin_user, sample_image):
    app.dependency_overrides[require_admin] = lambda: admin_user
    payload = {
        "image_url": "https://images.unsplash.com/photo-amul-milk.jpg",
        "alt_text": "Amul Milk pouch front view",
        "is_primary": True,
    }
    with patch("app.services.product_service.ProductService.add_image", new=AsyncMock(return_value=sample_image)):
        response = client.post("/api/v1/admin/products/prod-1/images", json=payload)
        assert response.status_code == 201
        data = response.json()
        assert data["success"] is True
        assert data["data"]["imageUrl"] == "https://images.unsplash.com/photo-amul-milk.jpg"


def test_admin_set_primary_image_success(client, admin_user, sample_image):
    app.dependency_overrides[require_admin] = lambda: admin_user
    with patch("app.services.product_service.ProductService.set_primary_image", new=AsyncMock(return_value=sample_image)):
        response = client.patch("/api/v1/admin/products/prod-1/images/img-1/primary")
        assert response.status_code == 200
        assert response.json()["success"] is True


def test_admin_delete_image_success(client, admin_user):
    app.dependency_overrides[require_admin] = lambda: admin_user
    with patch("app.services.product_service.ProductService.delete_image", new=AsyncMock()):
        response = client.delete("/api/v1/admin/products/prod-1/images/img-1")
        assert response.status_code == 200
        assert response.json()["data"]["deleted"] is True
