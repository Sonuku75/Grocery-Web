"""
Cartify Admin Payment Endpoints (Module 12)

Administrative auditing, payment detail inspection with audit trail, and refund issuance.
"""

from typing import Optional
from fastapi import APIRouter, Depends, Path, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db_reader, get_db_writer, require_admin
from app.core.errors import NotFoundError
from app.models.user import User
from app.repositories.payment import PaymentRepository
from app.schemas.common import ApiResponse
from app.schemas.payment import (
    AdminPaymentListResponse,
    AdminPaymentResponse,
    CreateRefundRequest,
    PaymentRefundResponse,
    PaymentResponse,
)
from app.services.refund_service import RefundService

router = APIRouter(prefix="/admin/payments", tags=["Admin Payments"])


@router.get(
    "",
    response_model=ApiResponse[AdminPaymentListResponse],
    summary="List all payments with filtering and pagination (Admin only)",
)
async def list_payments(
    page: int = Query(1, ge=1, description="Page number"),
    limit: int = Query(20, ge=1, le=100, description="Items per page"),
    status: Optional[str] = Query(None, description="Filter by status (PENDING, PAID, FAILED, REFUNDED, etc.)"),
    provider: Optional[str] = Query(None, description="Filter by provider (MOCK, RAZORPAY)"),
    payment_method: Optional[str] = Query(None, description="Filter by payment method (UPI, CARD, COD, etc.)"),
    order_id: Optional[str] = Query(None, description="Filter by order ID"),
    user_id: Optional[str] = Query(None, description="Filter by user ID"),
    current_admin: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db_reader),
):
    offset = (page - 1) * limit
    payments, total = await PaymentRepository.list_admin_payments(
        db=db,
        limit=limit,
        offset=offset,
        status=status,
        provider=provider,
        payment_method=payment_method,
        order_id=order_id,
        user_id=user_id,
    )
    total_pages = (total + limit - 1) // limit if total > 0 else 1

    return ApiResponse[AdminPaymentListResponse](
        success=True,
        data=AdminPaymentListResponse(
            items=[PaymentResponse.model_validate(p) for p in payments],
            total=total,
            page=page,
            limit=limit,
            total_pages=total_pages,
        ),
        message="Payments retrieved successfully.",
    )


@router.get(
    "/{payment_id}",
    response_model=ApiResponse[AdminPaymentResponse],
    summary="Get payment details with status history and refunds (Admin only)",
)
async def get_payment_details(
    payment_id: str = Path(..., description="UUID of payment"),
    current_admin: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db_reader),
):
    payment = await PaymentRepository.get_by_id(db, payment_id)
    if not payment:
        raise NotFoundError("Payment", payment_id)

    return ApiResponse[AdminPaymentResponse](
        success=True,
        data=AdminPaymentResponse.model_validate(payment),
        message="Admin payment details retrieved.",
    )


@router.post(
    "/{payment_id}/refund",
    response_model=ApiResponse[PaymentRefundResponse],
    status_code=status.HTTP_201_CREATED,
    summary="Initiate partial or full refund (Admin only)",
)
async def initiate_refund(
    req: CreateRefundRequest,
    payment_id: str = Path(..., description="UUID of payment to refund"),
    current_admin: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db_writer),
):
    refund = await RefundService.initiate_refund(
        db=db,
        payment_id=payment_id,
        amount=req.amount,
        reason=req.reason,
        admin_user=current_admin,
    )

    return ApiResponse[PaymentRefundResponse](
        success=True,
        data=PaymentRefundResponse.model_validate(refund),
        message="Refund initiated successfully.",
    )
