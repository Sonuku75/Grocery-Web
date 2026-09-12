"""
Integration tests for Cartify Category Endpoints (Module 3)
Tests customer category browsing, slug lookup, subcategories, and admin-only mutations.
"""

from datetime import datetime, timezone
from unittest.mock import AsyncMock, patch
import pytest
from fastapi.testclient import TestClient

from app.api.deps import get_current_active_user, require_admin
from app.core.database import get_db_reader, get_db_writer
from app.core.errors import NotFoundError
from app.main import app
from app.models.user import User
from app.schemas.category import CategoryListResponse, CategoryResponse


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


@pytest.fixture
def client(mock_session):
    app.dependency_overrides[get_db_writer] = lambda: mock_session
    app.dependency_overrides[get_db_reader] = lambda: mock_session
    with TestClient(app, base_url="http://testserver") as test_client:
        yield test_client
    app.dependency_overrides.clear()


def test_list_categories_active_only(client):
    fake_items = [
        CategoryResponse(
            id="cat-1",
            name="Fruits & Vegetables",
            slug="fruits-vegetables",
            description="Fresh fruits and greens",
            is_active=True,
            sort_order=1,
            created_at=datetime.now(timezone.utc),
        ),
        CategoryResponse(
            id="cat-2",
            name="Dairy & Breakfast",
            slug="dairy-breakfast",
            description="Milk and eggs",
            is_active=True,
            sort_order=2,
            created_at=datetime.now(timezone.utc),
        ),
    ]
    with patch(
        "app.services.category.CategoryService.list_categories",
        new=AsyncMock(return_value=CategoryListResponse(items=fake_items, total=2)),
    ):
        res = client.get("/api/v1/categories")
        assert res.status_code == 200
        body = res.json()
        assert body["success"] is True
        assert len(body["data"]["items"]) == 2
        assert body["data"]["items"][0]["name"] == "Fruits & Vegetables"


def test_get_category_by_slug_success(client):
    fake_cat = CategoryResponse(
        id="cat-1",
        name="Fruits & Vegetables",
        slug="fruits-vegetables",
        description="Fresh fruits",
        is_active=True,
        sort_order=1,
        subcategories=[
            CategoryResponse(
                id="sub-1",
                name="Fresh Fruits",
                slug="fresh-fruits",
                parent_id="cat-1",
                is_active=True,
                sort_order=1,
            )
        ],
    )
    with patch(
        "app.services.category.CategoryService.get_category_by_slug",
        new=AsyncMock(return_value=fake_cat),
    ):
        res = client.get("/api/v1/categories/slug/fruits-vegetables")
        assert res.status_code == 200
        body = res.json()
        assert body["success"] is True
        assert body["data"]["slug"] == "fruits-vegetables"
        assert len(body["data"]["subcategories"]) == 1


def test_get_category_by_slug_not_found(client):
    with patch(
        "app.services.category.CategoryService.get_category_by_slug",
        side_effect=NotFoundError("Category", "non-existent"),
    ):
        res = client.get("/api/v1/categories/slug/non-existent")
        assert res.status_code == 404
        assert res.json()["success"] is False


def test_get_category_by_id_success(client):
    fake_cat = CategoryResponse(
        id="cat-uuid-1",
        name="Bakery",
        slug="bakery",
        is_active=True,
        sort_order=3,
    )
    with patch(
        "app.services.category.CategoryService.get_category_by_id",
        new=AsyncMock(return_value=fake_cat),
    ):
        res = client.get("/api/v1/categories/cat-uuid-1")
        assert res.status_code == 200
        assert res.json()["data"]["name"] == "Bakery"


def test_list_subcategories_success(client):
    fake_subs = [
        CategoryResponse(
            id="sub-1",
            name="Milk",
            slug="milk",
            parent_id="cat-dairy",
            is_active=True,
            sort_order=1,
        ),
        CategoryResponse(
            id="sub-2",
            name="Cheese",
            slug="cheese",
            parent_id="cat-dairy",
            is_active=True,
            sort_order=2,
        ),
    ]
    with patch(
        "app.services.category.CategoryService.list_subcategories",
        new=AsyncMock(return_value=CategoryListResponse(items=fake_subs, total=2)),
    ):
        res = client.get("/api/v1/categories/cat-dairy/subcategories")
        assert res.status_code == 200
        assert len(res.json()["data"]["items"]) == 2


def test_admin_create_category_success(client, admin_user):
    app.dependency_overrides[require_admin] = lambda: admin_user
    fake_cat = CategoryResponse(
        id="cat-new-1",
        name="Snacks & Munchies",
        slug="snacks-munchies",
        description="Chips and dips",
        is_active=True,
        sort_order=5,
    )
    with patch(
        "app.services.category.CategoryService.create_category",
        new=AsyncMock(return_value=fake_cat),
    ):
        res = client.post(
            "/api/v1/admin/categories",
            json={
                "name": "Snacks & Munchies",
                "description": "Chips and dips",
                "sort_order": 5,
            },
        )
        assert res.status_code == 201
        assert res.json()["data"]["name"] == "Snacks & Munchies"


def test_customer_cannot_create_category(client, customer_user):
    app.dependency_overrides[get_current_active_user] = lambda: customer_user
    # Customer will be rejected by require_admin dependency (403)
    res = client.post(
        "/api/v1/admin/categories",
        json={"name": "Hacked Category"},
    )
    assert res.status_code == 403


def test_unauthenticated_cannot_create_category(client):
    res = client.post(
        "/api/v1/admin/categories",
        json={"name": "Hacked Category"},
    )
    assert res.status_code == 401


def test_admin_update_category_success(client, admin_user):
    app.dependency_overrides[require_admin] = lambda: admin_user
    fake_cat = CategoryResponse(
        id="cat-1",
        name="Updated Name",
        slug="updated-name",
        is_active=True,
        sort_order=1,
    )
    with patch(
        "app.services.category.CategoryService.update_category",
        new=AsyncMock(return_value=fake_cat),
    ):
        res = client.patch(
            "/api/v1/admin/categories/cat-1",
            json={"name": "Updated Name"},
        )
        assert res.status_code == 200
        assert res.json()["data"]["name"] == "Updated Name"


def test_customer_cannot_update_category(client, customer_user):
    app.dependency_overrides[get_current_active_user] = lambda: customer_user
    res = client.patch(
        "/api/v1/admin/categories/cat-1",
        json={"name": "Updated Name"},
    )
    assert res.status_code == 403


def test_admin_delete_category_soft(client, admin_user):
    app.dependency_overrides[require_admin] = lambda: admin_user
    with patch(
        "app.services.category.CategoryService.delete_category",
        new=AsyncMock(return_value={"message": "Category and its subcategories deactivated successfully."}),
    ):
        res = client.delete("/api/v1/admin/categories/cat-1")
        assert res.status_code == 200
        assert "deactivated successfully" in res.json()["data"]["message"]


def test_customer_cannot_delete_category(client, customer_user):
    app.dependency_overrides[get_current_active_user] = lambda: customer_user
    res = client.delete("/api/v1/admin/categories/cat-1")
    assert res.status_code == 403
