from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, get_db_reader, get_db_writer, rate_limit
from app.models.user import User
from app.schemas.cart import CartItemBase, CartResponse
from app.schemas.common import ApiResponse
from app.services.cart_service import CartService

router = APIRouter()

@router.get(
    "",
    response_model=ApiResponse[CartResponse],
    dependencies=[Depends(rate_limit(limit=200, window_seconds=60))],
    summary="Get user cart",
)
async def get_cart(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_reader),
):
    cart = await CartService.get_cart(db=db, user_id=current_user.id)
    return ApiResponse[CartResponse](
        success=True,
        data=cart,
        message="Cart retrieved.",
    )

@router.post(
    "/items",
    response_model=ApiResponse[CartResponse],
    status_code=status.HTTP_200_OK,
    summary="Add item to cart",
)
async def add_cart_item(
    item: CartItemBase,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_writer),
):
    cart = await CartService.add_item(
        db=db,
        user_id=current_user.id,
        product_id=item.product_id,
        quantity=item.quantity,
    )
    return ApiResponse[CartResponse](
        success=True,
        data=cart,
        message="Item added to cart.",
    )

@router.patch(
    "/items/{product_id}",
    response_model=ApiResponse[CartResponse],
    summary="Update cart item quantity",
)
async def update_cart_item_quantity(
    product_id: str,
    item: CartItemBase,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_writer),
):
    cart = await CartService.update_quantity(
        db=db,
        user_id=current_user.id,
        product_id=product_id,
        quantity=item.quantity,
    )
    return ApiResponse[CartResponse](
        success=True,
        data=cart,
        message="Cart quantity updated.",
    )

@router.delete(
    "/items/{product_id}",
    response_model=ApiResponse[CartResponse],
    summary="Remove item from cart",
)
async def remove_cart_item(
    product_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_writer),
):
    cart = await CartService.remove_item(
        db=db,
        user_id=current_user.id,
        product_id=product_id,
    )
    return ApiResponse[CartResponse](
        success=True,
        data=cart,
        message="Item removed from cart.",
    )

@router.delete(
    "",
    response_model=ApiResponse[None],
    summary="Clear entire cart",
)
async def clear_cart(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_writer),
):
    await CartService.clear_cart(db=db, user_id=current_user.id)
    return ApiResponse[None](
        success=True,
        data=None,
        message="Cart cleared.",
    )
