"""
Cartify Search & Discovery API (Module 5)

Public search endpoints for Web, Android, and iOS:
- GET /api/v1/search: Relevance-ranked product catalog search with filters and pagination
- GET /api/v1/search/suggestions: Fast autocomplete suggestions for products, brands, and categories
"""

from decimal import Decimal
from typing import Literal, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db_reader, rate_limit
from app.schemas.common import ApiResponse
from app.schemas.search import (
    SearchFilterParams,
    SearchResponse,
    SearchSuggestionParams,
    SearchSuggestionResponse,
)
from app.services.search_service import SearchService

router = APIRouter(prefix="/search", tags=["Search"])


@router.get(
    "",
    response_model=ApiResponse[SearchResponse],
    dependencies=[Depends(rate_limit(limit=180, window_seconds=60))],
    summary="Search active products with relevance ranking, filters, and cursor pagination",
)
async def search_products(
    q: Optional[str] = Query(None, max_length=100, description="Search keyword"),
    category_id: Optional[str] = Query(None, description="Category or subcategory ID"),
    brand: Optional[str] = Query(None, max_length=100, description="Brand name"),
    min_price: Optional[Decimal] = Query(None, ge=0, description="Minimum price"),
    max_price: Optional[Decimal] = Query(None, ge=0, description="Maximum price"),
    sort: Literal["relevance", "price_low_to_high", "price_high_to_low", "newest", "featured"] = Query(
        "relevance", description="Sort option"
    ),
    cursor: Optional[str] = Query(None, description="Pagination cursor"),
    limit: int = Query(20, ge=1, le=50, description="Items per page"),
    db: AsyncSession = Depends(get_db_reader),
) -> ApiResponse[SearchResponse]:
    """
    Searches active grocery products across name, brand, category, and SKU.
    Supports category hierarchy filtering, brand filtering, min/max price range,
    whitelisted sorting, and keyset cursor pagination.
    """
    # Reject whitespace-only queries
    if q is not None:
        trimmed = q.strip()
        if not trimmed:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Search query cannot be empty or whitespace.",
            )
        q = trimmed

    # Validate price range
    if min_price is not None and max_price is not None and min_price > max_price:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="min_price cannot be greater than max_price.",
        )

    filters = SearchFilterParams(
        q=q,
        category_id=category_id,
        brand=brand,
        min_price=min_price,
        max_price=max_price,
        sort=sort,
        cursor=cursor,
        limit=limit,
    )
    result = await SearchService.search_products(db=db, filters=filters)
    return ApiResponse[SearchResponse](
        success=True,
        data=result,
        message="Search results retrieved successfully.",
    )


@router.get(
    "/suggestions",
    response_model=ApiResponse[SearchSuggestionResponse],
    dependencies=[Depends(rate_limit(limit=300, window_seconds=60))],
    summary="Get autocomplete suggestions for products, brands, and categories",
)
async def get_search_suggestions(
    q: str = Query(..., min_length=1, max_length=100, description="Search query prefix"),
    limit: int = Query(8, ge=1, le=20, description="Max suggestions to return"),
    db: AsyncSession = Depends(get_db_reader),
) -> ApiResponse[SearchSuggestionResponse]:
    """
    Fast autocomplete endpoint returning lightweight suggestions across products,
    brands, and categories. Backed by Redis cache-aside.
    """
    trimmed = q.strip()
    if not trimmed:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Query parameter 'q' cannot be empty or whitespace.",
        )

    params = SearchSuggestionParams(q=trimmed, limit=limit)
    result = await SearchService.get_suggestions(db=db, params=params)
    return ApiResponse[SearchSuggestionResponse](
        success=True,
        data=result,
        message="Suggestions retrieved successfully.",
    )
