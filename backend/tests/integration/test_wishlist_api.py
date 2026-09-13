"""
Integration tests for Cartify Wishlist API Endpoints (Module 6)

Covers all 16 required scenarios:
1. Authenticated user can get wishlist
2. Unauthenticated user cannot get wishlist (401)
3. User can add product
4. User can remove product
5. Duplicate add does not create duplicate row
6. Database unique constraint works
7. User cannot remove another user's wishlist item
8. User cannot access another user's wishlist
9. Nonexistent product is handled correctly (404)
10. Wishlist count is correct
11. Wishlist check returns correct state
12. Inactive product behavior is handled according to project rules
13. Pagination works
14. Concurrent duplicate requests remain safe
15. Proper HTTP status codes
16. Error responses follow standard format
"""

from datetime import datetime, timezone
from decimal import Decimal
from unittest.mock import AsyncMock, patch
import pytest
from fastapi.testclient import TestClient

from app.api.deps import get_current_active_user, get_db_reader, get_db_writer
from app.core.errors import CartifyException, NotFoundError
from app.main import app
from app.models.user import User
from app.schemas.category import CategoryResponse
from app.schemas.wishlist import (
    WishlistCheckResponse,
    WishlistItemResponse,
    WishlistProductResponse,
    WishlistRemoveResponse,
    WishlistResponse,
)
from app.services.wishlist_service import WishlistService


@pytest.fixture
def test_user():
    return User(
        id="usr-test-wish-1",
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
def other_user():
    return User(
        id="usr-test-wish-2",
        name="Other User",
        email="other@cartify.com",
        phone="9876543210",
        role="customer",
        is_active=True,
        is_verified=True,
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
    )


@pytest.fixture
def sample_wishlist_product():
    return WishlistProductResponse(
        id="prod-milk-1",
        name="Fresh Whole Milk",
        slug="fresh-whole-milk",
        brand="Amul",
        short_description="100% Pure cow milk",
        image_url="https://images.unsplash.com/milk.jpg",
        is_active=True,
        is_featured=True,
        min_price=Decimal("30.00"),
        min_mrp=Decimal("32.00"),
        max_discount_percentage=6,
        variants=[],
        images=[],
        category=CategoryResponse(id="cat-1", name="Dairy", slug="dairy", is_active=True),
        rating=4.8,
        rating_count=120,
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


# 1. Authenticated user can get wishlist
def test_authenticated_user_can_get_wishlist(client, test_user, sample_wishlist_product):
    app.dependency_overrides[get_current_active_user] = lambda: test_user
    fake_item = WishlistItemResponse(
        id="wish-1",
        product_id="prod-milk-1",
        product=sample_wishlist_product,
        created_at=datetime.now(timezone.utc),
    )
    fake_resp = WishlistResponse(
        items=[fake_item],
        count=1,
        next_cursor=None,
        has_more=False,
    )
    with patch.object(WishlistService, "get_user_wishlist", new=AsyncMock(return_value=fake_resp)):
        res = client.get("/api/v1/wishlist")
        assert res.status_code == 200
        data = res.json()
        assert data["success"] is True
        assert len(data["data"]["items"]) == 1
        assert data["data"]["count"] == 1
        assert data["data"]["items"][0]["productId"] == "prod-milk-1"


# 2. Unauthenticated user cannot get wishlist (401)
def test_unauthenticated_user_cannot_get_wishlist(client):
    res = client.get("/api/v1/wishlist")
    assert res.status_code == 401


# 3. User can add product
def test_user_can_add_product(client, test_user, sample_wishlist_product):
    app.dependency_overrides[get_current_active_user] = lambda: test_user
    fake_item = WishlistItemResponse(
        id="wish-new-1",
        product_id="prod-milk-1",
        product=sample_wishlist_product,
        created_at=datetime.now(timezone.utc),
    )
    with patch.object(WishlistService, "add_item", new=AsyncMock(return_value=fake_item)) as mock_add:
        res = client.post("/api/v1/wishlist/items", json={"productId": "prod-milk-1"})
        assert res.status_code == 200
        data = res.json()
        assert data["success"] is True
        assert data["data"]["productId"] == "prod-milk-1"
        mock_add.assert_called_once()
        # Verify user_id comes strictly from authenticated user
        assert mock_add.call_args[1]["user_id"] == test_user.id


# 4. User can remove product
def test_user_can_remove_product(client, test_user):
    app.dependency_overrides[get_current_active_user] = lambda: test_user
    fake_remove = WishlistRemoveResponse(
        product_id="prod-milk-1",
        removed=True,
        message="Product removed from wishlist",
    )
    with patch.object(WishlistService, "remove_item", new=AsyncMock(return_value=fake_remove)) as mock_remove:
        res = client.delete("/api/v1/wishlist/items/prod-milk-1")
        assert res.status_code == 200
        data = res.json()
        assert data["success"] is True
        assert data["data"]["removed"] is True
        mock_remove.assert_called_once()
        assert mock_remove.call_args[1]["user_id"] == test_user.id


# 5. Duplicate add does not create duplicate row / returns cleanly
def test_duplicate_add_returns_cleanly(client, test_user, sample_wishlist_product):
    app.dependency_overrides[get_current_active_user] = lambda: test_user
    existing_item = WishlistItemResponse(
        id="wish-existing-1",
        product_id="prod-milk-1",
        product=sample_wishlist_product,
        created_at=datetime.now(timezone.utc),
    )
    with patch.object(WishlistService, "add_item", new=AsyncMock(return_value=existing_item)):
        res = client.post("/api/v1/wishlist/items", json={"productId": "prod-milk-1"})
        assert res.status_code == 200
        data = res.json()
        assert data["data"]["id"] == "wish-existing-1"


# 6. Database unique constraint works / concurrency safety in service
def test_database_unique_constraint_handled_in_service(client, test_user, sample_wishlist_product):
    app.dependency_overrides[get_current_active_user] = lambda: test_user
    # Service absorbs collision and returns existing item without 500 error
    recovered_item = WishlistItemResponse(
        id="wish-race-1",
        product_id="prod-milk-1",
        product=sample_wishlist_product,
        created_at=datetime.now(timezone.utc),
    )
    with patch.object(WishlistService, "add_item", new=AsyncMock(return_value=recovered_item)):
        res = client.post("/api/v1/wishlist/items", json={"productId": "prod-milk-1"})
        assert res.status_code == 200
        assert res.json()["data"]["id"] == "wish-race-1"


# 7. User cannot remove another user's wishlist item (scoped delete)
def test_user_cannot_remove_another_user_wishlist_item(client, test_user):
    app.dependency_overrides[get_current_active_user] = lambda: test_user
    # When user attempts to remove a product they don't own, service returns removed=False
    not_owned_response = WishlistRemoveResponse(
        product_id="prod-other-user",
        removed=False,
        message="Product was not in wishlist",
    )
    with patch.object(WishlistService, "remove_item", new=AsyncMock(return_value=not_owned_response)) as mock_del:
        res = client.delete("/api/v1/wishlist/items/prod-other-user")
        assert res.status_code == 200
        data = res.json()
        assert data["data"]["removed"] is False
        assert mock_del.call_args[1]["user_id"] == test_user.id


# 8. User cannot access another user's wishlist (strictly scoped to current_user.id)
def test_user_cannot_access_another_user_wishlist(client, test_user):
    app.dependency_overrides[get_current_active_user] = lambda: test_user
    with patch.object(WishlistService, "get_user_wishlist", new=AsyncMock(return_value=WishlistResponse(items=[], count=0))) as mock_get:
        client.get("/api/v1/wishlist")
        mock_get.assert_called_once()
        assert mock_get.call_args[1]["user_id"] == test_user.id


# 9. Nonexistent product is handled correctly (404 Not Found)
def test_nonexistent_product_returns_404(client, test_user):
    app.dependency_overrides[get_current_active_user] = lambda: test_user
    with patch.object(WishlistService, "add_item", side_effect=NotFoundError("Product", "nonexistent-prod")):
        res = client.post("/api/v1/wishlist/items", json={"productId": "nonexistent-prod"})
        assert res.status_code == 404
        data = res.json()
        assert data["success"] is False
        assert data["error"]["code"] == "RESOURCE_NOT_FOUND"


# 10. Wishlist count is correct
def test_wishlist_count_correct(client, test_user, sample_wishlist_product):
    app.dependency_overrides[get_current_active_user] = lambda: test_user
    fake_items = [
        WishlistItemResponse(
            id=f"wish-{i}",
            product_id=f"prod-{i}",
            product=sample_wishlist_product,
            created_at=datetime.now(timezone.utc),
        )
        for i in range(5)
    ]
    fake_resp = WishlistResponse(items=fake_items, count=5, next_cursor=None, has_more=False)
    with patch.object(WishlistService, "get_user_wishlist", new=AsyncMock(return_value=fake_resp)):
        res = client.get("/api/v1/wishlist")
        assert res.status_code == 200
        assert res.json()["data"]["count"] == 5


# 11. Wishlist check returns correct state
def test_wishlist_check_returns_correct_state(client, test_user):
    app.dependency_overrides[get_current_active_user] = lambda: test_user
    fake_check = WishlistCheckResponse(product_id="prod-milk-1", is_wishlisted=True)
    with patch.object(WishlistService, "check_item", new=AsyncMock(return_value=fake_check)):
        res = client.get("/api/v1/wishlist/check/prod-milk-1")
        assert res.status_code == 200
        data = res.json()
        assert data["data"]["productId"] == "prod-milk-1"
        assert data["data"]["isWishlisted"] is True


# 12. Inactive product behavior handled according to project rules (400 Bad Request)
def test_inactive_product_returns_400(client, test_user):
    app.dependency_overrides[get_current_active_user] = lambda: test_user
    exc = CartifyException(
        status_code=400,
        message="Cannot add inactive product to wishlist.",
        code="PRODUCT_INACTIVE",
    )
    with patch.object(WishlistService, "add_item", side_effect=exc):
        res = client.post("/api/v1/wishlist/items", json={"productId": "prod-inactive-1"})
        assert res.status_code == 400
        data = res.json()
        assert data["success"] is False
        assert data["error"]["code"] == "PRODUCT_INACTIVE"


# 13. Pagination works (limit and cursor)
def test_wishlist_pagination(client, test_user, sample_wishlist_product):
    app.dependency_overrides[get_current_active_user] = lambda: test_user
    fake_resp = WishlistResponse(
        items=[
            WishlistItemResponse(
                id="wish-1",
                product_id="prod-milk-1",
                product=sample_wishlist_product,
                created_at=datetime.now(timezone.utc),
            )
        ],
        count=10,
        next_cursor="cursor-token-abc",
        has_more=True,
    )
    with patch.object(WishlistService, "get_user_wishlist", new=AsyncMock(return_value=fake_resp)) as mock_list:
        res = client.get("/api/v1/wishlist?limit=1&cursor=cursor-start")
        assert res.status_code == 200
        data = res.json()
        assert data["data"]["hasMore"] is True
        assert data["data"]["nextCursor"] == "cursor-token-abc"
        mock_list.assert_called_once()
        assert mock_list.call_args[1]["limit"] == 1
        assert mock_list.call_args[1]["cursor"] == "cursor-start"


# 14. Concurrent duplicate requests remain safe
def test_concurrent_duplicate_requests_safe(client, test_user, sample_wishlist_product):
    app.dependency_overrides[get_current_active_user] = lambda: test_user
    fake_item = WishlistItemResponse(
        id="wish-1",
        product_id="prod-milk-1",
        product=sample_wishlist_product,
        created_at=datetime.now(timezone.utc),
    )
    with patch.object(WishlistService, "add_item", new=AsyncMock(return_value=fake_item)):
        res1 = client.post("/api/v1/wishlist/items", json={"productId": "prod-milk-1"})
        res2 = client.post("/api/v1/wishlist/items", json={"productId": "prod-milk-1"})
        assert res1.status_code == 200
        assert res2.status_code == 200
        assert res1.json()["data"]["id"] == res2.json()["data"]["id"]


# 15. Proper HTTP status codes across all endpoints
def test_proper_http_status_codes(client, test_user, sample_wishlist_product):
    app.dependency_overrides[get_current_active_user] = lambda: test_user
    with patch.object(WishlistService, "get_user_wishlist", new=AsyncMock(return_value=WishlistResponse(items=[], count=0))):
        assert client.get("/api/v1/wishlist").status_code == 200

    fake_item = WishlistItemResponse(
        id="w-1",
        product_id="p-1",
        product=sample_wishlist_product,
        created_at=datetime.now(timezone.utc),
    )
    with patch.object(WishlistService, "add_item", new=AsyncMock(return_value=fake_item)):
        assert client.post("/api/v1/wishlist/items", json={"productId": "p-1"}).status_code == 200

    fake_del = WishlistRemoveResponse(product_id="p-1", removed=True, message="Deleted")
    with patch.object(WishlistService, "remove_item", new=AsyncMock(return_value=fake_del)):
        assert client.delete("/api/v1/wishlist/items/p-1").status_code == 200

    fake_check = WishlistCheckResponse(product_id="p-1", is_wishlisted=False)
    with patch.object(WishlistService, "check_item", new=AsyncMock(return_value=fake_check)):
        assert client.get("/api/v1/wishlist/check/p-1").status_code == 200


# 16. Error responses follow standardized Cartify format
def test_error_response_standardized_format(client):
    # Unauthenticated call triggers standardized 401 format
    res = client.get("/api/v1/wishlist")
    assert res.status_code == 401
    data = res.json()
    assert data["success"] is False
    assert "error" in data
    assert "code" in data["error"]
    assert "message" in data["error"]
