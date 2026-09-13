"""
Unit tests for Cartify WishlistService (Module 6)

Validates domain business logic:
- Cursor encoding & decoding
- Product summary formatting with pricing aggregates
- Nonexistent product validation
- Inactive product validation
- Concurrency & IntegrityError collision recovery
- Scoped deletion and boolean status check
"""

from datetime import datetime, timezone
from decimal import Decimal
from unittest.mock import AsyncMock, patch
import pytest
from sqlalchemy.exc import IntegrityError

from app.core.errors import CartifyException, NotFoundError
from app.models.category import Category
from app.models.product import Product
from app.models.product_image import ProductImage
from app.models.product_variant import ProductVariant
from app.models.wishlist import WishlistItem
from app.repositories.wishlist import decode_cursor, encode_cursor
from app.services.wishlist_service import WishlistService


@pytest.fixture
def sample_category():
    return Category(
        id="cat-dairy-1",
        name="Dairy & Eggs",
        slug="dairy-and-eggs",
        is_active=True,
    )


@pytest.fixture
def sample_product(sample_category):
    prod = Product(
        id="prod-milk-1",
        name="Fresh Whole Milk",
        slug="fresh-whole-milk",
        brand="Amul",
        category_id=sample_category.id,
        category=sample_category,
        description="Fresh pasture-raised whole milk",
        short_description="100% Pure cow milk",
        image_url="https://images.unsplash.com/milk.jpg",
        is_active=True,
        is_featured=True,
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
    )
    v1 = ProductVariant(
        id="var-1",
        product_id=prod.id,
        sku="MILK-500ML",
        name="500ml Pouch",
        unit_value=Decimal("500"),
        unit_type="ml",
        price=Decimal("30.00"),
        mrp=Decimal("32.00"),
        discount_percentage=6,
        is_active=True,
        sort_order=1,
    )
    v2 = ProductVariant(
        id="var-2",
        product_id=prod.id,
        sku="MILK-1L",
        name="1L Bottle",
        unit_value=Decimal("1"),
        unit_type="litre",
        price=Decimal("58.00"),
        mrp=Decimal("65.00"),
        discount_percentage=10,
        is_active=True,
        sort_order=2,
    )
    img = ProductImage(
        id="img-1",
        product_id=prod.id,
        image_url="https://images.unsplash.com/milk.jpg",
        alt_text="Fresh milk bottle",
        is_primary=True,
        sort_order=1,
    )
    prod.variants = [v1, v2]
    prod.images = [img]
    return prod


def test_cursor_encode_decode():
    now = datetime(2026, 9, 13, 12, 0, 0, tzinfo=timezone.utc)
    item_id = "wish-item-12345"
    encoded = encode_cursor(now, item_id)
    assert isinstance(encoded, str)
    assert len(encoded) > 0

    decoded = decode_cursor(encoded)
    assert decoded is not None
    assert decoded[0] == now
    assert decoded[1] == item_id


def test_decode_invalid_cursor():
    assert decode_cursor("invalid-base64!!!") is None
    assert decode_cursor("") is None


def test_format_wishlist_product(sample_product):
    formatted = WishlistService._format_wishlist_product(sample_product)
    assert formatted.id == "prod-milk-1"
    assert formatted.name == "Fresh Whole Milk"
    assert formatted.brand == "Amul"
    assert formatted.min_price == Decimal("30.00")
    assert formatted.max_discount_percentage == 10
    assert len(formatted.variants) == 2
    assert formatted.primary_variant is not None
    assert formatted.primary_variant.sku == "MILK-500ML"


def test_format_wishlist_item(sample_product):
    now = datetime.now(timezone.utc)
    item = WishlistItem(
        id="item-uuid-1",
        user_id="user-123",
        product_id=sample_product.id,
        created_at=now,
    )
    item.product = sample_product
    res = WishlistService._format_wishlist_item(item)
    assert res.id == "item-uuid-1"
    assert res.product_id == "prod-milk-1"
    assert res.product.name == "Fresh Whole Milk"
    assert res.created_at == now


@pytest.mark.asyncio
async def test_add_nonexistent_product_raises_not_found():
    db = AsyncMock()
    with patch("app.services.wishlist_service.ProductRepository.get_by_id", new=AsyncMock(return_value=None)):
        with pytest.raises(NotFoundError) as exc_info:
            await WishlistService.add_item(db, user_id="u1", product_id="missing-id")
        assert "missing-id" in str(exc_info.value.message)


@pytest.mark.asyncio
async def test_add_inactive_product_raises_bad_request(sample_product):
    db = AsyncMock()
    sample_product.is_active = False
    with patch("app.services.wishlist_service.ProductRepository.get_by_id", new=AsyncMock(return_value=sample_product)):
        with pytest.raises(CartifyException) as exc_info:
            await WishlistService.add_item(db, user_id="u1", product_id=sample_product.id)
        assert exc_info.value.status_code == 400
        assert exc_info.value.code == "PRODUCT_INACTIVE"


@pytest.mark.asyncio
async def test_add_existing_product_returns_cleanly(sample_product):
    db = AsyncMock()
    existing_item = WishlistItem(
        id="item-1",
        user_id="u1",
        product_id=sample_product.id,
        created_at=datetime.now(timezone.utc),
    )
    existing_item.product = sample_product

    with patch("app.services.wishlist_service.ProductRepository.get_by_id", new=AsyncMock(return_value=sample_product)), \
         patch("app.services.wishlist_service.WishlistRepository.get_by_user_and_product", new=AsyncMock(return_value=existing_item)), \
         patch("app.services.wishlist_service.WishlistRepository.create", new=AsyncMock()) as mock_create:
        res = await WishlistService.add_item(db, user_id="u1", product_id=sample_product.id)
        assert res.id == "item-1"
        # create was not called because item already existed
        mock_create.assert_not_called()


@pytest.mark.asyncio
async def test_add_product_integrity_error_recovery(sample_product):
    """Simulates race condition where another request inserts item concurrently."""
    db = AsyncMock()
    existing_item = WishlistItem(
        id="item-race-1",
        user_id="u1",
        product_id=sample_product.id,
        created_at=datetime.now(timezone.utc),
    )
    existing_item.product = sample_product

    with patch("app.services.wishlist_service.ProductRepository.get_by_id", new=AsyncMock(return_value=sample_product)), \
         patch("app.services.wishlist_service.WishlistRepository.get_by_user_and_product", side_effect=[None, existing_item]), \
         patch("app.services.wishlist_service.WishlistRepository.create", side_effect=IntegrityError("duplicate", None, None)):
        res = await WishlistService.add_item(db, user_id="u1", product_id=sample_product.id)
        assert res.id == "item-race-1"
        db.rollback.assert_called_once()


@pytest.mark.asyncio
async def test_remove_item(sample_product):
    db = AsyncMock()
    with patch("app.services.wishlist_service.WishlistRepository.delete", new=AsyncMock(return_value=True)):
        res = await WishlistService.remove_item(db, user_id="u1", product_id=sample_product.id)
        assert res.product_id == sample_product.id
        assert res.removed is True
        db.commit.assert_called_once()


@pytest.mark.asyncio
async def test_check_item():
    db = AsyncMock()
    with patch("app.services.wishlist_service.WishlistRepository.is_wishlisted", new=AsyncMock(return_value=True)):
        res = await WishlistService.check_item(db, user_id="u1", product_id="prod-1")
        assert res.product_id == "prod-1"
        assert res.is_wishlisted is True
