from typing import Optional
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db_reader, get_db_writer, rate_limit
from app.schemas.common import ApiResponse, CursorPage
from app.schemas.product import ProductCreate, ProductFilterParams, ProductResponse, ProductUpdate
from app.services.product_service import ProductService

router = APIRouter()

@router.get(
    "",
    response_model=ApiResponse[CursorPage[ProductResponse]],
    dependencies=[Depends(rate_limit(limit=300, window_seconds=60))],
    summary="List products with keyset cursor pagination and filters",
)
async def list_products(
    filters: ProductFilterParams = Depends(),
    db: AsyncSession = Depends(get_db_reader),
):
    """
    High-concurrency product listing.
    Serves from Redis Cache-Aside or PostgreSQL Read Replica.
    Uses keyset pagination (created_at, id) for O(1) performance at any page depth.
    """
    result = await ProductService.get_products_keyset(db=db, filters=filters)
    return ApiResponse[CursorPage[ProductResponse]](
        success=True,
        data=result,
        message="Products retrieved successfully.",
    )

@router.get(
    "/{identifier}",
    response_model=ApiResponse[ProductResponse],
    dependencies=[Depends(rate_limit(limit=500, window_seconds=60))],
    summary="Get single product by ID or slug",
)
async def get_product(
    identifier: str,
    db: AsyncSession = Depends(get_db_reader),
):
    """
    Retrieves a single product with stampede-protected Redis cache.
    """
    product = await ProductService.get_by_id_or_slug(db=db, identifier=identifier)
    return ApiResponse[ProductResponse](
        success=True,
        data=product,
        message="Product details retrieved.",
    )

@router.post(
    "",
    response_model=ApiResponse[dict],
    status_code=status.HTTP_201_CREATED,
    summary="Create a new product",
)
async def create_product(
    data: ProductCreate,
    db: AsyncSession = Depends(get_db_writer),
):
    """
    Creates product in PostgreSQL Primary and invalidates relevant caches.
    """
    product = await ProductService.create_product(db=db, data=data)
    return ApiResponse[dict](
        success=True,
        data={"id": product.id, "slug": product.slug},
        message="Product created successfully.",
    )

@router.patch(
    "/{product_id}",
    response_model=ApiResponse[dict],
    summary="Update product details or stock",
)
async def update_product(
    product_id: str,
    data: ProductUpdate,
    db: AsyncSession = Depends(get_db_writer),
):
    """
    Updates product in PostgreSQL Primary and clears cached entries.
    """
    product = await ProductService.update_product(db=db, product_id=product_id, data=data)
    return ApiResponse[dict](
        success=True,
        data={"id": product.id, "stock": product.stock, "in_stock": product.in_stock},
        message="Product updated successfully.",
    )
