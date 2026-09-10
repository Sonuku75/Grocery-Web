from typing import List
from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db_reader, get_db_writer, rate_limit
from app.schemas.category import CategoryCreate, CategoryResponse
from app.schemas.common import ApiResponse
from app.services.category_service import CategoryService

router = APIRouter()

@router.get(
    "",
    response_model=ApiResponse[List[CategoryResponse]],
    dependencies=[Depends(rate_limit(limit=300, window_seconds=60))],
    summary="Get all active categories",
)
async def list_categories(
    db: AsyncSession = Depends(get_db_reader),
):
    categories = await CategoryService.get_all_categories(db=db)
    return ApiResponse[List[CategoryResponse]](
        success=True,
        data=categories,
        message="Categories retrieved successfully.",
    )

@router.get(
    "/{slug}",
    response_model=ApiResponse[CategoryResponse],
    dependencies=[Depends(rate_limit(limit=300, window_seconds=60))],
    summary="Get category by slug",
)
async def get_category(
    slug: str,
    db: AsyncSession = Depends(get_db_reader),
):
    category = await CategoryService.get_by_slug(db=db, slug=slug)
    return ApiResponse[CategoryResponse](
        success=True,
        data=category,
        message="Category retrieved.",
    )

@router.post(
    "",
    response_model=ApiResponse[dict],
    status_code=status.HTTP_201_CREATED,
    summary="Create category",
)
async def create_category(
    data: CategoryCreate,
    db: AsyncSession = Depends(get_db_writer),
):
    cat = await CategoryService.create_category(db=db, data=data)
    return ApiResponse[dict](
        success=True,
        data={"id": cat.id, "slug": cat.slug},
        message="Category created successfully.",
    )
