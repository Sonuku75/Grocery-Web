"""
Cartify Order Schemas (Module 10)

Pydantic schemas for order creation, detail views, and administrative lifecycle management:
- Dual camelCase and snake_case alias support across Web, iOS, and Android
- Authoritative purchase-time snapshots for items, prices, address, and coupons
- State machine representations and audit history tracking
"""

from datetime import datetime
from decimal import Decimal
from typing import List, Optional
from pydantic import AliasChoices, BaseModel, ConfigDict, Field

from app.models.order import FulfillmentStatus, OrderStatus, PaymentStatus


class OrderItemResponse(BaseModel):
    model_config = ConfigDict(populate_by_name=True, from_attributes=True)

    id: str
    product_id: Optional[str] = Field(
        None,
        validation_alias=AliasChoices("productId", "product_id"),
        serialization_alias="productId",
    )
    variant_id: Optional[str] = Field(
        None,
        validation_alias=AliasChoices("variantId", "variant_id"),
        serialization_alias="variantId",
    )
    product_name: str = Field(
        ...,
        validation_alias=AliasChoices("productName", "product_name", "title", "name"),
        serialization_alias="productName",
    )
    variant_name: Optional[str] = Field(
        None,
        validation_alias=AliasChoices("variantName", "variant_name"),
        serialization_alias="variantName",
    )
    sku: Optional[str] = None
    unit_value: Optional[str] = Field(
        None,
        validation_alias=AliasChoices("unitValue", "unit_value"),
        serialization_alias="unitValue",
    )
    unit_type: Optional[str] = Field(
        None,
        validation_alias=AliasChoices("unitType", "unit_type"),
        serialization_alias="unitType",
    )
    unit_price: Decimal = Field(
        ...,
        validation_alias=AliasChoices("unitPrice", "unit_price", "price"),
        serialization_alias="unitPrice",
    )
    mrp: Optional[Decimal] = None
    quantity: int
    discount_amount: Decimal = Field(
        default=Decimal("0.00"),
        validation_alias=AliasChoices("discountAmount", "discount_amount"),
        serialization_alias="discountAmount",
    )
    line_total: Decimal = Field(
        ...,
        validation_alias=AliasChoices("lineTotal", "line_total"),
        serialization_alias="lineTotal",
    )
    thumbnail_url: Optional[str] = Field(
        None,
        validation_alias=AliasChoices("thumbnailUrl", "thumbnail_url", "imageUrl", "image_url"),
        serialization_alias="thumbnailUrl",
    )
    created_at: Optional[datetime] = Field(
        None,
        validation_alias=AliasChoices("createdAt", "created_at"),
        serialization_alias="createdAt",
    )


class OrderAddressSnapshot(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

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
    address_label: Optional[str] = Field(
        "Home",
        validation_alias=AliasChoices("addressLabel", "address_label", "label"),
        serialization_alias="addressLabel",
    )
    latitude: Optional[float] = None
    longitude: Optional[float] = None


class OrderStatusHistoryResponse(BaseModel):
    model_config = ConfigDict(populate_by_name=True, from_attributes=True)

    id: str
    order_id: str = Field(
        ...,
        validation_alias=AliasChoices("orderId", "order_id"),
        serialization_alias="orderId",
    )
    old_status: Optional[str] = Field(
        None,
        validation_alias=AliasChoices("oldStatus", "old_status", "fromStatus", "from_status"),
        serialization_alias="oldStatus",
    )
    new_status: str = Field(
        ...,
        validation_alias=AliasChoices("newStatus", "new_status", "toStatus", "to_status"),
        serialization_alias="newStatus",
    )
    changed_by_user_id: Optional[str] = Field(
        None,
        validation_alias=AliasChoices("changedByUserId", "changed_by_user_id"),
        serialization_alias="changedByUserId",
    )
    reason: Optional[str] = None
    created_at: datetime = Field(
        ...,
        validation_alias=AliasChoices("createdAt", "created_at"),
        serialization_alias="createdAt",
    )


class CreateOrderRequest(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    checkout_session_id: str = Field(
        ...,
        validation_alias=AliasChoices("checkoutSessionId", "checkout_session_id", "sessionId", "session_id"),
        serialization_alias="checkoutSessionId",
        description="UUID of confirmed checkout session",
    )
    notes: Optional[str] = Field(None, max_length=500)


class OrderSummaryResponse(BaseModel):
    model_config = ConfigDict(populate_by_name=True, from_attributes=True)

    id: str
    order_number: str = Field(
        ...,
        validation_alias=AliasChoices("orderNumber", "order_number"),
        serialization_alias="orderNumber",
    )
    status: OrderStatus
    payment_status: PaymentStatus = Field(
        ...,
        validation_alias=AliasChoices("paymentStatus", "payment_status"),
        serialization_alias="paymentStatus",
    )
    fulfillment_status: FulfillmentStatus = Field(
        default=FulfillmentStatus.UNFULFILLED,
        validation_alias=AliasChoices("fulfillmentStatus", "fulfillment_status"),
        serialization_alias="fulfillmentStatus",
    )
    currency: str = "INR"
    subtotal: Decimal = Field(
        default=Decimal("0.00"),
        validation_alias=AliasChoices("subtotal", "subtotalAmount", "subtotal_amount"),
        serialization_alias="subtotalAmount",
    )
    discount_amount: Decimal = Field(
        default=Decimal("0.00"),
        validation_alias=AliasChoices("discountAmount", "discount_amount", "discount"),
        serialization_alias="discountAmount",
    )
    delivery_fee: Decimal = Field(
        default=Decimal("0.00"),
        validation_alias=AliasChoices("deliveryFee", "delivery_fee"),
        serialization_alias="deliveryFee",
    )
    total_amount: Decimal = Field(
        ...,
        validation_alias=AliasChoices("totalAmount", "total_amount", "total"),
        serialization_alias="totalAmount",
    )
    item_count: int = Field(
        default=0,
        validation_alias=AliasChoices("itemCount", "item_count"),
        serialization_alias="itemCount",
    )
    first_item_title: Optional[str] = Field(
        None,
        validation_alias=AliasChoices("firstItemTitle", "first_item_title"),
        serialization_alias="firstItemTitle",
    )
    first_item_thumbnail: Optional[str] = Field(
        None,
        validation_alias=AliasChoices("firstItemThumbnail", "first_item_thumbnail"),
        serialization_alias="firstItemThumbnail",
    )
    delivery_slot: Optional[str] = Field(
        None,
        validation_alias=AliasChoices("deliverySlot", "delivery_slot"),
        serialization_alias="deliverySlot",
    )
    created_at: datetime = Field(
        ...,
        validation_alias=AliasChoices("createdAt", "created_at"),
        serialization_alias="createdAt",
    )


class OrderDetailResponse(BaseModel):
    model_config = ConfigDict(populate_by_name=True, from_attributes=True)

    id: str
    order_number: str = Field(
        ...,
        validation_alias=AliasChoices("orderNumber", "order_number"),
        serialization_alias="orderNumber",
    )
    user_id: str = Field(
        ...,
        validation_alias=AliasChoices("userId", "user_id"),
        serialization_alias="userId",
    )
    status: OrderStatus
    payment_status: PaymentStatus = Field(
        ...,
        validation_alias=AliasChoices("paymentStatus", "payment_status"),
        serialization_alias="paymentStatus",
    )
    fulfillment_status: FulfillmentStatus = Field(
        ...,
        validation_alias=AliasChoices("fulfillmentStatus", "fulfillment_status"),
        serialization_alias="fulfillmentStatus",
    )
    currency: str = "INR"
    subtotal: Decimal = Field(
        ...,
        validation_alias=AliasChoices("subtotal", "subtotalAmount", "subtotal_amount"),
        serialization_alias="subtotalAmount",
    )
    discount_amount: Decimal = Field(
        default=Decimal("0.00"),
        validation_alias=AliasChoices("discountAmount", "discount_amount", "discount"),
        serialization_alias="discountAmount",
    )
    delivery_fee: Decimal = Field(
        default=Decimal("0.00"),
        validation_alias=AliasChoices("deliveryFee", "delivery_fee"),
        serialization_alias="deliveryFee",
    )
    tax_amount: Decimal = Field(
        default=Decimal("0.00"),
        validation_alias=AliasChoices("taxAmount", "tax_amount", "tax"),
        serialization_alias="taxAmount",
    )
    total_amount: Decimal = Field(
        ...,
        validation_alias=AliasChoices("totalAmount", "total_amount", "total"),
        serialization_alias="totalAmount",
    )
    coupon_code: Optional[str] = Field(
        None,
        validation_alias=AliasChoices("couponCode", "coupon_code"),
        serialization_alias="couponCode",
    )
    coupon_discount_amount: Decimal = Field(
        default=Decimal("0.00"),
        validation_alias=AliasChoices("couponDiscountAmount", "coupon_discount_amount"),
        serialization_alias="couponDiscountAmount",
    )
    address: OrderAddressSnapshot = Field(
        ...,
        validation_alias=AliasChoices("address", "addressSnapshot", "address_snapshot"),
        serialization_alias="addressSnapshot",
    )
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
    notes: Optional[str] = None
    checkout_session_id: Optional[str] = Field(
        None,
        validation_alias=AliasChoices("checkoutSessionId", "checkout_session_id"),
        serialization_alias="checkoutSessionId",
    )
    items: List[OrderItemResponse] = Field(default_factory=list)
    status_history: List[OrderStatusHistoryResponse] = Field(
        default_factory=list,
        validation_alias=AliasChoices("statusHistory", "status_history"),
        serialization_alias="statusHistory",
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


class OrderListResponse(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    items: List[OrderSummaryResponse] = Field(default_factory=list)
    total: int
    limit: int
    offset: int


class CancelOrderRequest(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    reason: Optional[str] = Field("Cancelled by customer", max_length=255)


class AdminUpdateOrderStatusRequest(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    status: OrderStatus
    fulfillment_status: Optional[FulfillmentStatus] = Field(
        None,
        validation_alias=AliasChoices("fulfillmentStatus", "fulfillment_status"),
        serialization_alias="fulfillmentStatus",
    )
    reason: Optional[str] = Field(None, max_length=255)
