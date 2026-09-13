"""
Cartify Search Schemas (Module 5)

Defines request validation and response models for:
- GET /api/v1/search (Full search catalog with filtering, sorting, relevance, pagination)
- GET /api/v1/search/suggestions (Autocomplete suggestions for products, brands, categories)
"""

from decimal import Decimal
from typing import List, Literal, Optional
from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    field_validator,
    model_validator,
    AliasChoices,
)


class SearchFilterParams(BaseModel):
    """
    Query parameter model for GET /api/v1/search.
    Supports query string, category, brand, price range, sorting, and keyset cursor pagination.
    """
    model_config = ConfigDict(extra="forbid")

    q: Optional[str] = Field(
        None,
        description="Search keyword (max 100 chars, whitespace trimmed)",
    )
    category_id: Optional[str] = Field(
        None,
        description="Optional category or subcategory ID filter",
    )
    brand: Optional[str] = Field(
        None,
        max_length=100,
        description="Optional brand name filter",
    )
    min_price: Optional[Decimal] = Field(
        None,
        ge=0,
        description="Minimum variant selling price",
    )
    max_price: Optional[Decimal] = Field(
        None,
        ge=0,
        description="Maximum variant selling price",
    )
    sort: Literal[
        "relevance",
        "price_low_to_high",
        "price_high_to_low",
        "newest",
        "featured",
    ] = Field(
        "relevance",
        description="Sort order (relevance default for keyword search)",
    )
    cursor: Optional[str] = Field(
        None,
        description="Opaque base64 pagination cursor",
    )
    limit: int = Field(
        20,
        ge=1,
        le=50,
        description="Items per page (1-50, default 20)",
    )

    @field_validator("q")
    @classmethod
    def validate_query(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return None
        trimmed = v.strip()
        if not trimmed:
            raise ValueError("Search query cannot be empty or purely whitespace.")
        if len(trimmed) > 100:
            raise ValueError("Search query cannot exceed 100 characters.")
        return trimmed

    @field_validator("brand")
    @classmethod
    def validate_brand(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return None
        trimmed = v.strip()
        return trimmed if trimmed else None

    @model_validator(mode="after")
    def validate_price_range(self) -> "SearchFilterParams":
        if self.min_price is not None and self.max_price is not None:
            if self.min_price > self.max_price:
                raise ValueError("min_price cannot be greater than max_price.")
        return self


class SearchSuggestionParams(BaseModel):
    """
    Query parameter model for GET /api/v1/search/suggestions.
    """
    model_config = ConfigDict(extra="forbid")

    q: str = Field(
        ...,
        description="Autocomplete search prefix (1-100 characters)",
    )
    limit: int = Field(
        8,
        ge=1,
        le=20,
        description="Max suggestions to return (1-20, default 8)",
    )

    @field_validator("q")
    @classmethod
    def validate_suggestion_query(cls, v: str) -> str:
        trimmed = v.strip()
        if not trimmed:
            raise ValueError("Query parameter 'q' cannot be empty or whitespace.")
        if len(trimmed) > 100:
            raise ValueError("Query parameter 'q' cannot exceed 100 characters.")
        return trimmed


class SearchItemCategory(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    id: str
    name: str
    slug: str


class SearchItem(BaseModel):
    """
    Compact product search result model optimized for listing performance.
    """
    model_config = ConfigDict(populate_by_name=True)

    id: str
    name: str
    slug: str
    brand: str
    image_url: Optional[str] = Field(
        None,
        validation_alias=AliasChoices("image_url", "imageUrl"),
        serialization_alias="imageUrl",
    )
    price: Decimal
    mrp: Decimal
    discount_percentage: Decimal = Field(
        ...,
        validation_alias=AliasChoices("discount_percentage", "discountPercentage"),
        serialization_alias="discountPercentage",
    )
    unit: Optional[str] = None
    is_featured: bool = Field(
        False,
        validation_alias=AliasChoices("is_featured", "isFeatured"),
        serialization_alias="isFeatured",
    )
    category: Optional[SearchItemCategory] = None


class SearchResponse(BaseModel):
    """
    Container response for product search results.
    """
    model_config = ConfigDict(populate_by_name=True)

    query: Optional[str] = None
    items: List[SearchItem] = Field(default_factory=list)
    next_cursor: Optional[str] = Field(
        None,
        validation_alias=AliasChoices("next_cursor", "nextCursor"),
        serialization_alias="nextCursor",
    )
    has_more: bool = Field(
        False,
        validation_alias=AliasChoices("has_more", "hasMore"),
        serialization_alias="hasMore",
    )
    total: int = 0


class SuggestionItem(BaseModel):
    """
    Single autocomplete suggestion entity (product, brand, or category).
    """
    model_config = ConfigDict(populate_by_name=True)

    type: Literal["product", "brand", "category"]
    label: str
    slug: Optional[str] = None
    id: Optional[str] = None
    price: Optional[Decimal] = None
    image_url: Optional[str] = Field(
        None,
        validation_alias=AliasChoices("image_url", "imageUrl"),
        serialization_alias="imageUrl",
    )


class SearchSuggestionResponse(BaseModel):
    """
    Container response for autocomplete suggestions.
    """
    model_config = ConfigDict(populate_by_name=True)

    items: List[SuggestionItem] = Field(default_factory=list)
