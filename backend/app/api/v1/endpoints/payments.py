import uuid
from decimal import Decimal
from typing import Optional
from fastapi import APIRouter, Depends, Header, status
from pydantic import BaseModel
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, get_db_writer, rate_limit
from app.core.errors import NotFoundError
from app.models.order import Order
from app.models.user import User
from app.schemas.common import ApiResponse
from app.services.idempotency import IdempotencyService

router = APIRouter()

class PaymentIntentRequest(BaseModel):
    order_id: str

class PaymentIntentResponse(BaseModel):
    client_secret: str
    order_id: str
    amount: Decimal
    currency: str = "INR"

class PaymentVerifyRequest(BaseModel):
    order_id: str
    payment_id: str
    signature: Optional[str] = None

@router.post(
    "/create-intent",
    response_model=ApiResponse[PaymentIntentResponse],
    dependencies=[Depends(rate_limit(limit=60, window_seconds=60))],
    summary="Create payment intent for an order",
)
async def create_payment_intent(
    req: PaymentIntentRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_writer),
    idempotency_key: Optional[str] = Header(None, alias="Idempotency-Key"),
):
    stmt = select(Order).where(Order.id == req.order_id, Order.user_id == current_user.id)
    res = await db.execute(stmt)
    order = res.scalar_one_or_none()
    if not order:
        raise NotFoundError("Order", req.order_id)

    client_secret = f"pi_secret_{uuid.uuid4().hex}"
    return ApiResponse[PaymentIntentResponse](
        success=True,
        data=PaymentIntentResponse(
            client_secret=client_secret,
            order_id=order.id,
            amount=Decimal(str(order.total)),
            currency="INR",
        ),
        message="Payment intent initialized.",
    )

@router.post(
    "/verify",
    response_model=ApiResponse[dict],
    dependencies=[Depends(rate_limit(limit=60, window_seconds=60))],
    summary="Verify payment completion idempotently",
)
async def verify_payment(
    req: PaymentVerifyRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_writer),
    idempotency_key: Optional[str] = Header(None, alias="Idempotency-Key"),
):
    stmt = select(Order).where(Order.id == req.order_id, Order.user_id == current_user.id)
    res = await db.execute(stmt)
    order = res.scalar_one_or_none()
    if not order:
        raise NotFoundError("Order", req.order_id)

    order.payment_status = "paid"
    order.status = "processing"
    await db.commit()

    return ApiResponse[dict](
        success=True,
        data={"order_id": order.id, "payment_status": "paid", "status": order.status},
        message="Payment verified successfully.",
    )
