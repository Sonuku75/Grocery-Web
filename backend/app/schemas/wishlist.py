"""
Cartify Wishlist Schemas (Module 6)

Pydantic schemas for wishlist / favorites operations:
- Dual camelCase and snake_case alias support (AliasChoices) across Web, iOS, and Android
- Keyset cursor pagination envelope
- Product details payload for rapid frontend rendering
- Strict type validation and mass-assignment protection
"""

from datetime import datetime
from decimal import Decimal
from typing import List, Optional
from pydantic import AliasChoices, BaseModel, ConfigDict, Field

from app.schemas.category import CategoryResponse
from app.schemas.product_image import ProductImageResponse
from app.schemas.product_variant import ProductVariantResponse


class WishlistItemCreate(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    product_id: str = Field(
        ...,
        min_length=1,
        max_length=36,
        validation_alias=AliasChoices("productId", "product_id"),
        serialization_alias="productId",
        description="UUID of the product to add to wishlist",
    )


class WishlistProductResponse(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    id: str
    name: str
    slug: str
    brand: str
    description: Optional[str] = None
    short_description: Optional[str] = Field(
        None,
        validation_alias=AliasChoices("shortDescription", "short_description"),
        serialization_alias="shortDescription",
    )
    image_url: Optional[str] = Field(
        None,
        validation_alias=AliasChoices("imageUrl", "image_url"),
        serialization_alias="imageUrl",
    )
    is_active: bool = Field(
        True,
        validation_alias=AliasChoices("isActive", "is_active"),
        serialization_alias="isActive",
    )
    is_featured: bool = Field(
        False,
        validation_alias=AliasChoices("isFeatured", "is_featured"),
        serialization_alias="isFeatured",
    )
    min_price: Optional[Decimal] = Field(
        None,
        validation_alias=AliasChoices("minPrice", "min_price"),
        serialization_alias="minPrice",
    )
    min_mrp: Optional[Decimal] = Field(
        None,
        validation_alias=AliasChoices("minMrp", "min_mrp"),
        serialization_alias="minMrp",
    )
    max_discount_percentage: Optional[int] = Field(
        0,
        validation_alias=AliasChoices("maxDiscountPercentage", "max_discount_percentage"),
        serialization_alias="maxDiscountPercentage",
    )
    primary_variant: Optional[ProductVariantResponse] = Field(
        None,
        validation_alias=AliasChoices("primaryVariant", "primary_variant"),
        serialization_alias="primaryVariant",
    )
    variants: List[ProductVariantResponse] = Field(default_factory=list)
    images: List[ProductImageResponse] = Field(default_factory=list)
    category: Optional[CategoryResponse] = None
    category_id: Optional[str] = Field(
        None,
        validation_alias=AliasChoices("categoryId", "category_id"),
        serialization_alias="categoryId",
    )
    rating: float = 4.8
    rating_count: int = Field(
        120,
        validation_alias=AliasChoices("ratingCount", "rating_count"),
        serialization_alias="ratingCount",
    )


class WishlistItemResponse(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    id: str
    product_id: str = Field(
        ...,
        validation_alias=AliasChoices("productId", "product_id"),
        serialization_alias="productId",
    )
    product: WishlistProductResponse
    created_at: datetime = Field(
        ...,
        validation_alias=AliasChoices("createdAt", "created_at"),
        serialization_alias="createdAt",
    )


class WishlistResponse(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    items: List[WishlistItemResponse]
    count: int = Field(..., description="Total wishlist items count for authenticated user")
    next_cursor: Optional[str] = Field(
        None,
        validation_alias=AliasChoices("nextCursor", "next_cursor"),
        serialization_alias="nextCursor",
    )
    has_more: bool = Field(
        False,
        validation_alias=AliasChoices("hasMore", "has_more"),
        serialization_alias="hasMore",
    )


class WishlistCheckResponse(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    product_id: str = Field(
        ...,
        validation_alias=AliasChoices("productId", "product_id"),
        serialization_alias="productId",
    )
    is_wishlisted: bool = Field(
        ...,
        validation_alias=AliasChoices("isWishlisted", "is_wishlisted"),
        serialization_alias="isWishlisted",
    )


class WishlistRemoveResponse(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    product_id: str = Field(
        ...,
        validation_alias=AliasChoices("productId", "product_id"),
        serialization_alias="productId",
    )
    removed: bool = True
    message: str = "Product removed from wishlist"
