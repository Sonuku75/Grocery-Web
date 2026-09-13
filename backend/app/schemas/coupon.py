"""
Cartify Coupon Schemas (Module 8)

Pydantic schemas for coupons, promotions, and discount validation:
- Constrained DiscountType ('PERCENTAGE', 'FIXED_AMOUNT')
- Dual camelCase and snake_case alias support across Web, iOS, and Android
- Validation of start and expiration dates, percentage bounds, and limits
- Safe public summaries excluding sensitive counter metadata
"""

from datetime import datetime
from decimal import Decimal
from enum import Enum
from typing import List, Optional
from pydantic import (
    AliasChoices,
    BaseModel,
    ConfigDict,
    Field,
    field_validator,
    model_validator,
)


class DiscountType(str, Enum):
    PERCENTAGE = "PERCENTAGE"
    FIXED_AMOUNT = "FIXED_AMOUNT"


class CouponSummary(BaseModel):
    model_config = ConfigDict(populate_by_name=True, from_attributes=True)

    id: str
    code: str
    name: str
    description: Optional[str] = None
    discount_type: DiscountType = Field(
        ...,
        validation_alias=AliasChoices("discountType", "discount_type"),
        serialization_alias="discountType",
    )
    discount_value: Decimal = Field(
        ...,
        validation_alias=AliasChoices("discountValue", "discount_value"),
        serialization_alias="discountValue",
    )
    minimum_order_value: Decimal = Field(
        default=Decimal("0.00"),
        validation_alias=AliasChoices("minimumOrderValue", "minimum_order_value", "minOrderAmount"),
        serialization_alias="minimumOrderValue",
    )
    maximum_discount: Optional[Decimal] = Field(
        None,
        validation_alias=AliasChoices("maximumDiscount", "maximum_discount", "maxDiscount"),
        serialization_alias="maximumDiscount",
    )
    expires_at: datetime = Field(
        ...,
        validation_alias=AliasChoices("expiresAt", "expires_at", "validUntil"),
        serialization_alias="expiresAt",
    )
    is_active: bool = Field(
        default=True,
        validation_alias=AliasChoices("isActive", "is_active"),
        serialization_alias="isActive",
    )


class CouponDetailResponse(CouponSummary):
    model_config = ConfigDict(populate_by_name=True, from_attributes=True)

    starts_at: datetime = Field(
        ...,
        validation_alias=AliasChoices("startsAt", "starts_at"),
        serialization_alias="startsAt",
    )
    usage_limit: Optional[int] = Field(
        None,
        validation_alias=AliasChoices("usageLimit", "usage_limit"),
        serialization_alias="usageLimit",
    )
    per_user_usage_limit: Optional[int] = Field(
        None,
        validation_alias=AliasChoices("perUserUsageLimit", "per_user_usage_limit"),
        serialization_alias="perUserUsageLimit",
    )
    used_count: int = Field(
        default=0,
        validation_alias=AliasChoices("usedCount", "used_count"),
        serialization_alias="usedCount",
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


class CouponCreateRequest(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    code: str = Field(..., min_length=2, max_length=64, description="Unique coupon code")
    name: str = Field(..., min_length=2, max_length=255, description="Coupon display title")
    description: Optional[str] = Field(None, max_length=1000)
    discount_type: DiscountType = Field(
        ...,
        validation_alias=AliasChoices("discountType", "discount_type"),
        serialization_alias="discountType",
    )
    discount_value: Decimal = Field(
        ...,
        gt=0,
        validation_alias=AliasChoices("discountValue", "discount_value"),
        serialization_alias="discountValue",
    )
    minimum_order_value: Decimal = Field(
        default=Decimal("0.00"),
        ge=0,
        validation_alias=AliasChoices("minimumOrderValue", "minimum_order_value"),
        serialization_alias="minimumOrderValue",
    )
    maximum_discount: Optional[Decimal] = Field(
        None,
        ge=0,
        validation_alias=AliasChoices("maximumDiscount", "maximum_discount"),
        serialization_alias="maximumDiscount",
    )
    starts_at: datetime = Field(
        ...,
        validation_alias=AliasChoices("startsAt", "starts_at"),
        serialization_alias="startsAt",
    )
    expires_at: datetime = Field(
        ...,
        validation_alias=AliasChoices("expiresAt", "expires_at"),
        serialization_alias="expiresAt",
    )
    usage_limit: Optional[int] = Field(
        None,
        gt=0,
        validation_alias=AliasChoices("usageLimit", "usage_limit"),
        serialization_alias="usageLimit",
    )
    per_user_usage_limit: Optional[int] = Field(
        None,
        gt=0,
        validation_alias=AliasChoices("perUserUsageLimit", "per_user_usage_limit"),
        serialization_alias="perUserUsageLimit",
    )
    is_active: bool = Field(
        default=True,
        validation_alias=AliasChoices("isActive", "is_active"),
        serialization_alias="isActive",
    )

    @field_validator("code")
    @classmethod
    def normalize_code(cls, v: str) -> str:
        code = v.strip().upper()
        if not code:
            raise ValueError("Coupon code cannot be blank.")
        return code

    @model_validator(mode="after")
    def validate_rules(self) -> "CouponCreateRequest":
        if self.expires_at <= self.starts_at:
            raise ValueError("expires_at must be strictly after starts_at.")
        if self.discount_type == DiscountType.PERCENTAGE:
            if self.discount_value <= 0 or self.discount_value > 100:
                raise ValueError("Percentage discount must be between 1 and 100.")
        return self


class CouponUpdateRequest(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    name: Optional[str] = Field(None, min_length=2, max_length=255)
    description: Optional[str] = Field(None, max_length=1000)
    discount_type: Optional[DiscountType] = Field(
        None,
        validation_alias=AliasChoices("discountType", "discount_type"),
        serialization_alias="discountType",
    )
    discount_value: Optional[Decimal] = Field(
        None,
        gt=0,
        validation_alias=AliasChoices("discountValue", "discount_value"),
        serialization_alias="discountValue",
    )
    minimum_order_value: Optional[Decimal] = Field(
        None,
        ge=0,
        validation_alias=AliasChoices("minimumOrderValue", "minimum_order_value"),
        serialization_alias="minimumOrderValue",
    )
    maximum_discount: Optional[Decimal] = Field(
        None,
        ge=0,
        validation_alias=AliasChoices("maximumDiscount", "maximum_discount"),
        serialization_alias="maximumDiscount",
    )
    starts_at: Optional[datetime] = Field(
        None,
        validation_alias=AliasChoices("startsAt", "starts_at"),
        serialization_alias="startsAt",
    )
    expires_at: Optional[datetime] = Field(
        None,
        validation_alias=AliasChoices("expiresAt", "expires_at"),
        serialization_alias="expiresAt",
    )
    usage_limit: Optional[int] = Field(
        None,
        gt=0,
        validation_alias=AliasChoices("usageLimit", "usage_limit"),
        serialization_alias="usageLimit",
    )
    per_user_usage_limit: Optional[int] = Field(
        None,
        gt=0,
        validation_alias=AliasChoices("perUserUsageLimit", "per_user_usage_limit"),
        serialization_alias="perUserUsageLimit",
    )
    is_active: Optional[bool] = Field(
        None,
        validation_alias=AliasChoices("isActive", "is_active"),
        serialization_alias="isActive",
    )


class CouponValidateRequest(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    code: str = Field(
        ...,
        min_length=1,
        max_length=64,
        description="Coupon promo code to validate against active cart",
    )

    @field_validator("code")
    @classmethod
    def normalize_code(cls, v: str) -> str:
        return v.strip().upper()


class CouponValidateResponse(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    valid: bool
    code: str
    discount: Decimal = Field(default=Decimal("0.00"))
    message: str
    coupon: Optional[CouponSummary] = None


class CouponListResponse(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    items: List[CouponSummary]
    total: int
