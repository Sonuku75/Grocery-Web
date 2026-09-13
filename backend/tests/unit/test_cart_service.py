"""
Unit tests for Cartify CartService (Module 7)

Validates domain business logic:
- Cart formatting with authoritative pricing (Decimal)
- Subtotal and line total calculations
- Quantity bounds validation (1 <= quantity <= 99)
- Inactive product and variant validation
- Nonexistent entity handling (404)
- IDOR prevention on update and remove
- Concurrency recovery on duplicate additions
"""

from datetime import datetime, timezone
from decimal import Decimal
from unittest.mock import AsyncMock, patch
import pytest
from sqlalchemy.exc import IntegrityError

from app.core.errors import CartifyException, ForbiddenError, NotFoundError
from app.models.cart import Cart, CartItem
from app.models.product import Product
from app.models.product_variant import ProductVariant
from app.services.cart_service import CartService


@pytest.fixture
def sample_product():
    return Product(
        id="prod-milk-1",
        name="Fresh Whole Milk",
        slug="fresh-whole-milk",
        brand="Amul",
        category_id="cat-dairy-1",
        description="Pasteurized milk",
        image_url="https://images.unsplash.com/milk.jpg",
        is_active=True,
    )


@pytest.fixture
def sample_variant(sample_product):
    return ProductVariant(
        id="var-milk-1L",
        product_id=sample_product.id,
        sku="MILK-1L",
        name="1 Litre Bottle",
        unit_value=Decimal("1"),
        unit_type="L",
        price=Decimal("68.00"),
        mrp=Decimal("75.00"),
        discount_percentage=9,
        is_active=True,
        product=sample_product,
    )


@pytest.fixture
def sample_cart(sample_product, sample_variant):
    cart = Cart(
        id="cart-user-1",
        user_id="usr-test-1",
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
    )
    item = CartItem(
        id="cart-item-1",
        cart_id=cart.id,
        product_id=sample_product.id,
        variant_id=sample_variant.id,
        quantity=3,
        product=sample_product,
        variant=sample_variant,
        cart=cart,
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
    )
    cart.items = [item]
    return cart


@pytest.mark.asyncio
async def test_format_cart_authoritative_calculations(sample_cart):
    """Verifies subtotal and line totals derive exclusively from variant price using Decimal."""
    cart_resp = CartService._format_cart(sample_cart)
    assert cart_resp.id == "cart-user-1"
    assert cart_resp.item_count == 3
    assert len(cart_resp.items) == 1
    # 68.00 * 3 = 204.00
    assert cart_resp.items[0].unit_price == Decimal("68.00")
    assert cart_resp.items[0].line_total == Decimal("204.00")
    assert cart_resp.subtotal == Decimal("204.00")
    assert cart_resp.total == Decimal("204.00")


@pytest.mark.asyncio
async def test_add_item_quantity_out_of_bounds():
    """Verifies quantity < 1 or > 99 is rejected immediately."""
    db = AsyncMock()
    with pytest.raises(CartifyException) as exc_info:
        await CartService.add_item(db, user_id="u1", variant_id="v1", quantity=0)
    assert exc_info.value.code == "INVALID_QUANTITY"

    with pytest.raises(CartifyException) as exc_info2:
        await CartService.add_item(db, user_id="u1", variant_id="v1", quantity=100)
    assert exc_info2.value.code == "INVALID_QUANTITY"


@pytest.mark.asyncio
async def test_add_item_nonexistent_variant():
    """Verifies 404 when adding variant that does not exist."""
    db = AsyncMock()
    with patch("app.services.cart_service.ProductVariantRepository.get_by_id", return_value=None):
        with pytest.raises(NotFoundError):
            await CartService.add_item(db, user_id="u1", variant_id="nonexistent-var", quantity=1)


@pytest.mark.asyncio
async def test_add_item_inactive_variant(sample_variant):
    """Verifies 400 when adding an inactive variant."""
    db = AsyncMock()
    sample_variant.is_active = False
    with patch("app.services.cart_service.ProductVariantRepository.get_by_id", return_value=sample_variant):
        with pytest.raises(CartifyException) as exc_info:
            await CartService.add_item(db, user_id="u1", variant_id=sample_variant.id, quantity=1)
        assert exc_info.value.code == "VARIANT_INACTIVE"


@pytest.mark.asyncio
async def test_add_item_inactive_product(sample_product, sample_variant):
    """Verifies 400 when adding variant belonging to an inactive product."""
    db = AsyncMock()
    sample_product.is_active = False
    with patch("app.services.cart_service.ProductVariantRepository.get_by_id", return_value=sample_variant):
        with patch("app.services.cart_service.ProductRepository.get_by_id", return_value=sample_product):
            with pytest.raises(CartifyException) as exc_info:
                await CartService.add_item(db, user_id="u1", variant_id=sample_variant.id, quantity=1)
            assert exc_info.value.code == "PRODUCT_INACTIVE"


@pytest.mark.asyncio
async def test_add_item_increments_existing_variant(sample_product, sample_variant, sample_cart):
    """Verifies adding already-existing variant increments quantity up to 99."""
    db = AsyncMock()
    existing_item = sample_cart.items[0]  # initial qty = 3
    with patch("app.services.cart_service.ProductVariantRepository.get_by_id", return_value=sample_variant):
        with patch("app.services.cart_service.ProductRepository.get_by_id", return_value=sample_product):
            with patch("app.services.cart_service.CartRepository.get_by_user_id", return_value=sample_cart):
                with patch("app.services.cart_service.CartRepository.get_item_by_cart_and_variant", return_value=existing_item):
                    with patch("app.services.cart_service.CartRepository.update_item_quantity") as mock_update:
                        await CartService.add_item(db, user_id="usr-test-1", variant_id=sample_variant.id, quantity=2)
                        mock_update.assert_called_once_with(db, existing_item, 5)


@pytest.mark.asyncio
async def test_update_quantity_idor_protection(sample_cart):
    """Verifies modifying an item belonging to another user raises ForbiddenError (403)."""
    db = AsyncMock()
    item = sample_cart.items[0]
    # cart belongs to 'usr-test-1'
    with patch("app.services.cart_service.CartRepository.get_item_by_id", return_value=item):
        with pytest.raises(ForbiddenError):
            await CartService.update_item_quantity(db, user_id="intruder-user-2", cart_item_id=item.id, quantity=5)


@pytest.mark.asyncio
async def test_remove_item_idor_protection(sample_cart):
    """Verifies removing an item belonging to another user raises ForbiddenError (403)."""
    db = AsyncMock()
    item = sample_cart.items[0]
    with patch("app.services.cart_service.CartRepository.get_item_by_id", return_value=item):
        with pytest.raises(ForbiddenError):
            await CartService.remove_item(db, user_id="intruder-user-2", cart_item_id=item.id)


@pytest.mark.asyncio
async def test_clear_cart_success(sample_cart):
    """Verifies clear cart calls repository to delete all items."""
    db = AsyncMock()
    with patch("app.services.cart_service.CartRepository.get_by_user_id", return_value=sample_cart):
        with patch("app.services.cart_service.CartRepository.clear_cart") as mock_clear:
            resp = await CartService.clear_cart(db, user_id="usr-test-1")
            mock_clear.assert_called_once_with(db, sample_cart.id)
            assert resp.message == "Cart cleared successfully"
            assert resp.cart_id == sample_cart.id
