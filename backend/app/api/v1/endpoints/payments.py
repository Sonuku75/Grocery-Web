"""
Cartify Payment Endpoints (Module 12)

Customer-facing payment initiation, status lookup, signature verification,
order payment retries, and inbound webhook ingestion.
"""

from typing import Optional
from fastapi import APIRouter, Depends, Header, Path, Query, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, get_db_reader, get_db_writer, rate_limit
from app.core.errors import ForbiddenError, NotFoundError, ValidationError
from app.models.payment import PaymentMethod
from app.models.user import User
from app.repositories.payment import PaymentRepository
from app.schemas.common import ApiResponse
from app.schemas.payment import (
    InitiatePaymentRequest,
    InitiatePaymentResponse,
    PaymentResponse,
    RetryPaymentRequest,
    VerifyPaymentRequest,
)
from app.services.payment_service import PaymentService

router = APIRouter(tags=["Payments"])


@router.post(
    "/payments",
    response_model=ApiResponse[InitiatePaymentResponse],
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(rate_limit(limit=60, window_seconds=60))],
    summary="Initiate payment for an order",
)
async def initiate_payment(
    req: InitiatePaymentRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_writer),
    idempotency_key: Optional[str] = Header(None, alias="Idempotency-Key"),
):
    """
    Initiates payment for an unfulfilled order using server-authoritative monetary derivation.
    Accepts payment method (UPI, CARD, NET_BANKING, WALLET, COD).
    """
    payment_res = await PaymentService.initiate_payment(
        db=db,
        user_id=current_user.id,
        req=req,
        idempotency_key=idempotency_key,
    )
    return ApiResponse[InitiatePaymentResponse](
        success=True,
        data=payment_res,
        message="Payment initiated successfully.",
    )


@router.get(
    "/payments/{payment_id}",
    response_model=ApiResponse[PaymentResponse],
    dependencies=[Depends(rate_limit(limit=120, window_seconds=60))],
    summary="Get payment details and verification status",
)
async def get_payment_status(
    payment_id: str = Path(..., description="UUID of payment"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_reader),
):
    """
    Retrieves current payment status with ownership enforcement.
    """
    payment = await PaymentRepository.get_by_id(db, payment_id)
    if not payment:
        raise NotFoundError("Payment", payment_id)

    if payment.user_id != current_user.id and current_user.role != "ADMIN":
        raise ForbiddenError("You do not have access to view this payment.")

    return ApiResponse[PaymentResponse](
        success=True,
        data=PaymentResponse.model_validate(payment),
        message="Payment details retrieved.",
    )


@router.post(
    "/payments/verify",
    response_model=ApiResponse[PaymentResponse],
    dependencies=[Depends(rate_limit(limit=60, window_seconds=60))],
    summary="Verify cryptographic payment signature",
)
async def verify_payment(
    req: VerifyPaymentRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_writer),
):
    """
    Verifies gateway signature and transitions payment and order status to PAID.
    """
    payment = await PaymentService.verify_payment(
        db=db,
        user_id=current_user.id,
        req=req,
    )
    return ApiResponse[PaymentResponse](
        success=True,
        data=PaymentResponse.model_validate(payment),
        message="Payment verified successfully.",
    )


@router.post(
    "/orders/{order_id}/payment/retry",
    response_model=ApiResponse[InitiatePaymentResponse],
    dependencies=[Depends(rate_limit(limit=30, window_seconds=60))],
    summary="Retry payment for an existing unpaid order",
)
async def retry_payment(
    order_id: str = Path(..., description="UUID of order to retry"),
    req: Optional[RetryPaymentRequest] = None,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_writer),
):
    """
    Cancels any previous active/pending payment attempt and issues a new payment challenge.
    """
    method = req.payment_method if req else None
    provider = req.provider if req else None

    payment_res = await PaymentService.retry_payment(
        db=db,
        user_id=current_user.id,
        order_id=order_id,
        payment_method=method,
        provider=provider,
    )
    return ApiResponse[InitiatePaymentResponse](
        success=True,
        data=payment_res,
        message="Payment retry initiated successfully.",
    )


@router.post(
    "/payments/webhooks/{provider}",
    response_model=ApiResponse[dict],
    summary="Inbound payment gateway webhook handler",
)
async def handle_payment_webhook(
    request: Request,
    provider: str = Path(..., description="Gateway provider identifier (mock, razorpay)"),
    db: AsyncSession = Depends(get_db_writer),
):
    """
    Ingests inbound gateway webhook events with raw body bytes verification and deduplication.
    """
    raw_body = await request.body()
    signature = (
        request.headers.get("X-Razorpay-Signature")
        or request.headers.get("X-Mock-Signature")
        or request.headers.get("signature")
        or request.headers.get("x-signature")
        or ""
    )

    result = await PaymentService.process_webhook(
        db=db,
        provider_name=provider,
        raw_body_bytes=raw_body,
        signature_header=signature,
    )

    return ApiResponse[dict](
        success=True,
        data=result,
        message="Webhook processed successfully.",
    )
