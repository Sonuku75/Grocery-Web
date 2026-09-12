"""
Cartify Category Endpoints (Module 3)

Customer-facing endpoints for browsing categories and subcategories:
- GET /api/v1/categories: List active top-level categories
- GET /api/v1/categories/slug/{slug}: Retrieve category by URL slug
- GET /api/v1/categories/{category_id}: Retrieve category by ID
- GET /api/v1/categories/{category_id}/subcategories: List direct active subcategories
"""

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import rate_limit
from app.core.database import get_db_reader
from app.schemas.category import CategoryListResponse, CategoryResponse
from app.schemas.common import ApiResponse
from app.services.category import CategoryService

router = APIRouter(prefix="/categories", tags=["Categories"])


@router.get(
    "",
    response_model=ApiResponse[CategoryListResponse],
    dependencies=[Depends(rate_limit(limit=300, window_seconds=60))],
    summary="List active top-level categories",
)
async def list_categories(
    include_subcategories: bool = Query(
        False,
        alias="includeSubcategories",
        description="Whether to nest active subcategories inside each top-level category",
    ),
    limit: int = Query(100, ge=1, le=200, description="Pagination limit"),
    skip: int = Query(0, ge=0, description="Pagination offset"),
    db: AsyncSession = Depends(get_db_reader),
) -> ApiResponse[CategoryListResponse]:
    """
    Returns active top-level categories ordered by sort_order ASC, name ASC.
    High-frequency customer calls are cached via Redis.
    """
    result = await CategoryService.list_categories(
        db=db,
        active_only=True,
        include_subcategories=include_subcategories,
        limit=limit,
        skip=skip,
    )
    return ApiResponse(
        success=True,
        message="Categories retrieved successfully.",
        data=result,
    )


@router.get(
    "/slug/{slug}",
    response_model=ApiResponse[CategoryResponse],
    dependencies=[Depends(rate_limit(limit=300, window_seconds=60))],
    summary="Get category by URL slug",
)
async def get_category_by_slug(
    slug: str,
    db: AsyncSession = Depends(get_db_reader),
) -> ApiResponse[CategoryResponse]:
    """
    Retrieves a category and its direct active subcategories using its URL-safe slug.
    Ideal for SEO, website routes, and mobile navigation.
    """
    category = await CategoryService.get_category_by_slug(db=db, slug=slug, active_only=True)
    return ApiResponse(
        success=True,
        message="Category retrieved successfully.",
        data=category,
    )


@router.get(
    "/{category_id}",
    response_model=ApiResponse[CategoryResponse],
    dependencies=[Depends(rate_limit(limit=300, window_seconds=60))],
    summary="Get category by ID",
)
async def get_category_by_id(
    category_id: str,
    db: AsyncSession = Depends(get_db_reader),
) -> ApiResponse[CategoryResponse]:
    """
    Retrieves category details and active direct subcategories by UUID.
    """
    category = await CategoryService.get_category_by_id(
        db=db, category_id=category_id, active_only=True
    )
    return ApiResponse(
        success=True,
        message="Category retrieved successfully.",
        data=category,
    )


@router.get(
    "/{category_id}/subcategories",
    response_model=ApiResponse[CategoryListResponse],
    dependencies=[Depends(rate_limit(limit=300, window_seconds=60))],
    summary="List direct subcategories for category",
)
async def list_subcategories(
    category_id: str,
    db: AsyncSession = Depends(get_db_reader),
) -> ApiResponse[CategoryListResponse]:
    """
    Returns active direct subcategories for a given category ID ordered by sort_order.
    """
    result = await CategoryService.list_subcategories(
        db=db, category_id=category_id, active_only=True
    )
    return ApiResponse(
        success=True,
        message="Subcategories retrieved successfully.",
        data=result,
    )
