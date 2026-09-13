"""
Cartify Checkout API Endpoints (Module 9)

Authenticated customer checkout endpoints:
- GET /api/v1/checkout: Retrieve current user's active checkout session
- POST /api/v1/checkout/preview: Generate or update authoritative checkout preview
- POST /api/v1/checkout/confirm: Confirm checkout with idempotency key protection (READY_FOR_ORDER)
- DELETE /api/v1/checkout/{checkout_session_id}: Cancel an active checkout session
"""

from typing import Optional
from fastapi import APIRouter, Body, Depends, Header, Path, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import (
    get_current_active_user,
    get_db_reader,
    get_db_writer,
    rate_limit,
)
from app.models.user import User
from app.schemas.checkout import (
    CheckoutConfirmRequest,
    CheckoutConfirmResponse,
    CheckoutPreviewRequest,
    CheckoutSummaryResponse,
)
from app.schemas.common import ApiResponse
from app.services.checkout_service import CheckoutService

router = APIRouter(prefix="/checkout", tags=["Checkout"])


@router.get(
    "",
    response_model=ApiResponse[CheckoutSummaryResponse],
    dependencies=[Depends(rate_limit(limit=180, window_seconds=60))],
    summary="Get active checkout session",
)
async def get_active_checkout(
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db_reader),
) -> ApiResponse[CheckoutSummaryResponse]:
    """
    Retrieves the customer's current active checkout session.
    Returns 404 if no session is active or if the session has expired.
    """
    session_summary = await CheckoutService.get_active_session(
        db=db, user_id=current_user.id
    )
    return ApiResponse[CheckoutSummaryResponse](
        success=True,
        data=session_summary,
        message="Active checkout session retrieved successfully.",
    )


@router.post(
    "/preview",
    response_model=ApiResponse[CheckoutSummaryResponse],
    status_code=status.HTTP_200_OK,
    dependencies=[Depends(rate_limit(limit=120, window_seconds=60))],
    summary="Generate or update checkout preview",
)
async def preview_checkout(
    preview_data: Optional[CheckoutPreviewRequest] = Body(default=None),
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db_writer),
) -> ApiResponse[CheckoutSummaryResponse]:
    """
    Generates or refreshes an authoritative checkout preview for the customer:
    - Verifies non-empty cart and item availability
    - Computes current variant prices & warns if prices changed
    - Validates address ownership
    - Re-validates applied coupon against order minimums
    - Authoritative server-side delivery fee calculation (₹0 above ₹499)
    - Returns or extends active CheckoutSession (30-min window)
    """
    summary = await CheckoutService.preview_checkout(
        db=db,
        user_id=current_user.id,
        preview_data=preview_data or CheckoutPreviewRequest(),
    )
    return ApiResponse[CheckoutSummaryResponse](
        success=True,
        data=summary,
        message="Checkout preview generated successfully.",
    )


@router.post(
    "/confirm",
    response_model=ApiResponse[CheckoutConfirmResponse],
    status_code=status.HTTP_200_OK,
    dependencies=[Depends(rate_limit(limit=60, window_seconds=60))],
    summary="Confirm checkout and ready for order",
)
async def confirm_checkout(
    confirm_data: CheckoutConfirmRequest,
    idempotency_key: Optional[str] = Header(None, alias="Idempotency-Key"),
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db_writer),
) -> ApiResponse[CheckoutConfirmResponse]:
    """
    Confirms an active checkout session with Idempotency-Key support:
    - Enforces delivery address selection
    - Re-checks non-empty cart
    - Transitions session status to COMPLETED
    - Returns READY_FOR_ORDER status for handoff to Module 10 (Orders)
    """
    result = await CheckoutService.confirm_checkout(
        db=db,
        user_id=current_user.id,
        confirm_data=confirm_data,
        idempotency_key=idempotency_key,
    )
    return ApiResponse[CheckoutConfirmResponse](
        success=True,
        data=result,
        message=result.message,
    )


@router.delete(
    "/{checkout_session_id}",
    response_model=ApiResponse[dict],
    dependencies=[Depends(rate_limit(limit=60, window_seconds=60))],
    summary="Cancel checkout session",
)
async def cancel_checkout(
    checkout_session_id: str = Path(..., description="UUID of checkout session to cancel"),
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db_writer),
) -> ApiResponse[dict]:
    """
    Cancels an active checkout session.
    """
    await CheckoutService.cancel_checkout(
        db=db,
        checkout_session_id=checkout_session_id,
        user_id=current_user.id,
    )
    return ApiResponse[dict](
        success=True,
        data={"cancelled": True, "checkoutSessionId": checkout_session_id},
        message="Checkout session cancelled successfully.",
    )
