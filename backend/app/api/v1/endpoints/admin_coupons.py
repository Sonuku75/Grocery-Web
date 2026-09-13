"""
Cartify Admin Coupons API Endpoints (Module 8)

Administrative endpoints for coupon lifecycle management:
- POST /api/v1/admin/coupons: Create new promotional coupon (Admin only)
- GET /api/v1/admin/coupons: List all coupons with filters (Admin only)
- PATCH /api/v1/admin/coupons/{coupon_id}: Update coupon status or attributes (Admin only)
"""

from typing import Any, Dict, List, Optional
from fastapi import APIRouter, Depends, Query, status
from pydantic import BaseModel, ConfigDict
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db_reader, get_db_writer, rate_limit, require_admin
from app.models.user import User
from app.schemas.common import ApiResponse
from app.schemas.coupon import (
    CouponCreateRequest,
    CouponDetailResponse,
    CouponUpdateRequest,
)
from app.services.coupon_service import CouponService

router = APIRouter(prefix="/admin/coupons", tags=["Admin Coupons"])


class AdminCouponListResponse(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    items: List[CouponDetailResponse]
    total: int


@router.post(
    "",
    response_model=ApiResponse[CouponDetailResponse],
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_admin), Depends(rate_limit(limit=60, window_seconds=60))],
    summary="Create coupon (Admin)",
)
async def create_coupon(
    payload: CouponCreateRequest,
    admin: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db_writer),
) -> ApiResponse[CouponDetailResponse]:
    """
    Creates a new promotional coupon code with defined discount rules and validity limits.
    """
    coupon = await CouponService.admin_create_coupon(db=db, coupon_in=payload)
    return ApiResponse[CouponDetailResponse](
        success=True,
        data=coupon,
        message=f"Coupon '{coupon.code}' created successfully.",
    )


@router.get(
    "",
    response_model=ApiResponse[AdminCouponListResponse],
    dependencies=[Depends(require_admin), Depends(rate_limit(limit=120, window_seconds=60))],
    summary="List all coupons (Admin)",
)
async def list_admin_coupons(
    is_active: Optional[bool] = Query(None, description="Filter by active state"),
    search: Optional[str] = Query(None, description="Search by coupon code or title"),
    limit: int = Query(50, ge=1, le=100, description="Page limit"),
    offset: int = Query(0, ge=0, description="Page offset"),
    admin: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db_reader),
) -> ApiResponse[AdminCouponListResponse]:
    """
    Lists all coupons across active, inactive, and expired statuses with usage stats.
    """
    items, total = await CouponService.admin_list_coupons(
        db=db,
        is_active=is_active,
        search=search,
        limit=limit,
        offset=offset,
    )
    return ApiResponse[AdminCouponListResponse](
        success=True,
        data=AdminCouponListResponse(items=items, total=total),
        message="Coupons retrieved successfully.",
    )


@router.patch(
    "/{coupon_id}",
    response_model=ApiResponse[CouponDetailResponse],
    dependencies=[Depends(require_admin), Depends(rate_limit(limit=60, window_seconds=60))],
    summary="Update coupon (Admin)",
)
async def update_coupon(
    coupon_id: str,
    payload: CouponUpdateRequest,
    admin: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db_writer),
) -> ApiResponse[CouponDetailResponse]:
    """
    Updates coupon parameters (name, dates, status, limits).
    """
    updated_coupon = await CouponService.admin_update_coupon(
        db=db,
        coupon_id=coupon_id,
        coupon_update=payload,
    )
    return ApiResponse[CouponDetailResponse](
        success=True,
        data=updated_coupon,
        message=f"Coupon '{updated_coupon.code}' updated successfully.",
    )
