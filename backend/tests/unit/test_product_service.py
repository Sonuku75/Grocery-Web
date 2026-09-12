"""
Unit tests for Cartify Product Service (Module 4)

Tests:
- Slug generation and collision resolution
- Authoritative discount calculation
- SKU normalization and validation
- Selling price <= MRP validation
- Non-existent category validation
- Single primary image invariant and automatic synchronization
"""

from decimal import Decimal
from unittest.mock import AsyncMock, patch
import pytest

from app.core.errors import CartifyException, NotFoundError
from app.models.category import Category
from app.models.product import Product
from app.models.product_image import ProductImage
from app.models.product_variant import ProductVariant
from app.schemas.product import ProductCreate
from app.schemas.product_image import ProductImageCreate
from app.schemas.product_variant import ProductVariantCreate
from app.services.product_service import (
    ProductService,
    calculate_discount_percentage,
    slugify,
)


def test_slugify_formatting():
    assert slugify("Amul Taaza Milk") == "amul-taaza-milk"
    assert slugify("Fruits & Vegetables") == "fruits-and-vegetables"
    assert slugify("Aashirvaad Superior MP Atta 5kg") == "aashirvaad-superior-mp-atta-5kg"
    assert slugify("  Special   Offer!  ") == "special-offer"
    assert slugify("---Leading-and-Trailing---") == "leading-and-trailing"


def test_calculate_discount_percentage():
    # 290 on 320 MRP -> (30 / 320) * 100 = 9.375% -> 9%
    assert calculate_discount_percentage(Decimal("290.00"), Decimal("320.00")) == 9
    # 425 on 500 MRP -> (75 / 500) * 100 = 15%
    assert calculate_discount_percentage(Decimal("425.00"), Decimal("500.00")) == 15
    # No discount
    assert calculate_discount_percentage(Decimal("100.00"), Decimal("100.00")) == 0
    # Zero MRP edge case
    assert calculate_discount_percentage(Decimal("0.00"), Decimal("0.00")) == 0


def test_variant_sku_uppercase_and_whitespace_strip():
    variant = ProductVariantCreate(
        sku="  amul-milk-500ml  ",
        name="500 ml",
        unit_value=Decimal("500"),
        unit_type="ml",
        price=Decimal("30.00"),
        mrp=Decimal("32.00"),
    )
    assert variant.sku == "AMUL-MILK-500ML"


def test_variant_price_greater_than_mrp_rejected():
    with pytest.raises(ValueError) as exc_info:
        ProductVariantCreate(
            sku="AMUL-MILK-500ML",
            name="500 ml",
            unit_value=Decimal("500"),
            unit_type="ml",
            price=Decimal("35.00"),
            mrp=Decimal("32.00"),
        )
    assert "cannot be greater than MRP" in str(exc_info.value)


@pytest.mark.asyncio
async def test_ensure_unique_slug_no_collision():
    mock_db = AsyncMock()
    with patch("app.repositories.product.ProductRepository.slug_exists", new=AsyncMock(return_value=False)):
        slug = await ProductService.ensure_unique_slug(mock_db, "Amul Taaza Milk")
        assert slug == "amul-taaza-milk"


@pytest.mark.asyncio
async def test_ensure_unique_slug_with_collision():
    mock_db = AsyncMock()
    with patch(
        "app.repositories.product.ProductRepository.slug_exists",
        new=AsyncMock(side_effect=[True, True, False]),
    ):
        slug = await ProductService.ensure_unique_slug(mock_db, "Amul Taaza Milk")
        assert slug == "amul-taaza-milk-3"


@pytest.mark.asyncio
async def test_create_product_invalid_category_raises_400():
    mock_db = AsyncMock()
    with patch("app.repositories.category.CategoryRepository.get_by_id", new=AsyncMock(return_value=None)):
        req = ProductCreate(
            name="Fresh Apples",
            category_id="non-existent-cat",
            brand="FreshFarm",
            description="Crisp red apples",
        )
        with pytest.raises(CartifyException) as exc_info:
            await ProductService.create_product(mock_db, req)
        assert exc_info.value.status_code == 400
        assert exc_info.value.code == "INVALID_CATEGORY"


@pytest.mark.asyncio
async def test_create_variant_duplicate_sku_raises_409():
    mock_db = AsyncMock()
    mock_prod = Product(id="p-1", name="Amul Milk", slug="amul-milk")
    with patch("app.repositories.product.ProductRepository.get_by_id", new=AsyncMock(return_value=mock_prod)), \
         patch("app.repositories.product_variant.ProductVariantRepository.sku_exists", new=AsyncMock(return_value=True)):
        req = ProductVariantCreate(
            sku="AMUL-500ML",
            name="500 ml",
            unit_value=Decimal("500"),
            unit_type="ml",
            price=Decimal("30.00"),
            mrp=Decimal("32.00"),
        )
        with pytest.raises(CartifyException) as exc_info:
            await ProductService.create_variant(mock_db, "p-1", req)
        assert exc_info.value.status_code == 409
        assert exc_info.value.code == "DUPLICATE_SKU"


@pytest.mark.asyncio
async def test_primary_image_logic_atomically_clears_and_syncs():
    mock_db = AsyncMock()
    mock_prod = Product(id="p-1", name="Amul Milk", slug="amul-milk", image_url=None)
    mock_image = ProductImage(
        id="img-1",
        product_id="p-1",
        image_url="https://images.unsplash.com/milk.jpg",
        sort_order=0,
        is_primary=True,
    )

    with patch("app.repositories.product.ProductRepository.get_by_id", new=AsyncMock(return_value=mock_prod)), \
         patch("app.repositories.product.ProductRepository.update", new=AsyncMock()) as mock_prod_update, \
         patch("app.repositories.product_image.ProductImageRepository.clear_primary_for_product", new=AsyncMock()) as mock_clear, \
         patch("app.repositories.product_image.ProductImageRepository.create", new=AsyncMock(return_value=mock_image)):
        
        req = ProductImageCreate(
            image_url="https://images.unsplash.com/milk.jpg",
            is_primary=True,
        )
        res = await ProductService.add_image(mock_db, "p-1", req)
        assert res.is_primary is True
        mock_clear.assert_called_once_with(mock_db, "p-1")
        mock_prod_update.assert_called_once_with(mock_db, mock_prod, {"image_url": "https://images.unsplash.com/milk.jpg"})
