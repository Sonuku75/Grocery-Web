"""
Cartify Admin Products API (Module 4)

Admin-only endpoints for managing products, variants, and gallery images:
- Strict role-based access control via require_admin
- Full product CRUD with mass-assignment protection
- Variant management with SKU collision enforcement and price/MRP validation
- Image management with single primary invariant enforcement
"""

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db_writer, require_admin
from app.models.user import User
from app.schemas.common import ApiResponse
from app.schemas.product import (
    ProductCreate,
    ProductDetailResponse,
    ProductStatusUpdate,
    ProductUpdate,
)
from app.schemas.product_image import (
    ProductImageCreate,
    ProductImageResponse,
    ProductImageUpdate,
)
from app.schemas.product_variant import (
    ProductVariantCreate,
    ProductVariantResponse,
    ProductVariantStatusUpdate,
    ProductVariantUpdate,
)
from app.services.product_service import ProductService

router = APIRouter(prefix="/admin/products", tags=["Admin Products"])


# -----------------------------------------------------------------------------
# Product Endpoints
# -----------------------------------------------------------------------------

@router.post(
    "",
    response_model=ApiResponse[ProductDetailResponse],
    status_code=status.HTTP_201_CREATED,
    summary="Create a new product (Admin)",
)
async def create_product(
    data: ProductCreate,
    db: AsyncSession = Depends(get_db_writer),
    current_admin: User = Depends(require_admin),
) -> ApiResponse[ProductDetailResponse]:
    """Creates a new catalog product with optional initial variants and gallery images."""
    product = await ProductService.create_product(db=db, data=data)
    return ApiResponse[ProductDetailResponse](
        success=True,
        data=product,
        message="Product created successfully.",
    )


@router.patch(
    "/{product_id}",
    response_model=ApiResponse[ProductDetailResponse],
    summary="Update product details (Admin)",
)
async def update_product(
    product_id: str,
    data: ProductUpdate,
    db: AsyncSession = Depends(get_db_writer),
    current_admin: User = Depends(require_admin),
) -> ApiResponse[ProductDetailResponse]:
    """Updates product fields with mass-assignment protection."""
    product = await ProductService.update_product(db=db, product_id=product_id, data=data)
    return ApiResponse[ProductDetailResponse](
        success=True,
        data=product,
        message="Product updated successfully.",
    )


@router.patch(
    "/{product_id}/status",
    response_model=ApiResponse[ProductDetailResponse],
    summary="Activate or deactivate a product (Admin)",
)
async def update_product_status(
    product_id: str,
    data: ProductStatusUpdate,
    db: AsyncSession = Depends(get_db_writer),
    current_admin: User = Depends(require_admin),
) -> ApiResponse[ProductDetailResponse]:
    """Toggles active/inactive visibility status of a product."""
    product = await ProductService.update_product_status(
        db=db,
        product_id=product_id,
        is_active=data.is_active,
    )
    return ApiResponse[ProductDetailResponse](
        success=True,
        data=product,
        message="Product status updated successfully.",
    )


# -----------------------------------------------------------------------------
# Variant Endpoints
# -----------------------------------------------------------------------------

@router.post(
    "/{product_id}/variants",
    response_model=ApiResponse[ProductVariantResponse],
    status_code=status.HTTP_201_CREATED,
    summary="Add a variant to a product (Admin)",
)
async def create_variant(
    product_id: str,
    data: ProductVariantCreate,
    db: AsyncSession = Depends(get_db_writer),
    current_admin: User = Depends(require_admin),
) -> ApiResponse[ProductVariantResponse]:
    """Adds a new purchasable variant (SKU, pricing, unit) to an existing product."""
    variant = await ProductService.create_variant(db=db, product_id=product_id, data=data)
    return ApiResponse[ProductVariantResponse](
        success=True,
        data=variant,
        message="Variant added successfully.",
    )


@router.patch(
    "/{product_id}/variants/{variant_id}",
    response_model=ApiResponse[ProductVariantResponse],
    summary="Update variant details (Admin)",
)
async def update_variant(
    product_id: str,
    variant_id: str,
    data: ProductVariantUpdate,
    db: AsyncSession = Depends(get_db_writer),
    current_admin: User = Depends(require_admin),
) -> ApiResponse[ProductVariantResponse]:
    """Updates variant price, MRP, unit, or SKU."""
    variant = await ProductService.update_variant(
        db=db,
        product_id=product_id,
        variant_id=variant_id,
        data=data,
    )
    return ApiResponse[ProductVariantResponse](
        success=True,
        data=variant,
        message="Variant updated successfully.",
    )


@router.patch(
    "/{product_id}/variants/{variant_id}/status",
    response_model=ApiResponse[ProductVariantResponse],
    summary="Activate or deactivate a variant (Admin)",
)
async def update_variant_status(
    product_id: str,
    variant_id: str,
    data: ProductVariantStatusUpdate,
    db: AsyncSession = Depends(get_db_writer),
    current_admin: User = Depends(require_admin),
) -> ApiResponse[ProductVariantResponse]:
    """Toggles variant active state."""
    variant = await ProductService.update_variant_status(
        db=db,
        product_id=product_id,
        variant_id=variant_id,
        is_active=data.is_active,
    )
    return ApiResponse[ProductVariantResponse](
        success=True,
        data=variant,
        message="Variant status updated successfully.",
    )


# -----------------------------------------------------------------------------
# Image Endpoints
# -----------------------------------------------------------------------------

@router.post(
    "/{product_id}/images",
    response_model=ApiResponse[ProductImageResponse],
    status_code=status.HTTP_201_CREATED,
    summary="Add an image to a product (Admin)",
)
async def add_image(
    product_id: str,
    data: ProductImageCreate,
    db: AsyncSession = Depends(get_db_writer),
    current_admin: User = Depends(require_admin),
) -> ApiResponse[ProductImageResponse]:
    """Adds a new gallery image. If marked primary, unsets previous primary."""
    image = await ProductService.add_image(db=db, product_id=product_id, data=data)
    return ApiResponse[ProductImageResponse](
        success=True,
        data=image,
        message="Image added successfully.",
    )


@router.patch(
    "/{product_id}/images/{image_id}",
    response_model=ApiResponse[ProductImageResponse],
    summary="Update image metadata (Admin)",
)
async def update_image(
    product_id: str,
    image_id: str,
    data: ProductImageUpdate,
    db: AsyncSession = Depends(get_db_writer),
    current_admin: User = Depends(require_admin),
) -> ApiResponse[ProductImageResponse]:
    """Updates image attributes."""
    image = await ProductService.update_image(
        db=db,
        product_id=product_id,
        image_id=image_id,
        data=data,
    )
    return ApiResponse[ProductImageResponse](
        success=True,
        data=image,
        message="Image updated successfully.",
    )


@router.patch(
    "/{product_id}/images/{image_id}/primary",
    response_model=ApiResponse[ProductImageResponse],
    summary="Set image as primary (Admin)",
)
async def set_primary_image(
    product_id: str,
    image_id: str,
    db: AsyncSession = Depends(get_db_writer),
    current_admin: User = Depends(require_admin),
) -> ApiResponse[ProductImageResponse]:
    """Atomically sets this image as the sole primary image for the product."""
    image = await ProductService.set_primary_image(
        db=db,
        product_id=product_id,
        image_id=image_id,
    )
    return ApiResponse[ProductImageResponse](
        success=True,
        data=image,
        message="Primary image updated successfully.",
    )


@router.delete(
    "/{product_id}/images/{image_id}",
    response_model=ApiResponse[dict],
    summary="Delete a product image (Admin)",
)
async def delete_image(
    product_id: str,
    image_id: str,
    db: AsyncSession = Depends(get_db_writer),
    current_admin: User = Depends(require_admin),
) -> ApiResponse[dict]:
    """Removes an image and reassigns primary image if needed."""
    await ProductService.delete_image(db=db, product_id=product_id, image_id=image_id)
    return ApiResponse[dict](
        success=True,
        data={"deleted": True, "imageId": image_id},
        message="Image deleted successfully.",
    )
