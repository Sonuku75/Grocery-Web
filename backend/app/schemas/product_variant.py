"""
Cartify Product Variant Schemas (Module 4)

Pydantic schemas for product variants:
- Input validation (non-empty uppercase SKU, non-negative INR prices, price <= mrp)
- Automatic discount percentage representation
- Output serialization with camelCase aliases via AliasChoices
"""

from datetime import datetime
from decimal import Decimal
from typing import Optional
from pydantic import AliasChoices, BaseModel, ConfigDict, Field, field_validator, model_validator


class ProductVariantBase(BaseModel):
    sku: str = Field(..., min_length=1, max_length=64, description="Unique uppercase SKU identifier")
    name: str = Field(..., min_length=1, max_length=128, description="Variant name, e.g. 500 ml or 1 kg")
    unit_value: Decimal = Field(..., ge=0, description="Numerical quantity value, e.g. 500 or 1.0")
    unit_type: str = Field(..., min_length=1, max_length=32, description="Unit measurement, e.g. ml, kg, g, pack")
    price: Decimal = Field(..., ge=0, description="Selling price in ₹ INR")
    mrp: Decimal = Field(..., ge=0, description="Maximum Retail Price in ₹ INR")
    sort_order: int = Field(0, ge=0, description="Display order sequence")
    is_active: bool = Field(True, description="Whether variant is purchasable")

    @field_validator("sku")
    @classmethod
    def normalize_sku(cls, v: str) -> str:
        clean = v.strip().upper()
        if not clean:
            raise ValueError("SKU cannot be empty or whitespace only")
        return clean

    @field_validator("name")
    @classmethod
    def clean_name(cls, v: str) -> str:
        clean = v.strip()
        if not clean:
            raise ValueError("Variant name cannot be empty")
        return clean


class ProductVariantCreate(ProductVariantBase):
    @model_validator(mode="after")
    def validate_price_against_mrp(self) -> "ProductVariantCreate":
        if self.price > self.mrp:
            raise ValueError(f"Selling price ({self.price}) cannot be greater than MRP ({self.mrp})")
        return self


class ProductVariantUpdate(BaseModel):
    sku: Optional[str] = Field(None, min_length=1, max_length=64)
    name: Optional[str] = Field(None, min_length=1, max_length=128)
    unit_value: Optional[Decimal] = Field(None, ge=0)
    unit_type: Optional[str] = Field(None, min_length=1, max_length=32)
    price: Optional[Decimal] = Field(None, ge=0)
    mrp: Optional[Decimal] = Field(None, ge=0)
    sort_order: Optional[int] = Field(None, ge=0)
    is_active: Optional[bool] = None

    @field_validator("sku")
    @classmethod
    def normalize_sku(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return v
        clean = v.strip().upper()
        if not clean:
            raise ValueError("SKU cannot be empty")
        return clean

    @model_validator(mode="after")
    def validate_price_and_mrp(self) -> "ProductVariantUpdate":
        if self.price is not None and self.mrp is not None and self.price > self.mrp:
            raise ValueError(f"Selling price ({self.price}) cannot be greater than MRP ({self.mrp})")
        return self


class ProductVariantStatusUpdate(BaseModel):
    is_active: bool = Field(..., description="Active state for the variant")


class ProductVariantResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True, populate_by_name=True)

    id: str
    product_id: str = Field(
        ...,
        validation_alias=AliasChoices("productId", "product_id"),
        serialization_alias="productId",
    )
    sku: str
    name: str
    unit_value: Decimal = Field(
        ...,
        validation_alias=AliasChoices("unitValue", "unit_value"),
        serialization_alias="unitValue",
    )
    unit_type: str = Field(
        ...,
        validation_alias=AliasChoices("unitType", "unit_type"),
        serialization_alias="unitType",
    )
    price: Decimal
    mrp: Decimal
    discount_percentage: int = Field(
        0,
        validation_alias=AliasChoices("discountPercentage", "discount_percentage"),
        serialization_alias="discountPercentage",
    )
    is_active: bool = Field(
        True,
        validation_alias=AliasChoices("isActive", "is_active"),
        serialization_alias="isActive",
    )
    sort_order: int = Field(
        0,
        validation_alias=AliasChoices("sortOrder", "sort_order"),
        serialization_alias="sortOrder",
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
