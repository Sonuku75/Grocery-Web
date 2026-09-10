from typing import List, Optional
from fastapi import APIRouter, Depends, Header, Response, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, get_db_reader, get_db_writer, rate_limit
from app.models.user import User
from app.schemas.common import ApiResponse
from app.schemas.order import OrderCreate, OrderResponse
from app.services.idempotency import IdempotencyService
from app.services.order_service import OrderService

router = APIRouter()

@router.post(
    "",
    response_model=ApiResponse[OrderResponse],
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(rate_limit(limit=60, window_seconds=60))],
    summary="Create order with idempotency protection and atomic stock decrement",
)
async def create_order(
    data: OrderCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_writer),
    idempotency_key: Optional[str] = Header(None, alias="Idempotency-Key"),
):
    """
    High-concurrency order creation.
    Protected by:
    1. Distributed Redis Idempotency Lock
    2. Deterministic Row-Level Locks (Deadlock-Free)
    3. Non-negative Check Constraint in PostgreSQL
    """
    if idempotency_key:
        acquired, cached = await IdempotencyService.acquire_lock(idempotency_key)
        if not acquired and cached:
            return ApiResponse[OrderResponse](
                success=True,
                data=OrderResponse(**cached),
                message="Order retrieved from idempotency cache.",
            )

    try:
        order = await OrderService.create_order(
            db=db,
            user_id=current_user.id,
            data=data,
            idempotency_key=idempotency_key,
        )

        if idempotency_key:
            await IdempotencyService.save_result(
                idempotency_key,
                status.HTTP_201_CREATED,
                order.model_dump(),
            )

        return ApiResponse[OrderResponse](
            success=True,
            data=order,
            message="Order placed successfully.",
        )
    except Exception:
        if idempotency_key:
            await IdempotencyService.release_lock(idempotency_key)
        raise

@router.get(
    "",
    response_model=ApiResponse[List[OrderResponse]],
    dependencies=[Depends(rate_limit(limit=120, window_seconds=60))],
    summary="Get user order history",
)
async def get_my_orders(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_reader),
):
    orders = await OrderService.get_user_orders(db=db, user_id=current_user.id)
    return ApiResponse[List[OrderResponse]](
        success=True,
        data=orders,
        message="Order history retrieved.",
    )

@router.get(
    "/{order_id}",
    response_model=ApiResponse[OrderResponse],
    dependencies=[Depends(rate_limit(limit=120, window_seconds=60))],
    summary="Get order details by ID",
)
async def get_order_detail(
    order_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_reader),
):
    order = await OrderService.get_order_by_id(db=db, order_id=order_id, user_id=current_user.id)
    return ApiResponse[OrderResponse](
        success=True,
        data=order,
        message="Order details retrieved.",
    )
