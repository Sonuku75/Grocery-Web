"""
Cartify Customer Coupons API Endpoints (Module 8)

Customer-facing coupons endpoints:
- GET /api/v1/coupons: List active, valid, public coupons with pagination
"""

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db_reader, rate_limit
from app.schemas.common import ApiResponse
from app.schemas.coupon import CouponListResponse
from app.services.coupon_service import CouponService

router = APIRouter(prefix="/coupons", tags=["Coupons"])


@router.get(
    "",
    response_model=ApiResponse[CouponListResponse],
    dependencies=[Depends(rate_limit(limit=120, window_seconds=60))],
    summary="List available public coupons",
)
async def list_public_coupons(
    limit: int = Query(50, ge=1, le=100, description="Page limit"),
    offset: int = Query(0, ge=0, description="Page offset"),
    db: AsyncSession = Depends(get_db_reader),
) -> ApiResponse[CouponListResponse]:
    """
    Returns active, unexpired coupons currently available for customers.
    """
    coupons = await CouponService.get_public_coupons(db=db, limit=limit, offset=offset)
    return ApiResponse[CouponListResponse](
        success=True,
        data=coupons,
        message="Available coupons retrieved successfully.",
    )
