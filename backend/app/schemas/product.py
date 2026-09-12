"""
Cartify Product Schemas (Module 4)

Pydantic schemas for product catalog operations:
- Product creation with optional embedded initial variants and images
- Mass-assignment protected partial update schemas
- Scalable keyset pagination filters with whitelisted sort validation
- Lightweight summary and rich detail response envelopes with camelCase aliases via AliasChoices
"""

from datetime import datetime
from decimal import Decimal
from typing import List, Literal, Optional
from pydantic import AliasChoices, BaseModel, ConfigDict, Field, field_validator

from app.schemas.category import CategoryResponse
from app.schemas.product_image import ProductImageCreate, ProductImageResponse
from app.schemas.product_variant import ProductVariantCreate, ProductVariantResponse


class ProductBase(BaseModel):
    name: str = Field(..., min_length=2, max_length=255, description="Product title")
    category_id: str = Field(
        ...,
        min_length=1,
        max_length=36,
        validation_alias=AliasChoices("categoryId", "category_id"),
        serialization_alias="categoryId",
        description="Referenced category UUID",
    )
    brand: str = Field(..., min_length=1, max_length=128, description="Product brand name")
    description: str = Field(..., min_length=2, description="Detailed product description")
    short_description: Optional[str] = Field(
        None,
        max_length=500,
        validation_alias=AliasChoices("shortDescription", "short_description"),
        serialization_alias="shortDescription",
        description="Concise synopsis",
    )
    image_url: Optional[str] = Field(
        None,
        max_length=1024,
        validation_alias=AliasChoices("imageUrl", "image_url"),
        serialization_alias="imageUrl",
        description="Primary thumbnail image URL",
    )
    is_featured: bool = Field(
        False,
        validation_alias=AliasChoices("isFeatured", "is_featured"),
        serialization_alias="isFeatured",
        description="Flag for featured placements",
    )
    is_active: bool = Field(
        True,
        validation_alias=AliasChoices("isActive", "is_active"),
        serialization_alias="isActive",
        description="Public customer visibility flag",
    )

    @field_validator("name", "brand")
    @classmethod
    def clean_text(cls, v: str) -> str:
        clean = v.strip()
        if not clean:
            raise ValueError("Field cannot be empty")
        return clean


class ProductCreate(ProductBase):
    variants: List[ProductVariantCreate] = Field(
        default_factory=list,
        description="Optional initial product variants created atomically",
    )
    images: List[ProductImageCreate] = Field(
        default_factory=list,
        description="Optional initial product images created atomically",
    )


class ProductUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=2, max_length=255)
    category_id: Optional[str] = Field(
        None,
        min_length=1,
        max_length=36,
        validation_alias=AliasChoices("categoryId", "category_id"),
    )
    brand: Optional[str] = Field(None, min_length=1, max_length=128)
    description: Optional[str] = Field(None, min_length=2)
    short_description: Optional[str] = Field(
        None,
        max_length=500,
        validation_alias=AliasChoices("shortDescription", "short_description"),
    )
    image_url: Optional[str] = Field(
        None,
        max_length=1024,
        validation_alias=AliasChoices("imageUrl", "image_url"),
    )
    is_featured: Optional[bool] = Field(
        None,
        validation_alias=AliasChoices("isFeatured", "is_featured"),
    )
    is_active: Optional[bool] = Field(
        None,
        validation_alias=AliasChoices("isActive", "is_active"),
    )

    @field_validator("name", "brand", mode="before")
    @classmethod
    def clean_optional_text(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return v
        clean = v.strip()
        if not clean:
            raise ValueError("Field cannot be empty")
        return clean


class ProductStatusUpdate(BaseModel):
    is_active: bool = Field(
        ...,
        validation_alias=AliasChoices("isActive", "is_active"),
        description="Active visibility state",
    )


class ProductFilterParams(BaseModel):
    category_id: Optional[str] = Field(None, description="Filter by category or subcategory ID")
    subcategory_id: Optional[str] = Field(None, description="Filter by subcategory ID")
    brand: Optional[str] = Field(None, description="Filter by exact or prefix brand name")
    featured: Optional[bool] = Field(None, description="Filter by is_featured flag")
    is_featured: Optional[bool] = Field(None, description="Alias for featured")
    sort: Optional[str] = Field(
        "newest",
        description="Whitelisted sort: newest, price_low_to_high, price_high_to_low, featured",
    )
    cursor: Optional[str] = Field(None, description="Keyset pagination cursor")
    limit: int = Field(20, ge=1, le=100, description="Page limit (default 20, max 100)")

    @field_validator("sort")
    @classmethod
    def validate_sort(cls, v: Optional[str]) -> str:
        allowed = {"newest", "price_low_to_high", "price_high_to_low", "featured"}
        if v and v not in allowed:
            raise ValueError(f"Invalid sort option '{v}'. Allowed: {', '.join(sorted(allowed))}")
        return v or "newest"


class ProductSummaryResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True, populate_by_name=True)

    id: str
    category_id: str = Field(
        ...,
        validation_alias=AliasChoices("categoryId", "category_id"),
        serialization_alias="categoryId",
    )
    category_name: Optional[str] = Field(
        None,
        validation_alias=AliasChoices("categoryName", "category_name"),
        serialization_alias="categoryName",
    )
    category_slug: Optional[str] = Field(
        None,
        validation_alias=AliasChoices("categorySlug", "category_slug"),
        serialization_alias="categorySlug",
    )
    name: str
    slug: str
    brand: str
    description: str
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
    max_price: Optional[Decimal] = Field(
        None,
        validation_alias=AliasChoices("maxPrice", "max_price"),
        serialization_alias="maxPrice",
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


class ProductDetailResponse(ProductSummaryResponse):
    category: Optional[CategoryResponse] = None


class ProductListResponse(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    items: List[ProductSummaryResponse]
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
    total: Optional[int] = None
