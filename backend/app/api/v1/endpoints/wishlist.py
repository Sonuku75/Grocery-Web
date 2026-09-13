"""
Cartify Wishlist API Endpoints (Module 6)

Authenticated customer wishlist endpoints:
- GET /api/v1/wishlist: Paginated wishlist items for authenticated customer
- POST /api/v1/wishlist/items: Add product to authenticated customer's wishlist
- DELETE /api/v1/wishlist/items/{product_id}: Remove product from customer's wishlist
- GET /api/v1/wishlist/check/{product_id}: Lightweight status check for product cards
"""

from typing import Optional
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import (
    get_current_active_user,
    get_db_reader,
    get_db_writer,
    rate_limit,
)
from app.models.user import User
from app.schemas.common import ApiResponse
from app.schemas.wishlist import (
    WishlistCheckResponse,
    WishlistItemCreate,
    WishlistItemResponse,
    WishlistRemoveResponse,
    WishlistResponse,
)
from app.services.wishlist_service import WishlistService

router = APIRouter(prefix="/wishlist", tags=["Wishlist"])


@router.get(
    "",
    response_model=ApiResponse[WishlistResponse],
    dependencies=[Depends(rate_limit(limit=180, window_seconds=60))],
    summary="Get authenticated customer's wishlist",
)
async def get_wishlist(
    cursor: Optional[str] = Query(None, description="Keyset pagination cursor"),
    limit: int = Query(default=20, ge=1, le=50, description="Items per page"),
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db_reader),
) -> ApiResponse[WishlistResponse]:
    """
    Returns keyset-paginated wishlist items belonging to the current user.
    Strictly isolated to the authenticated user ID.
    """
    result = await WishlistService.get_user_wishlist(
        db=db,
        user_id=current_user.id,
        limit=limit,
        cursor=cursor,
    )
    return ApiResponse[WishlistResponse](
        success=True,
        data=result,
        message="Wishlist retrieved successfully.",
    )


@router.post(
    "/items",
    response_model=ApiResponse[WishlistItemResponse],
    dependencies=[Depends(rate_limit(limit=120, window_seconds=60))],
    summary="Add product to customer's wishlist",
)
async def add_to_wishlist(
    payload: WishlistItemCreate,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db_writer),
) -> ApiResponse[WishlistItemResponse]:
    """
    Adds a product to the authenticated user's wishlist.
    Duplicate additions are handled gracefully without 500 errors.
    """
    result = await WishlistService.add_item(
        db=db,
        user_id=current_user.id,
        product_id=payload.product_id,
    )
    return ApiResponse[WishlistItemResponse](
        success=True,
        data=result,
        message="Product added to wishlist.",
    )


@router.delete(
    "/items/{product_id}",
    response_model=ApiResponse[WishlistRemoveResponse],
    dependencies=[Depends(rate_limit(limit=120, window_seconds=60))],
    summary="Remove product from customer's wishlist",
)
async def remove_from_wishlist(
    product_id: str,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db_writer),
) -> ApiResponse[WishlistRemoveResponse]:
    """
    Removes a product from the authenticated user's wishlist.
    Scoped strictly to the current user.
    """
    result = await WishlistService.remove_item(
        db=db,
        user_id=current_user.id,
        product_id=product_id,
    )
    return ApiResponse[WishlistRemoveResponse](
        success=True,
        data=result,
        message=result.message,
    )


@router.get(
    "/check/{product_id}",
    response_model=ApiResponse[WishlistCheckResponse],
    dependencies=[Depends(rate_limit(limit=300, window_seconds=60))],
    summary="Check if a product is in customer's wishlist",
)
async def check_wishlist_item(
    product_id: str,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db_reader),
) -> ApiResponse[WishlistCheckResponse]:
    """
    Lightweight check to determine if product_id is in current user's wishlist.
    Used by ProductCard and ProductDetail components without downloading entire list.
    """
    result = await WishlistService.check_item(
        db=db,
        user_id=current_user.id,
        product_id=product_id,
    )
    return ApiResponse[WishlistCheckResponse](
        success=True,
        data=result,
        message="Wishlist status checked.",
    )
