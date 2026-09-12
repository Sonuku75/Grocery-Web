"""
Cartify Product Image Schemas (Module 4)

Pydantic schemas for product gallery images:
- URL validation
- Primary image designation
- Output serialization with camelCase aliases via AliasChoices
"""

from datetime import datetime
from typing import Any, Optional
from pydantic import AliasChoices, BaseModel, ConfigDict, Field, field_validator


class ProductImageBase(BaseModel):
    image_url: str = Field(..., min_length=5, max_length=1024, description="Public CDN or storage image URL")
    alt_text: Optional[str] = Field(None, max_length=255, description="Accessible descriptive alt text")
    sort_order: int = Field(0, ge=0, description="Gallery sequencing order")
    is_primary: bool = Field(False, description="Designates the primary product thumbnail")

    @field_validator("image_url")
    @classmethod
    def validate_image_url(cls, v: str) -> str:
        clean = v.strip()
        if not (clean.startswith("http://") or clean.startswith("https://") or clean.startswith("/")):
            raise ValueError("image_url must be a valid HTTP/HTTPS URL or absolute asset path")
        return clean


class ProductImageCreate(ProductImageBase):
    pass


class ProductImageUpdate(BaseModel):
    image_url: Optional[str] = Field(None, min_length=5, max_length=1024)
    alt_text: Optional[str] = Field(None, max_length=255)
    sort_order: Optional[int] = Field(None, ge=0)
    is_primary: Optional[bool] = None

    @field_validator("image_url")
    @classmethod
    def validate_image_url(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return v
        clean = v.strip()
        if not (clean.startswith("http://") or clean.startswith("https://") or clean.startswith("/")):
            raise ValueError("image_url must be a valid HTTP/HTTPS URL or absolute asset path")
        return clean


class ProductImageResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True, populate_by_name=True)

    id: str
    product_id: str = Field(
        ...,
        validation_alias=AliasChoices("productId", "product_id"),
        serialization_alias="productId",
    )
    image_url: str = Field(
        ...,
        validation_alias=AliasChoices("imageUrl", "image_url"),
        serialization_alias="imageUrl",
    )
    alt_text: Optional[str] = Field(
        None,
        validation_alias=AliasChoices("altText", "alt_text"),
        serialization_alias="altText",
    )
    sort_order: int = Field(
        0,
        validation_alias=AliasChoices("sortOrder", "sort_order"),
        serialization_alias="sortOrder",
    )
    is_primary: bool = Field(
        False,
        validation_alias=AliasChoices("isPrimary", "is_primary"),
        serialization_alias="isPrimary",
    )
    created_at: Optional[datetime] = Field(
        None,
        validation_alias=AliasChoices("createdAt", "created_at"),
        serialization_alias="createdAt",
    )

    @field_validator("sort_order", mode="before")
    @classmethod
    def coerce_sort_order(cls, v: Any) -> int:
        return v if v is not None else 0
