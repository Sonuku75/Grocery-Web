"""
Cartify Cart Schemas (Module 7)

Pydantic schemas for shopping cart operations:
- Dual camelCase and snake_case alias support across Web, iOS, and Android
- Authoritative server-side price representation (Decimal)
- Variant-level cart items with product and variant metadata
- Strict bounded quantity validation (1 <= quantity <= 99)
"""

from datetime import datetime
from decimal import Decimal
from typing import List, Optional
from pydantic import AliasChoices, BaseModel, ConfigDict, Field


class AddToCartRequest(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    variant_id: str = Field(
        ...,
        min_length=1,
        max_length=36,
        validation_alias=AliasChoices("variantId", "variant_id"),
        serialization_alias="variantId",
        description="UUID of the product variant to add to cart",
    )
    product_id: Optional[str] = Field(
        None,
        max_length=36,
        validation_alias=AliasChoices("productId", "product_id"),
        serialization_alias="productId",
        description="Optional product UUID; if omitted, resolved from variant",
    )
    quantity: int = Field(
        default=1,
        ge=1,
        le=99,
        description="Quantity to add (bounded between 1 and 99)",
    )


class UpdateCartItemRequest(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    quantity: int = Field(
        ...,
        ge=1,
        le=99,
        description="New quantity for cart item (bounded between 1 and 99)",
    )


class CartVariantSummary(BaseModel):
    model_config = ConfigDict(populate_by_name=True, from_attributes=True)

    id: str
    product_id: Optional[str] = Field(
        None,
        validation_alias=AliasChoices("productId", "product_id"),
        serialization_alias="productId",
    )
    sku: Optional[str] = None
    name: Optional[str] = None
    unit: Optional[str] = None
    price: Decimal
    mrp: Optional[Decimal] = None
    stock_quantity: int = Field(
        default=0,
        validation_alias=AliasChoices("stockQuantity", "stock_quantity"),
        serialization_alias="stockQuantity",
    )
    is_active: bool = Field(
        default=True,
        validation_alias=AliasChoices("isActive", "is_active"),
        serialization_alias="isActive",
    )


class CartProductSummary(BaseModel):
    model_config = ConfigDict(populate_by_name=True, from_attributes=True)

    id: str
    title: str = Field(
        ...,
        validation_alias=AliasChoices("title", "name"),
        serialization_alias="title",
    )
    slug: str
    thumbnail_url: Optional[str] = Field(
        None,
        validation_alias=AliasChoices("thumbnailUrl", "thumbnail_url", "image_url", "imageUrl"),
        serialization_alias="thumbnailUrl",
    )
    is_active: bool = Field(
        default=True,
        validation_alias=AliasChoices("isActive", "is_active"),
        serialization_alias="isActive",
    )


class CartItemResponse(BaseModel):
    model_config = ConfigDict(populate_by_name=True, from_attributes=True)

    id: str
    cart_id: str = Field(
        ...,
        validation_alias=AliasChoices("cartId", "cart_id"),
        serialization_alias="cartId",
    )
    product_id: str = Field(
        ...,
        validation_alias=AliasChoices("productId", "product_id"),
        serialization_alias="productId",
    )
    variant_id: str = Field(
        ...,
        validation_alias=AliasChoices("variantId", "variant_id"),
        serialization_alias="variantId",
    )
    quantity: int
    unit_price: Decimal = Field(
        ...,
        validation_alias=AliasChoices("unitPrice", "unit_price"),
        serialization_alias="unitPrice",
    )
    line_total: Decimal = Field(
        ...,
        validation_alias=AliasChoices("lineTotal", "line_total"),
        serialization_alias="lineTotal",
    )
    product: CartProductSummary
    variant: CartVariantSummary
    created_at: Optional[datetime] = Field(
        None,
        validation_alias=AliasChoices("createdAt", "created_at"),
        serialization_alias="createdAt",
    )
    updated_at: Optional[datetime] = Field(
        None,
        validation_alias=AliasChoices("updatedAt", "updated_at"),
        serialization_alias="updatedAt",
    )


from app.schemas.coupon import CouponSummary


class CartResponse(BaseModel):
    model_config = ConfigDict(populate_by_name=True, from_attributes=True)

    id: str
    user_id: str = Field(
        ...,
        validation_alias=AliasChoices("userId", "user_id"),
        serialization_alias="userId",
    )
    items: List[CartItemResponse] = Field(default_factory=list)
    item_count: int = Field(
        default=0,
        validation_alias=AliasChoices("itemCount", "item_count"),
        serialization_alias="itemCount",
    )
    subtotal: Decimal = Field(default=Decimal("0.00"))
    discount: Decimal = Field(default=Decimal("0.00"))
    delivery_fee: Decimal = Field(
        default=Decimal("0.00"),
        validation_alias=AliasChoices("deliveryFee", "delivery_fee"),
        serialization_alias="deliveryFee",
    )
    tax: Decimal = Field(default=Decimal("0.00"))
    total: Decimal = Field(default=Decimal("0.00"))
    applied_coupon: Optional[CouponSummary] = Field(
        None,
        validation_alias=AliasChoices("appliedCoupon", "applied_coupon", "coupon"),
        serialization_alias="appliedCoupon",
    )
    created_at: Optional[datetime] = Field(
        None,
        validation_alias=AliasChoices("createdAt", "created_at"),
        serialization_alias="createdAt",
    )
    updated_at: Optional[datetime] = Field(
        None,
        validation_alias=AliasChoices("updatedAt", "updated_at"),
        serialization_alias="updatedAt",
    )


class CartClearResponse(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    message: str = "Cart cleared successfully"
    cart_id: Optional[str] = Field(
        None,
        validation_alias=AliasChoices("cartId", "cart_id"),
        serialization_alias="cartId",
    )
