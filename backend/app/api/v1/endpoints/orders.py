"""
Cartify Orders API Endpoints (Module 10)

Authenticated customer order endpoints:
- POST /api/v1/orders: Create order from checkout session (with Idempotency-Key support)
- GET /api/v1/orders: List authenticated customer's orders (paginated)
- GET /api/v1/orders/{order_id}: Get single order detail by UUID or order number (IDOR protected)
- POST /api/v1/orders/{order_id}/cancel: Cancel customer order (strictly permitted states)
"""

from typing import Optional
from fastapi import APIRouter, Body, Depends, Header, Path, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import (
    get_current_active_user,
    get_db_reader,
    get_db_writer,
    rate_limit,
)
from app.models.user import User
from app.schemas.common import ApiResponse
from app.schemas.order import (
    CancelOrderRequest,
    CreateOrderRequest,
    OrderDetailResponse,
    OrderListResponse,
)
from app.services.order_service import OrderService

router = APIRouter(prefix="/orders", tags=["Orders"])


@router.post(
    "",
    response_model=ApiResponse[OrderDetailResponse],
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(rate_limit(limit=60, window_seconds=60))],
    summary="Create order from checkout session",
)
async def create_order(
    create_in: CreateOrderRequest,
    idempotency_key: Optional[str] = Header(None, alias="Idempotency-Key"),
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db_writer),
) -> ApiResponse[OrderDetailResponse]:
    """
    Places an order from a verified checkout session:
    - Atomically captures purchase-time item, price, and address snapshots
    - Generates a unique human-friendly order number (CRT-YYYYMMDD-XXXXXX)
    - Clears purchased items from customer's cart
    - Transitions checkout session to COMPLETED
    - Deduplicates identical submissions via Idempotency-Key
    """
    order = await OrderService.create_order_from_checkout(
        db=db,
        user_id=current_user.id,
        create_in=create_in,
        idempotency_key=idempotency_key,
    )
    return ApiResponse[OrderDetailResponse](
        success=True,
        data=order,
        message="Order placed successfully.",
    )


@router.get(
    "",
    response_model=ApiResponse[OrderListResponse],
    dependencies=[Depends(rate_limit(limit=120, window_seconds=60))],
    summary="List customer orders",
)
async def list_orders(
    limit: int = Query(20, ge=1, le=100, description="Items per page"),
    offset: int = Query(0, ge=0, description="Pagination offset"),
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db_reader),
) -> ApiResponse[OrderListResponse]:
    """
    Lists orders placed by the authenticated customer, sorted newest first.
    """
    orders = await OrderService.list_orders(
        db=db,
        user_id=current_user.id,
        limit=limit,
        offset=offset,
    )
    return ApiResponse[OrderListResponse](
        success=True,
        data=orders,
        message="Orders retrieved successfully.",
    )


@router.get(
    "/{order_id}",
    response_model=ApiResponse[OrderDetailResponse],
    dependencies=[Depends(rate_limit(limit=180, window_seconds=60))],
    summary="Get order details",
)
async def get_order(
    order_id: str = Path(..., description="Internal UUID or public order_number"),
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db_reader),
) -> ApiResponse[OrderDetailResponse]:
    """
    Retrieves full details of an order owned by the authenticated customer.
    Guarantees horizontal isolation (cannot access another customer's order).
    """
    order = await OrderService.get_order(
        db=db,
        order_id_or_number=order_id,
        user_id=current_user.id,
    )
    return ApiResponse[OrderDetailResponse](
        success=True,
        data=order,
        message="Order details retrieved successfully.",
    )


@router.post(
    "/{order_id}/cancel",
    response_model=ApiResponse[OrderDetailResponse],
    dependencies=[Depends(rate_limit(limit=60, window_seconds=60))],
    summary="Cancel order",
)
async def cancel_order(
    order_id: str = Path(..., description="Internal UUID or public order_number"),
    cancel_in: Optional[CancelOrderRequest] = Body(default=None),
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db_writer),
) -> ApiResponse[OrderDetailResponse]:
    """
    Cancels an order owned by the authenticated customer:
    - Only permitted when order status is PENDING or CONFIRMED
    - Creates an immutable audit record in order_status_history
    """
    cancelled_order = await OrderService.cancel_order(
        db=db,
        order_id_or_number=order_id,
        user_id=current_user.id,
        cancel_in=cancel_in,
    )
    return ApiResponse[OrderDetailResponse](
        success=True,
        data=cancelled_order,
        message=f"Order #{cancelled_order.order_number} cancelled successfully.",
    )
