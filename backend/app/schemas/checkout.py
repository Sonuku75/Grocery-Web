"""
Cartify Checkout Schemas (Module 9)

Pydantic schemas for checkout preview, session management, and order handoff:
- Dual camelCase and snake_case alias support across Web, iOS, and Android
- Authoritative server-side price and delivery fee calculation representation
- Immutable snapshots of items, addresses, and coupon details
- Session lifecycle states (ACTIVE, COMPLETED, CANCELLED, EXPIRED)
- Price change warnings and handoff responses
"""

from datetime import datetime
from decimal import Decimal
from enum import Enum
from typing import List, Optional
from pydantic import AliasChoices, BaseModel, ConfigDict, Field

from app.models.checkout import CheckoutStatus
from app.schemas.coupon import CouponSummary


class CheckoutItemSnapshot(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    variant_id: str = Field(
        ...,
        validation_alias=AliasChoices("variantId", "variant_id"),
        serialization_alias="variantId",
    )
    product_id: str = Field(
        ...,
        validation_alias=AliasChoices("productId", "product_id"),
        serialization_alias="productId",
    )
    sku: Optional[str] = None
    product_title: str = Field(
        ...,
        validation_alias=AliasChoices("productTitle", "product_title", "title", "name"),
        serialization_alias="productTitle",
    )
    variant_name: Optional[str] = Field(
        None,
        validation_alias=AliasChoices("variantName", "variant_name"),
        serialization_alias="variantName",
    )
    unit: Optional[str] = None
    quantity: int
    unit_price: Decimal = Field(
        ...,
        validation_alias=AliasChoices("unitPrice", "unit_price", "price"),
        serialization_alias="unitPrice",
    )
    line_total: Decimal = Field(
        ...,
        validation_alias=AliasChoices("lineTotal", "line_total"),
        serialization_alias="lineTotal",
    )
    thumbnail_url: Optional[str] = Field(
        None,
        validation_alias=AliasChoices("thumbnailUrl", "thumbnail_url", "image_url", "imageUrl"),
        serialization_alias="thumbnailUrl",
    )


class CheckoutAddressSnapshot(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    id: Optional[str] = None
    recipient_name: str = Field(
        ...,
        validation_alias=AliasChoices("recipientName", "recipient_name", "fullName", "full_name"),
        serialization_alias="recipientName",
    )
    phone: str = Field(
        ...,
        validation_alias=AliasChoices("phone", "mobile"),
        serialization_alias="phone",
    )
    address_line_1: str = Field(
        ...,
        validation_alias=AliasChoices("addressLine1", "address_line_1", "houseFlat", "house_flat"),
        serialization_alias="addressLine1",
    )
    address_line_2: Optional[str] = Field(
        None,
        validation_alias=AliasChoices("addressLine2", "address_line_2", "street", "area"),
        serialization_alias="addressLine2",
    )
    landmark: Optional[str] = None
    city: str
    state: str
    country: str = "India"
    postal_code: str = Field(
        ...,
        validation_alias=AliasChoices("postalCode", "postal_code", "pincode"),
        serialization_alias="postalCode",
    )
    label: Optional[str] = Field(
        "Home",
        validation_alias=AliasChoices("label", "addressType", "address_type"),
        serialization_alias="label",
    )
    latitude: Optional[float] = None
    longitude: Optional[float] = None


class CheckoutPreviewRequest(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    address_id: Optional[str] = Field(
        None,
        validation_alias=AliasChoices("addressId", "address_id"),
        serialization_alias="addressId",
        description="UUID of the selected delivery address",
    )
    delivery_method: Optional[str] = Field(
        "STANDARD",
        validation_alias=AliasChoices("deliveryMethod", "delivery_method"),
        serialization_alias="deliveryMethod",
    )
    delivery_slot: Optional[str] = Field(
        "Today • Express 15-Minute Delivery",
        validation_alias=AliasChoices("deliverySlot", "delivery_slot"),
        serialization_alias="deliverySlot",
    )


class CheckoutConfirmRequest(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    checkout_session_id: str = Field(
        ...,
        validation_alias=AliasChoices("checkoutSessionId", "checkout_session_id", "sessionId", "session_id"),
        serialization_alias="checkoutSessionId",
        description="UUID of active checkout session",
    )
    delivery_slot: Optional[str] = Field(
        None,
        validation_alias=AliasChoices("deliverySlot", "delivery_slot"),
        serialization_alias="deliverySlot",
    )
    notes: Optional[str] = Field(None, max_length=500)


class CheckoutSummaryResponse(BaseModel):
    model_config = ConfigDict(populate_by_name=True, from_attributes=True)

    id: str
    user_id: str = Field(
        ...,
        validation_alias=AliasChoices("userId", "user_id"),
        serialization_alias="userId",
    )
    cart_id: str = Field(
        ...,
        validation_alias=AliasChoices("cartId", "cart_id"),
        serialization_alias="cartId",
    )
    status: CheckoutStatus
    items: List[CheckoutItemSnapshot] = Field(default_factory=list)
    address: Optional[CheckoutAddressSnapshot] = None
    subtotal: Decimal = Field(default=Decimal("0.00"))
    discount: Decimal = Field(default=Decimal("0.00"))
    delivery_fee: Decimal = Field(
        default=Decimal("0.00"),
        validation_alias=AliasChoices("deliveryFee", "delivery_fee"),
        serialization_alias="deliveryFee",
    )
    tax: Decimal = Field(default=Decimal("0.00"))
    total: Decimal = Field(default=Decimal("0.00"))
    currency: str = "INR"
    coupon: Optional[CouponSummary] = None
    delivery_method: str = Field(
        "STANDARD",
        validation_alias=AliasChoices("deliveryMethod", "delivery_method"),
        serialization_alias="deliveryMethod",
    )
    delivery_slot: Optional[str] = Field(
        None,
        validation_alias=AliasChoices("deliverySlot", "delivery_slot"),
        serialization_alias="deliverySlot",
    )
    expires_at: datetime = Field(
        ...,
        validation_alias=AliasChoices("expiresAt", "expires_at"),
        serialization_alias="expiresAt",
    )
    price_changed: bool = Field(
        default=False,
        validation_alias=AliasChoices("priceChanged", "price_changed"),
        serialization_alias="priceChanged",
    )
    warning_message: Optional[str] = Field(
        None,
        validation_alias=AliasChoices("warningMessage", "warning_message"),
        serialization_alias="warningMessage",
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


class CheckoutConfirmResponse(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    checkout_status: str = Field(
        default="READY_FOR_ORDER",
        validation_alias=AliasChoices("checkoutStatus", "checkout_status"),
        serialization_alias="checkoutStatus",
    )
    checkout_session_id: str = Field(
        ...,
        validation_alias=AliasChoices("checkoutSessionId", "checkout_session_id"),
        serialization_alias="checkoutSessionId",
    )
    summary: CheckoutSummaryResponse
    message: str = "Checkout confirmed and ready for order placement."
