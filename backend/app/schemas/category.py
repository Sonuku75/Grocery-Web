"""
Cartify Category Pydantic Schemas (Module 3)

Validates category creation, partial updates, and serialization
with support for self-referencing subcategories and camelCase aliases.
"""

from datetime import datetime
import re
from typing import Any, List, Optional
from pydantic import BaseModel, ConfigDict, Field, field_validator


class CategoryBase(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    name: str = Field(..., min_length=2, max_length=100, description="Category name")
    description: Optional[str] = Field(None, description="Category description")
    icon: Optional[str] = Field("Compass", max_length=64, description="Icon name")
    image_url: Optional[str] = Field(None, alias="imageUrl", max_length=1024, description="Category display image URL")
    parent_id: Optional[str] = Field(None, alias="parentId", max_length=36, description="Parent category UUID for subcategories")
    sort_order: int = Field(0, alias="sortOrder", ge=0, description="Display sort order")
    is_active: bool = Field(True, alias="isActive", description="Whether category is active")

    @field_validator("name")
    @classmethod
    def validate_name(cls, v: str) -> str:
        cleaned = " ".join(v.strip().split())
        if len(cleaned) < 2:
            raise ValueError("Category name must contain at least 2 non-whitespace characters.")
        return cleaned


class CategoryCreateRequest(CategoryBase):
    slug: Optional[str] = Field(None, min_length=2, max_length=120, description="Custom slug or auto-generated if omitted")

    @field_validator("slug")
    @classmethod
    def validate_slug(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return None
        cleaned = v.strip().lower()
        if not re.match(r"^[a-z0-9]+(?:-[a-z0-9]+)*$", cleaned):
            raise ValueError("Slug must be lowercase alphanumeric characters separated by single hyphens.")
        return cleaned


# Legacy alias for Module 0 compatibility
CategoryCreate = CategoryCreateRequest


class CategoryUpdateRequest(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    name: Optional[str] = Field(None, min_length=2, max_length=100)
    slug: Optional[str] = Field(None, min_length=2, max_length=120)
    description: Optional[str] = None
    icon: Optional[str] = Field(None, max_length=64)
    image_url: Optional[str] = Field(None, alias="imageUrl", max_length=1024)
    parent_id: Optional[str] = Field(None, alias="parentId", max_length=36)
    sort_order: Optional[int] = Field(None, alias="sortOrder", ge=0)
    is_active: Optional[bool] = Field(None, alias="isActive")

    @field_validator("name")
    @classmethod
    def validate_name(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return None
        cleaned = " ".join(v.strip().split())
        if len(cleaned) < 2:
            raise ValueError("Category name must contain at least 2 non-whitespace characters.")
        return cleaned

    @field_validator("slug")
    @classmethod
    def validate_slug(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return None
        cleaned = v.strip().lower()
        if not re.match(r"^[a-z0-9]+(?:-[a-z0-9]+)*$", cleaned):
            raise ValueError("Slug must be lowercase alphanumeric characters separated by single hyphens.")
        return cleaned


class CategoryResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True, populate_by_name=True)

    id: str
    name: str
    slug: str
    description: Optional[str] = None
    icon: Optional[str] = "Compass"
    image_url: Optional[str] = Field(None, alias="imageUrl")
    parent_id: Optional[str] = Field(None, alias="parentId")
    is_active: bool = Field(True, alias="isActive")
    sort_order: int = Field(0, alias="sortOrder")
    created_at: Optional[datetime] = Field(None, alias="createdAt")
    updated_at: Optional[datetime] = Field(None, alias="updatedAt")
    subcategories: Optional[List["CategoryResponse"]] = None
    item_count: Optional[int] = Field(0, alias="itemCount")


class CategoryListResponse(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    items: List[CategoryResponse]
    total: int

