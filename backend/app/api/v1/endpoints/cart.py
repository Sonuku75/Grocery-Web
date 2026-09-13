"""
Cartify Cart API Endpoints (Module 7)

Authenticated customer cart endpoints:
- GET /api/v1/cart: Get authenticated customer's cart with items and authoritative totals
- POST /api/v1/cart/items: Add product variant to cart (bounded quantity 1-99)
- PATCH /api/v1/cart/items/{cart_item_id}: Update cart item quantity
- DELETE /api/v1/cart/items/{cart_item_id}: Remove item from cart
- DELETE /api/v1/cart: Clear entire cart
"""

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import (
    get_current_active_user,
    get_db_reader,
    get_db_writer,
    rate_limit,
)
from app.models.user import User
from app.schemas.cart import (
    AddToCartRequest,
    CartClearResponse,
    CartResponse,
    UpdateCartItemRequest,
)
from app.schemas.common import ApiResponse
from app.schemas.coupon import CouponSummary, CouponValidateRequest, CouponValidateResponse
from app.services.cart_service import CartService
from app.services.coupon_service import CouponService

router = APIRouter(prefix="/cart", tags=["Cart"])



@router.get(
    "",
    response_model=ApiResponse[CartResponse],
    dependencies=[Depends(rate_limit(limit=180, window_seconds=60))],
    summary="Get user cart",
)
async def get_cart(
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db_reader),
) -> ApiResponse[CartResponse]:
    """
    Returns the authenticated user's shopping cart with all items,
    product metadata, variant details, and authoritative subtotal.
    """
    cart = await CartService.get_cart(db=db, user_id=current_user.id)
    return ApiResponse[CartResponse](
        success=True,
        data=cart,
        message="Cart retrieved successfully.",
    )


@router.post(
    "/items",
    response_model=ApiResponse[CartResponse],
    status_code=status.HTTP_200_OK,
    dependencies=[Depends(rate_limit(limit=120, window_seconds=60))],
    summary="Add item to cart",
)
async def add_cart_item(
    payload: AddToCartRequest,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db_writer),
) -> ApiResponse[CartResponse]:
    """
    Adds a product variant to the authenticated user's cart.
    Price is derived exclusively on the backend from the variant.
    """
    cart = await CartService.add_item(
        db=db,
        user_id=current_user.id,
        variant_id=payload.variant_id,
        quantity=payload.quantity,
        product_id=payload.product_id,
    )
    return ApiResponse[CartResponse](
        success=True,
        data=cart,
        message="Item added to cart.",
    )


@router.patch(
    "/items/{cart_item_id}",
    response_model=ApiResponse[CartResponse],
    dependencies=[Depends(rate_limit(limit=120, window_seconds=60))],
    summary="Update cart item quantity",
)
async def update_cart_item_quantity(
    cart_item_id: str,
    payload: UpdateCartItemRequest,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db_writer),
) -> ApiResponse[CartResponse]:
    """
    Updates the quantity of a specific cart item (1 to 99).
    Protected against IDOR: fails if item does not belong to authenticated user.
    """
    cart = await CartService.update_item_quantity(
        db=db,
        user_id=current_user.id,
        cart_item_id=cart_item_id,
        quantity=payload.quantity,
    )
    return ApiResponse[CartResponse](
        success=True,
        data=cart,
        message="Cart quantity updated.",
    )


@router.delete(
    "/items/{cart_item_id}",
    response_model=ApiResponse[CartResponse],
    dependencies=[Depends(rate_limit(limit=120, window_seconds=60))],
    summary="Remove item from cart",
)
async def remove_cart_item(
    cart_item_id: str,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db_writer),
) -> ApiResponse[CartResponse]:
    """
    Removes a single item from the authenticated user's cart.
    Protected against IDOR: fails if item does not belong to authenticated user.
    """
    cart = await CartService.remove_item(
        db=db,
        user_id=current_user.id,
        cart_item_id=cart_item_id,
    )
    return ApiResponse[CartResponse](
        success=True,
        data=cart,
        message="Item removed from cart.",
    )


@router.delete(
    "",
    response_model=ApiResponse[CartClearResponse],
    dependencies=[Depends(rate_limit(limit=60, window_seconds=60))],
    summary="Clear entire cart",
)
async def clear_cart(
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db_writer),
) -> ApiResponse[CartClearResponse]:
    """
    Removes all items from the authenticated user's cart.
    """
    result = await CartService.clear_cart(db=db, user_id=current_user.id)
    return ApiResponse[CartClearResponse](
        success=True,
        data=result,
        message="Cart cleared successfully.",
    )


@router.post(
    "/coupon/validate",
    response_model=ApiResponse[CouponValidateResponse],
    dependencies=[Depends(rate_limit(limit=60, window_seconds=60))],
    summary="Validate coupon against cart",
)
async def validate_cart_coupon(
    payload: CouponValidateRequest,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db_reader),
) -> ApiResponse[CouponValidateResponse]:
    """
    Validates a promo code against the user's current cart subtotal and user limits
    without applying it to the cart.
    """
    cart = await CartService.get_cart(db=db, user_id=current_user.id)
    is_valid, msg, coupon, discount = await CouponService.validate_coupon(
        db=db,
        code_or_coupon=payload.code,
        subtotal=cart.subtotal,
        user_id=current_user.id,
    )
    coupon_summary = CouponSummary.model_validate(coupon) if coupon else None
    return ApiResponse[CouponValidateResponse](
        success=True,
        data=CouponValidateResponse(
            valid=is_valid,
            code=payload.code,
            discount=discount,
            message=msg,
            coupon=coupon_summary,
        ),
        message=msg,
    )


@router.post(
    "/coupon",
    response_model=ApiResponse[CartResponse],
    dependencies=[Depends(rate_limit(limit=60, window_seconds=60))],
    summary="Apply coupon to cart",
)
async def apply_cart_coupon(
    payload: CouponValidateRequest,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db_writer),
) -> ApiResponse[CartResponse]:
    """
    Validates and applies a coupon to the authenticated user's cart,
    recalculating authoritative discounts and total.
    """
    cart = await CartService.apply_coupon(
        db=db,
        user_id=current_user.id,
        code=payload.code,
    )
    return ApiResponse[CartResponse](
        success=True,
        data=cart,
        message=f"Coupon '{payload.code}' applied successfully.",
    )


@router.delete(
    "/coupon",
    response_model=ApiResponse[CartResponse],
    dependencies=[Depends(rate_limit(limit=60, window_seconds=60))],
    summary="Remove coupon from cart",
)
async def remove_cart_coupon(
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db_writer),
) -> ApiResponse[CartResponse]:
    """
    Removes currently applied coupon from the user's cart.
    """
    cart = await CartService.remove_coupon(
        db=db,
        user_id=current_user.id,
    )
    return ApiResponse[CartResponse](
        success=True,
        data=cart,
        message="Coupon removed from cart.",
    )

