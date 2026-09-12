"""
Cartify Public Products API (Module 4)

Public customer-facing product endpoints:
- GET /api/v1/products: Keyset cursor paginated listing with brand/category/featured filters
- GET /api/v1/products/{product_id}: Detailed product info by UUID
- GET /api/v1/products/slug/{slug}: SEO-friendly product details by slug
"""

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db_reader, rate_limit
from app.schemas.common import ApiResponse
from app.schemas.product import (
    ProductDetailResponse,
    ProductFilterParams,
    ProductListResponse,
)
from app.services.product_service import ProductService

router = APIRouter(prefix="/products", tags=["Products"])


@router.get(
    "",
    response_model=ApiResponse[ProductListResponse],
    dependencies=[Depends(rate_limit(limit=300, window_seconds=60))],
    summary="List active products with filters and keyset cursor pagination",
)
async def list_products(
    filters: ProductFilterParams = Depends(),
    db: AsyncSession = Depends(get_db_reader),
) -> ApiResponse[ProductListResponse]:
    """
    Returns active products visible to customers.
    High performance keyset cursor pagination and whitelisted sorting.
    """
    result = await ProductService.list_products(db=db, filters=filters, active_only=True)
    return ApiResponse[ProductListResponse](
        success=True,
        data=result,
        message="Products retrieved successfully.",
    )


@router.get(
    "/slug/{slug}",
    response_model=ApiResponse[ProductDetailResponse],
    dependencies=[Depends(rate_limit(limit=500, window_seconds=60))],
    summary="Get active product details by URL slug",
)
async def get_product_by_slug(
    slug: str,
    db: AsyncSession = Depends(get_db_reader),
) -> ApiResponse[ProductDetailResponse]:
    """
    Retrieves full product detail including category, active variants, and images by slug.
    Backed by Redis cache-aside.
    """
    product = await ProductService.get_by_slug(db=db, slug=slug, active_only=True)
    return ApiResponse[ProductDetailResponse](
        success=True,
        data=product,
        message="Product details retrieved.",
    )


@router.get(
    "/{product_id}",
    response_model=ApiResponse[ProductDetailResponse],
    dependencies=[Depends(rate_limit(limit=500, window_seconds=60))],
    summary="Get active product details by product ID",
)
async def get_product_by_id(
    product_id: str,
    db: AsyncSession = Depends(get_db_reader),
) -> ApiResponse[ProductDetailResponse]:
    """
    Retrieves full product detail including category, active variants, and images by ID.
    Backed by Redis cache-aside.
    """
    product = await ProductService.get_by_id(db=db, product_id=product_id, active_only=True)
    return ApiResponse[ProductDetailResponse](
        success=True,
        data=product,
        message="Product details retrieved.",
    )
