"""
Cartify Admin Orders API Endpoints (Module 10)

Admin-only endpoints for managing orders:
- Strict role-based access control via require_admin
- Search, filter, and pagination across all platform orders
- View complete order snapshot details
- Transition order lifecycle state with strict state machine validation and audit logging
"""

from typing import Optional
from fastapi import APIRouter, Body, Depends, Path, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import (
    get_db_reader,
    get_db_writer,
    rate_limit,
    require_admin,
)
from app.models.user import User
from app.schemas.common import ApiResponse
from app.schemas.order import (
    AdminUpdateOrderStatusRequest,
    OrderDetailResponse,
    OrderListResponse,
)
from app.services.order_service import OrderService

router = APIRouter(prefix="/admin/orders", tags=["Admin Orders"])


@router.get(
    "",
    response_model=ApiResponse[OrderListResponse],
    dependencies=[Depends(rate_limit(limit=120, window_seconds=60))],
    summary="Admin list orders",
)
async def admin_list_orders(
    status: Optional[str] = Query(None, description="Filter by OrderStatus"),
    search: Optional[str] = Query(None, description="Search by order number or recipient"),
    limit: int = Query(50, ge=1, le=100, description="Items per page"),
    offset: int = Query(0, ge=0, description="Pagination offset"),
    admin_user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db_reader),
) -> ApiResponse[OrderListResponse]:
    """
    Lists orders across all users with optional status filtering and search query.
    """
    orders = await OrderService.admin_list_orders(
        db=db,
        status=status,
        search=search,
        limit=limit,
        offset=offset,
    )
    return ApiResponse[OrderListResponse](
        success=True,
        data=orders,
        message="Admin orders retrieved successfully.",
    )


@router.get(
    "/{order_id}",
    response_model=ApiResponse[OrderDetailResponse],
    dependencies=[Depends(rate_limit(limit=120, window_seconds=60))],
    summary="Admin get order details",
)
async def admin_get_order(
    order_id: str = Path(..., description="Order ID or public order number"),
    admin_user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db_reader),
) -> ApiResponse[OrderDetailResponse]:
    """
    Retrieves complete snapshot and timeline details of any order across the platform.
    """
    order = await OrderService.admin_get_order(
        db=db,
        order_id_or_number=order_id,
    )
    return ApiResponse[OrderDetailResponse](
        success=True,
        data=order,
        message="Order details retrieved successfully.",
    )


@router.patch(
    "/{order_id}/status",
    response_model=ApiResponse[OrderDetailResponse],
    dependencies=[Depends(rate_limit(limit=60, window_seconds=60))],
    summary="Admin update order status",
)
async def admin_update_order_status(
    order_id: str = Path(..., description="Order ID or public order number"),
    update_in: AdminUpdateOrderStatusRequest = Body(...),
    admin_user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db_writer),
) -> ApiResponse[OrderDetailResponse]:
    """
    Transitions order lifecycle status adhering to the strict state machine:
    - Verifies allowed forward transitions
    - Automatically captures audit log in order_status_history
    """
    updated_order = await OrderService.admin_update_status(
        db=db,
        order_id_or_number=order_id,
        admin_user=admin_user,
        update_in=update_in,
    )
    return ApiResponse[OrderDetailResponse](
        success=True,
        data=updated_order,
        message=f"Order #{updated_order.order_number} status updated to {updated_order.status.value}.",
    )
