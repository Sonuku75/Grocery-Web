"""
Unit tests for Cartify Search Schemas & Service Logic (Module 5)
"""

from decimal import Decimal
import pytest
from pydantic import ValidationError

from app.models.category import Category
from app.models.product import Product
from app.models.product_image import ProductImage
from app.models.product_variant import ProductVariant
from app.repositories.search import decode_cursor, encode_cursor
from app.schemas.search import (
    SearchFilterParams,
    SearchSuggestionParams,
)
from app.services.search_service import SearchService


def test_search_filter_params_valid():
    params = SearchFilterParams(
        q="  organic milk  ",
        brand="Amul",
        min_price=Decimal("20"),
        max_price=Decimal("100"),
        sort="price_low_to_high",
        limit=15,
    )
    assert params.q == "organic milk"
    assert params.brand == "Amul"
    assert params.min_price == Decimal("20")
    assert params.max_price == Decimal("100")
    assert params.sort == "price_low_to_high"
    assert params.limit == 15


def test_search_filter_params_empty_query_rejected():
    with pytest.raises(ValidationError) as exc:
        SearchFilterParams(q="   ")
    assert "Search query cannot be empty" in str(exc.value)


def test_search_filter_params_excessive_length_rejected():
    long_query = "a" * 101
    with pytest.raises(ValidationError) as exc:
        SearchFilterParams(q=long_query)
    assert "cannot exceed 100 characters" in str(exc.value)


def test_search_filter_params_invalid_price_range():
    with pytest.raises(ValidationError) as exc:
        SearchFilterParams(min_price=Decimal("100"), max_price=Decimal("50"))
    assert "min_price cannot be greater than max_price" in str(exc.value)


def test_search_filter_params_invalid_sort():
    with pytest.raises(ValidationError):
        SearchFilterParams(sort="unsupported_sql_sort; DROP TABLE products;")


def test_search_suggestion_params_validation():
    # Valid
    p = SearchSuggestionParams(q="  fresh  ", limit=5)
    assert p.q == "fresh"
    assert p.limit == 5

    # Empty
    with pytest.raises(ValidationError) as exc:
        SearchSuggestionParams(q="   ")
    assert "cannot be empty" in str(exc.value)

    # Exceed limit
    with pytest.raises(ValidationError):
        SearchSuggestionParams(q="fresh", limit=25)


def test_cursor_encoding_and_decoding():
    cursor = encode_cursor(40)
    assert isinstance(cursor, str)
    decoded = decode_cursor(cursor)
    assert decoded == 40

    # Invalid cursor returns None
    assert decode_cursor("invalid-base64-garbage!!") is None


def test_format_search_item_with_variants():
    cat = Category(id="cat-1", name="Dairy", slug="dairy")
    prod = Product(
        id="prod-1",
        name="Amul Taaza",
        slug="amul-taaza",
        brand="Amul",
        category=cat,
        image_url="https://example.com/amul.jpg",
        is_featured=True,
    )
    v1 = ProductVariant(
        id="v-1",
        product_id="prod-1",
        sku="AMUL-500",
        name="500 ml",
        unit_value=Decimal("500"),
        unit_type="ml",
        price=Decimal("30.00"),
        mrp=Decimal("32.00"),
        discount_percentage=Decimal("6.25"),
        is_active=True,
        sort_order=0,
    )
    v2 = ProductVariant(
        id="v-2",
        product_id="prod-1",
        sku="AMUL-1000",
        name="1 L",
        unit_value=Decimal("1"),
        unit_type="L",
        price=Decimal("58.00"),
        mrp=Decimal("64.00"),
        discount_percentage=Decimal("9.38"),
        is_active=True,
        sort_order=1,
    )
    prod.variants = [v1, v2]
    img = ProductImage(
        id="img-1",
        product_id="prod-1",
        image_url="https://example.com/primary.jpg",
        is_primary=True,
        sort_order=0,
    )
    prod.images = [img]

    item = SearchService._format_search_item(prod)
    assert item.id == "prod-1"
    assert item.name == "Amul Taaza"
    assert item.price == Decimal("30.00")
    assert item.mrp == Decimal("32.00")
    assert item.discount_percentage == Decimal("6.25")
    assert item.unit == "500 ml"
    assert item.image_url == "https://example.com/primary.jpg"
    assert item.category is not None
    assert item.category.name == "Dairy"
