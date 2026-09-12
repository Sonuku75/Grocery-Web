"""
Cartify Admin Category Endpoints (Module 3)

Administrative endpoints for category lifecycle management:
- POST /api/v1/admin/categories: Create a new category / subcategory
- PATCH /api/v1/admin/categories/{category_id}: Update category details
- DELETE /api/v1/admin/categories/{category_id}: Deactivate or safe hard-delete
Protected strictly by require_admin dependency.
"""

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import require_admin
from app.core.database import get_db_writer
from app.models.user import User
from app.schemas.category import (
    CategoryCreateRequest,
    CategoryResponse,
    CategoryUpdateRequest,
)
from app.schemas.common import ApiResponse
from app.services.category import CategoryService

router = APIRouter(prefix="/admin/categories", tags=["Admin - Categories"])


@router.post(
    "",
    response_model=ApiResponse[CategoryResponse],
    status_code=status.HTTP_201_CREATED,
    summary="Create category (Admin)",
)
async def create_category(
    payload: CategoryCreateRequest,
    current_admin: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db_writer),
) -> ApiResponse[CategoryResponse]:
    """
    Creates a new category or subcategory with unique slug generation and parent validation.
    Restricted strictly to administrators.
    """
    category = await CategoryService.create_category(db=db, data=payload)
    return ApiResponse(
        success=True,
        message="Category created successfully.",
        data=category,
    )


@router.patch(
    "/{category_id}",
    response_model=ApiResponse[CategoryResponse],
    summary="Update category (Admin)",
)
async def update_category(
    category_id: str,
    payload: CategoryUpdateRequest,
    current_admin: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db_writer),
) -> ApiResponse[CategoryResponse]:
    """
    Updates category properties (name, description, image, parent, sort order, active status).
    Validates against self-parenting and circular hierarchy.
    """
    updated = await CategoryService.update_category(
        db=db, category_id=category_id, data=payload
    )
    return ApiResponse(
        success=True,
        message="Category updated successfully.",
        data=updated,
    )


@router.delete(
    "/{category_id}",
    response_model=ApiResponse[dict],
    summary="Delete or deactivate category (Admin)",
)
async def delete_category(
    category_id: str,
    hard_delete: bool = Query(
        False,
        description="Whether to permanently remove the record or soft-deactivate (default: False)",
    ),
    current_admin: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db_writer),
) -> ApiResponse[dict]:
    """
    Deactivates or hard-deletes a category.
    Defaults to soft-deactivation (is_active=False) with cascaded child deactivation.
    Hard deletion is rejected if dependent subcategories exist.
    """
    result = await CategoryService.delete_category(
        db=db, category_id=category_id, hard_delete=hard_delete
    )
    return ApiResponse(
        success=True,
        message=result.get("message", "Category processed successfully."),
        data=result,
    )
