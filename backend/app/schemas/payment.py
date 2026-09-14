"""
Cartify Payment Schemas (Module 12)

Pydantic v2 schemas for payment initiation, verification, administrative listing,
and refund processing with dual camelCase and snake_case alias support.
"""

from datetime import datetime
from decimal import Decimal
from typing import Any, Dict, List, Optional
from pydantic import AliasChoices, BaseModel, ConfigDict, Field

from app.models.payment import (
    PaymentMethod,
    PaymentProviderType,
    PaymentStatus,
    RefundStatus,
)


class InitiatePaymentRequest(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    order_id: str = Field(
        ...,
        validation_alias=AliasChoices("orderId", "order_id"),
        serialization_alias="orderId",
        description="UUID of the order to pay for",
    )
    payment_method: PaymentMethod = Field(
        PaymentMethod.UPI,
        validation_alias=AliasChoices("paymentMethod", "payment_method", "method"),
        serialization_alias="paymentMethod",
    )
    provider: Optional[str] = Field(
        None,
        validation_alias=AliasChoices("provider", "paymentProvider"),
        serialization_alias="provider",
    )


class InitiatePaymentResponse(BaseModel):
    model_config = ConfigDict(populate_by_name=True, from_attributes=True)

    payment_id: str = Field(
        ...,
        validation_alias=AliasChoices("paymentId", "payment_id"),
        serialization_alias="paymentId",
    )
    order_id: str = Field(
        ...,
        validation_alias=AliasChoices("orderId", "order_id"),
        serialization_alias="orderId",
    )
    amount: Decimal
    currency: str = "INR"
    provider: str
    provider_order_id: Optional[str] = Field(
        None,
        validation_alias=AliasChoices("providerOrderId", "provider_order_id"),
        serialization_alias="providerOrderId",
    )
    payment_method: str = Field(
        ...,
        validation_alias=AliasChoices("paymentMethod", "payment_method"),
        serialization_alias="paymentMethod",
    )
    status: PaymentStatus
    client_secret: Optional[str] = Field(
        None,
        validation_alias=AliasChoices("clientSecret", "client_secret"),
        serialization_alias="clientSecret",
    )
    gateway_data: Optional[Dict[str, Any]] = Field(
        None,
        validation_alias=AliasChoices("gatewayData", "gateway_data"),
        serialization_alias="gatewayData",
    )


class VerifyPaymentRequest(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    payment_id: str = Field(
        ...,
        validation_alias=AliasChoices("paymentId", "payment_id"),
        serialization_alias="paymentId",
    )
    provider_payment_id: Optional[str] = Field(
        None,
        validation_alias=AliasChoices(
            "providerPaymentId",
            "provider_payment_id",
            "razorpay_payment_id",
            "razorpayPaymentId",
        ),
        serialization_alias="providerPaymentId",
    )
    provider_order_id: Optional[str] = Field(
        None,
        validation_alias=AliasChoices(
            "providerOrderId",
            "provider_order_id",
            "razorpay_order_id",
            "razorpayOrderId",
        ),
        serialization_alias="providerOrderId",
    )
    provider_signature: Optional[str] = Field(
        None,
        validation_alias=AliasChoices(
            "providerSignature",
            "provider_signature",
            "signature",
            "razorpay_signature",
            "razorpaySignature",
        ),
        serialization_alias="providerSignature",
    )


class PaymentStatusHistoryResponse(BaseModel):
    model_config = ConfigDict(populate_by_name=True, from_attributes=True)

    id: str
    payment_id: str = Field(
        ...,
        validation_alias=AliasChoices("paymentId", "payment_id"),
        serialization_alias="paymentId",
    )
    old_status: Optional[str] = Field(
        None,
        validation_alias=AliasChoices("oldStatus", "old_status"),
        serialization_alias="oldStatus",
    )
    new_status: str = Field(
        ...,
        validation_alias=AliasChoices("newStatus", "new_status"),
        serialization_alias="newStatus",
    )
    reason: Optional[str] = None
    created_at: datetime = Field(
        ...,
        validation_alias=AliasChoices("createdAt", "created_at"),
        serialization_alias="createdAt",
    )


class PaymentRefundResponse(BaseModel):
    model_config = ConfigDict(populate_by_name=True, from_attributes=True)

    id: str
    payment_id: str = Field(
        ...,
        validation_alias=AliasChoices("paymentId", "payment_id"),
        serialization_alias="paymentId",
    )
    provider_refund_id: Optional[str] = Field(
        None,
        validation_alias=AliasChoices("providerRefundId", "provider_refund_id"),
        serialization_alias="providerRefundId",
    )
    amount: Decimal
    currency: str = "INR"
    reason: Optional[str] = None
    status: RefundStatus
    created_at: datetime = Field(
        ...,
        validation_alias=AliasChoices("createdAt", "created_at"),
        serialization_alias="createdAt",
    )


class PaymentResponse(BaseModel):
    model_config = ConfigDict(populate_by_name=True, from_attributes=True)

    id: str
    order_id: str = Field(
        ...,
        validation_alias=AliasChoices("orderId", "order_id"),
        serialization_alias="orderId",
    )
    user_id: str = Field(
        ...,
        validation_alias=AliasChoices("userId", "user_id"),
        serialization_alias="userId",
    )
    provider: str
    provider_payment_id: Optional[str] = Field(
        None,
        validation_alias=AliasChoices("providerPaymentId", "provider_payment_id"),
        serialization_alias="providerPaymentId",
    )
    provider_order_id: Optional[str] = Field(
        None,
        validation_alias=AliasChoices("providerOrderId", "provider_order_id"),
        serialization_alias="providerOrderId",
    )
    payment_method: str = Field(
        ...,
        validation_alias=AliasChoices("paymentMethod", "payment_method"),
        serialization_alias="paymentMethod",
    )
    amount: Decimal
    currency: str = "INR"
    status: PaymentStatus
    failure_code: Optional[str] = Field(
        None,
        validation_alias=AliasChoices("failureCode", "failure_code"),
        serialization_alias="failureCode",
    )
    failure_message: Optional[str] = Field(
        None,
        validation_alias=AliasChoices("failureMessage", "failure_message"),
        serialization_alias="failureMessage",
    )
    paid_at: Optional[datetime] = Field(
        None,
        validation_alias=AliasChoices("paidAt", "paid_at"),
        serialization_alias="paidAt",
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


class AdminPaymentResponse(PaymentResponse):
    model_config = ConfigDict(populate_by_name=True, from_attributes=True)

    refundable_amount: Decimal = Field(
        Decimal("0.00"),
        validation_alias=AliasChoices("refundableAmount", "refundable_amount"),
        serialization_alias="refundableAmount",
    )
    status_history: List[PaymentStatusHistoryResponse] = Field(
        default_factory=list,
        validation_alias=AliasChoices("statusHistory", "status_history"),
        serialization_alias="statusHistory",
    )
    refunds: List[PaymentRefundResponse] = Field(
        default_factory=list,
        validation_alias=AliasChoices("refunds", "refund_list"),
        serialization_alias="refunds",
    )


class AdminPaymentListResponse(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    items: List[PaymentResponse]
    total: int
    page: int
    limit: int
    total_pages: int = Field(
        ...,
        validation_alias=AliasChoices("totalPages", "total_pages"),
        serialization_alias="totalPages",
    )


class CreateRefundRequest(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    amount: Decimal = Field(..., gt=Decimal("0.00"), description="Refund amount in payment currency")
    reason: Optional[str] = Field(None, max_length=255)


class RetryPaymentRequest(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    payment_method: Optional[PaymentMethod] = Field(
        None,
        validation_alias=AliasChoices("paymentMethod", "payment_method"),
        serialization_alias="paymentMethod",
    )
    provider: Optional[str] = None
