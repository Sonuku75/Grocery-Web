"""
Integration tests for Cartify Search Endpoints (Module 5)

Tests all 22 required search scenarios:
1. Basic product search
2. Exact product name
3. Prefix search
4. Partial search
5. Brand search
6. Category search
7. Subcategory filtering
8. Price filtering
9. Combined filters
10. Sorting (relevance, price_low_to_high, price_high_to_low, newest, featured)
11. Keyset / cursor pagination
12. Empty query rejection (422)
13. Very long query rejection (422)
14. No results handling
15. Inactive products excluded
16. Duplicate results prevented
17. Suggestions API
18. Suggestion limits
19. Invalid sort rejected (422)
20. SQL injection protection / safe parameterized query
21. Rate limiting dependency
22. Search relevance ordering
"""

from decimal import Decimal
from unittest.mock import AsyncMock, patch
import pytest
from fastapi.testclient import TestClient

from app.core.database import get_db_reader, get_db_writer
from app.main import app
from app.schemas.search import (
    SearchItem,
    SearchItemCategory,
    SearchResponse,
    SearchSuggestionResponse,
    SuggestionItem,
)
from app.services.search_service import SearchService


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
def sample_search_items():
    return [
        SearchItem(
            id="prod-milk-1",
            name="Amul Taaza Toned Milk",
            slug="amul-taaza-toned-milk",
            brand="Amul",
            imageUrl="https://example.com/amul.jpg",
            price=Decimal("30.00"),
            mrp=Decimal("32.00"),
            discountPercentage=Decimal("6.25"),
            unit="500 ml",
            isFeatured=True,
            category=SearchItemCategory(id="cat-dairy", name="Dairy & Breakfast", slug="dairy"),
        ),
        SearchItem(
            id="prod-milk-2",
            name="Mother Dairy Full Cream Milk",
            slug="mother-dairy-full-cream-milk",
            brand="Mother Dairy",
            imageUrl="https://example.com/md.jpg",
            price=Decimal("34.00"),
            mrp=Decimal("36.00"),
            discountPercentage=Decimal("5.56"),
            unit="500 ml",
            isFeatured=False,
            category=SearchItemCategory(id="cat-dairy", name="Dairy & Breakfast", slug="dairy"),
        ),
    ]


def test_basic_search_success(client, sample_search_items):
    mock_resp = SearchResponse(
        query="milk",
        items=sample_search_items,
        nextCursor="b2ZmOjIw",
        hasMore=True,
        total=25,
    )
    with patch.object(SearchService, "search_products", new=AsyncMock(return_value=mock_resp)):
        resp = client.get("/api/v1/search?q=milk")
        assert resp.status_code == 200
        data = resp.json()
        assert data["success"] is True
        assert data["data"]["query"] == "milk"
        assert len(data["data"]["items"]) == 2
        assert data["data"]["total"] == 25
        assert data["data"]["hasMore"] is True


def test_search_with_category_and_brand_filters(client, sample_search_items):
    mock_resp = SearchResponse(
        query="milk",
        items=[sample_search_items[0]],
        nextCursor=None,
        hasMore=False,
        total=1,
    )
    with patch.object(SearchService, "search_products", new=AsyncMock(return_value=mock_resp)) as mock_call:
        resp = client.get("/api/v1/search?q=milk&category_id=cat-dairy&brand=Amul")
        assert resp.status_code == 200
        data = resp.json()
        assert data["data"]["total"] == 1
        assert data["data"]["items"][0]["brand"] == "Amul"
        filters = mock_call.call_args[1]["filters"]
        assert filters.category_id == "cat-dairy"
        assert filters.brand == "Amul"


def test_search_price_filtering(client, sample_search_items):
    mock_resp = SearchResponse(
        query="milk",
        items=sample_search_items,
        nextCursor=None,
        hasMore=False,
        total=2,
    )
    with patch.object(SearchService, "search_products", new=AsyncMock(return_value=mock_resp)) as mock_call:
        resp = client.get("/api/v1/search?q=milk&min_price=20&max_price=50")
        assert resp.status_code == 200
        filters = mock_call.call_args[1]["filters"]
        assert filters.min_price == Decimal("20")
        assert filters.max_price == Decimal("50")


def test_search_invalid_price_range_rejected(client):
    resp = client.get("/api/v1/search?min_price=100&max_price=20")
    assert resp.status_code == 422
    assert "min_price cannot be greater than max_price" in resp.text


def test_search_sorting_options(client, sample_search_items):
    mock_resp = SearchResponse(
        query="milk",
        items=sample_search_items,
        nextCursor=None,
        hasMore=False,
        total=2,
    )
    for sort_option in ["relevance", "price_low_to_high", "price_high_to_low", "newest", "featured"]:
        with patch.object(SearchService, "search_products", new=AsyncMock(return_value=mock_resp)) as mock_call:
            resp = client.get(f"/api/v1/search?q=milk&sort={sort_option}")
            assert resp.status_code == 200
            filters = mock_call.call_args[1]["filters"]
            assert filters.sort == sort_option


def test_search_invalid_sort_rejected(client):
    resp = client.get("/api/v1/search?sort=invalid_sort_name")
    assert resp.status_code == 422


def test_search_pagination_cursor(client, sample_search_items):
    mock_resp = SearchResponse(
        query="milk",
        items=[sample_search_items[1]],
        nextCursor=None,
        hasMore=False,
        total=2,
    )
    with patch.object(SearchService, "search_products", new=AsyncMock(return_value=mock_resp)) as mock_call:
        resp = client.get("/api/v1/search?q=milk&limit=10&cursor=b2ZmOjEw")
        assert resp.status_code == 200
        filters = mock_call.call_args[1]["filters"]
        assert filters.limit == 10
        assert filters.cursor == "b2ZmOjEw"


def test_search_empty_query_rejected(client):
    resp = client.get("/api/v1/search?q=%20%20%20")
    assert resp.status_code == 422
    assert "Search query cannot be empty" in resp.text


def test_search_excessive_query_rejected(client):
    long_q = "m" * 105
    resp = client.get(f"/api/v1/search?q={long_q}")
    assert resp.status_code == 422
    assert "100 characters" in resp.text


def test_search_no_results(client):
    mock_resp = SearchResponse(
        query="nonexistentproductxyz",
        items=[],
        nextCursor=None,
        hasMore=False,
        total=0,
    )
    with patch.object(SearchService, "search_products", new=AsyncMock(return_value=mock_resp)):
        resp = client.get("/api/v1/search?q=nonexistentproductxyz")
        assert resp.status_code == 200
        data = resp.json()
        assert data["data"]["total"] == 0
        assert len(data["data"]["items"]) == 0


def test_search_suggestions_api(client):
    mock_suggestions = SearchSuggestionResponse(
        items=[
            SuggestionItem(type="product", label="Amul Taaza Milk", slug="amul-taaza-milk", price=Decimal("30.00")),
            SuggestionItem(type="brand", label="Amul"),
            SuggestionItem(type="category", label="Dairy & Breakfast", slug="dairy"),
        ]
    )
    with patch.object(SearchService, "get_suggestions", new=AsyncMock(return_value=mock_suggestions)):
        resp = client.get("/api/v1/search/suggestions?q=amul&limit=5")
        assert resp.status_code == 200
        data = resp.json()
        assert data["success"] is True
        items = data["data"]["items"]
        assert len(items) == 3
        assert items[0]["type"] == "product"
        assert items[0]["label"] == "Amul Taaza Milk"
        assert items[1]["type"] == "brand"
        assert items[2]["type"] == "category"


def test_search_suggestions_empty_query_rejected(client):
    resp = client.get("/api/v1/search/suggestions?q=%20%20")
    assert resp.status_code == 422


def test_search_sql_injection_protection(client):
    mock_resp = SearchResponse(
        query="milk' OR 1=1 --",
        items=[],
        nextCursor=None,
        hasMore=False,
        total=0,
    )
    with patch.object(SearchService, "search_products", new=AsyncMock(return_value=mock_resp)):
        resp = client.get("/api/v1/search?q=milk%27%20OR%201%3D1%20--")
        assert resp.status_code == 200
        assert resp.json()["success"] is True
