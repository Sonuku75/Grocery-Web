"""
Cartify Inventory Schemas (Module 11)

Pydantic v2 schemas for customer availability and admin inventory management:
- CustomerInventoryResponse: strictly customer-safe availability data
- AdminInventoryResponse: comprehensive operational stock metrics
- AdminCreateInventoryRequest: variant inventory initialization
- AdminAdjustStockRequest: signed inventory adjustments with mandatory reason
- InventoryTransactionResponse: immutable transaction audit log
"""

from datetime import datetime
from typing import List, Optional
from pydantic import AliasChoices, BaseModel, ConfigDict, Field

from app.models.inventory import InventoryTransactionType


class CustomerInventoryResponse(BaseModel):
    model_config = ConfigDict(populate_by_name=True, from_attributes=True)

    variant_id: str = Field(
        ...,
        validation_alias=AliasChoices("variantId", "variant_id"),
        serialization_alias="variantId",
    )
    available_quantity: int = Field(
        ...,
        validation_alias=AliasChoices("availableQuantity", "available_quantity"),
        serialization_alias="availableQuantity",
    )
    is_available: bool = Field(
        ...,
        validation_alias=AliasChoices("isAvailable", "is_available"),
        serialization_alias="isAvailable",
    )
    is_low_stock: bool = Field(
        ...,
        validation_alias=AliasChoices("isLowStock", "is_low_stock"),
        serialization_alias="isLowStock",
    )


class AdminInventoryResponse(BaseModel):
    model_config = ConfigDict(populate_by_name=True, from_attributes=True)

    id: str
    variant_id: str = Field(
        ...,
        validation_alias=AliasChoices("variantId", "variant_id"),
        serialization_alias="variantId",
    )
    product_id: Optional[str] = Field(
        None,
        validation_alias=AliasChoices("productId", "product_id"),
        serialization_alias="productId",
    )
    product_title: Optional[str] = Field(
        None,
        validation_alias=AliasChoices("productTitle", "product_title"),
        serialization_alias="productTitle",
    )
    variant_name: Optional[str] = Field(
        None,
        validation_alias=AliasChoices("variantName", "variant_name"),
        serialization_alias="variantName",
    )
    sku: Optional[str] = None
    quantity: int
    reserved_quantity: int = Field(
        ...,
        validation_alias=AliasChoices("reservedQuantity", "reserved_quantity"),
        serialization_alias="reservedQuantity",
    )
    available_quantity: int = Field(
        ...,
        validation_alias=AliasChoices("availableQuantity", "available_quantity"),
        serialization_alias="availableQuantity",
    )
    low_stock_threshold: int = Field(
        ...,
        validation_alias=AliasChoices("lowStockThreshold", "low_stock_threshold"),
        serialization_alias="lowStockThreshold",
    )
    is_active: bool = Field(
        ...,
        validation_alias=AliasChoices("isActive", "is_active"),
        serialization_alias="isActive",
    )
    is_low_stock: bool = Field(
        ...,
        validation_alias=AliasChoices("isLowStock", "is_low_stock"),
        serialization_alias="isLowStock",
    )
    is_out_of_stock: bool = Field(
        ...,
        validation_alias=AliasChoices("isOutOfStock", "is_out_of_stock"),
        serialization_alias="isOutOfStock",
    )
    created_at: datetime = Field(
        ...,
        validation_alias=AliasChoices("createdAt", "created_at"),
        serialization_alias="createdAt",
    )
    updated_at: Optional[datetime] = Field(
        None,
        validation_alias=AliasChoices("updatedAt", "updated_at"),
        serialization_alias="updatedAt",
    )


class AdminInventoryListResponse(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    items: List[AdminInventoryResponse] = Field(default_factory=list)
    total: int
    limit: int
    offset: int


class AdminCreateInventoryRequest(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    variant_id: str = Field(
        ...,
        validation_alias=AliasChoices("variantId", "variant_id"),
        serialization_alias="variantId",
    )
    quantity: int = Field(default=0, ge=0)
    low_stock_threshold: int = Field(
        default=5,
        ge=0,
        validation_alias=AliasChoices("lowStockThreshold", "low_stock_threshold"),
        serialization_alias="lowStockThreshold",
    )
    is_active: bool = Field(
        default=True,
        validation_alias=AliasChoices("isActive", "is_active"),
        serialization_alias="isActive",
    )


class AdminUpdateInventoryRequest(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    low_stock_threshold: Optional[int] = Field(
        None,
        ge=0,
        validation_alias=AliasChoices("lowStockThreshold", "low_stock_threshold"),
        serialization_alias="lowStockThreshold",
    )
    is_active: Optional[bool] = Field(
        None,
        validation_alias=AliasChoices("isActive", "is_active"),
        serialization_alias="isActive",
    )


class AdminAdjustStockRequest(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    quantity_change: int = Field(
        ...,
        description="Signed delta to add or remove from total stock, e.g. +50 or -10",
        validation_alias=AliasChoices("quantityChange", "quantity_change"),
        serialization_alias="quantityChange",
    )
    reason: str = Field(..., min_length=3, max_length=255)
    transaction_type: Optional[str] = Field(
        None,
        description="Optional specific transaction type like DAMAGE, RESTOCK, ADJUSTMENT",
        validation_alias=AliasChoices("transactionType", "transaction_type"),
        serialization_alias="transactionType",
    )
    reference_type: Optional[str] = Field(
        "ADMIN_ADJUSTMENT",
        max_length=64,
        validation_alias=AliasChoices("referenceType", "reference_type"),
        serialization_alias="referenceType",
    )
    reference_id: Optional[str] = Field(
        None,
        max_length=64,
        validation_alias=AliasChoices("referenceId", "reference_id"),
        serialization_alias="referenceId",
    )


class InventoryTransactionResponse(BaseModel):
    model_config = ConfigDict(populate_by_name=True, from_attributes=True)

    id: str
    inventory_id: str = Field(
        ...,
        validation_alias=AliasChoices("inventoryId", "inventory_id"),
        serialization_alias="inventoryId",
    )
    variant_id: str = Field(
        ...,
        validation_alias=AliasChoices("variantId", "variant_id"),
        serialization_alias="variantId",
    )
    transaction_type: str = Field(
        ...,
        validation_alias=AliasChoices("transactionType", "transaction_type"),
        serialization_alias="transactionType",
    )
    quantity_change: int = Field(
        ...,
        validation_alias=AliasChoices("quantityChange", "quantity_change"),
        serialization_alias="quantityChange",
    )
    quantity_before: int = Field(
        ...,
        validation_alias=AliasChoices("quantityBefore", "quantity_before"),
        serialization_alias="quantityBefore",
    )
    quantity_after: int = Field(
        ...,
        validation_alias=AliasChoices("quantityAfter", "quantity_after"),
        serialization_alias="quantityAfter",
    )
    reference_type: Optional[str] = Field(
        None,
        validation_alias=AliasChoices("referenceType", "reference_type"),
        serialization_alias="referenceType",
    )
    reference_id: Optional[str] = Field(
        None,
        validation_alias=AliasChoices("referenceId", "reference_id"),
        serialization_alias="referenceId",
    )
    reason: Optional[str] = None
    created_by_user_id: Optional[str] = Field(
        None,
        validation_alias=AliasChoices("createdByUserId", "created_by_user_id"),
        serialization_alias="createdByUserId",
    )
    created_at: datetime = Field(
        ...,
        validation_alias=AliasChoices("createdAt", "created_at"),
        serialization_alias="createdAt",
    )
