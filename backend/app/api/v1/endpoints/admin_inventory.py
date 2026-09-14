"""
Cartify Admin Inventory API (Module 11)

Admin-only endpoints for managing stock, reservations, and audit history:
- Strict role-based access control via require_admin
- Inventory initialization, thresholds updates, and signed stock adjustments
- Comprehensive catalog inventory listing with low-stock and out-of-stock filters
- Immutable transaction audit log tracking
"""

from typing import List, Optional
from fastapi import APIRouter, Body, Depends, Path, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import (
    get_db_reader,
    get_db_writer,
    rate_limit,
    require_admin,
)
from app.models.user import User
from app.schemas.common import ApiResponse
from app.schemas.inventory import (
    AdminAdjustStockRequest,
    AdminCreateInventoryRequest,
    AdminInventoryListResponse,
    AdminInventoryResponse,
    AdminUpdateInventoryRequest,
    InventoryTransactionResponse,
)
from app.services.inventory_service import InventoryService

router = APIRouter(prefix="/admin/inventory", tags=["Admin Inventory"])


@router.get(
    "",
    response_model=ApiResponse[AdminInventoryListResponse],
    dependencies=[Depends(rate_limit(limit=120, window_seconds=60))],
    summary="Admin list catalog inventory",
)
async def admin_list_inventory(
    variant_id: Optional[str] = Query(None, description="Filter by variant UUID"),
    product_id: Optional[str] = Query(None, description="Filter by product UUID"),
    low_stock: Optional[bool] = Query(None, description="Filter for variants with low stock"),
    out_of_stock: Optional[bool] = Query(None, description="Filter for out-of-stock variants"),
    is_active: Optional[bool] = Query(None, description="Filter by active status"),
    limit: int = Query(50, ge=1, le=100, description="Items per page"),
    offset: int = Query(0, ge=0, description="Pagination offset"),
    admin_user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db_reader),
) -> ApiResponse[AdminInventoryListResponse]:
    """
    Lists catalog inventory with multi-criteria filtering and pagination.
    """
    result = await InventoryService.admin_list_inventory(
        db=db,
        variant_id=variant_id,
        product_id=product_id,
        low_stock=low_stock,
        out_of_stock=out_of_stock,
        is_active=is_active,
        limit=limit,
        offset=offset,
    )
    return ApiResponse[AdminInventoryListResponse](
        success=True,
        data=result,
        message="Inventory records retrieved successfully.",
    )


@router.get(
    "/{variant_id}",
    response_model=ApiResponse[AdminInventoryResponse],
    dependencies=[Depends(rate_limit(limit=120, window_seconds=60))],
    summary="Admin get variant inventory details",
)
async def admin_get_inventory(
    variant_id: str = Path(..., description="Variant UUID"),
    admin_user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db_reader),
) -> ApiResponse[AdminInventoryResponse]:
    """
    Retrieves full operational inventory metrics for a variant.
    """
    inv = await InventoryService.admin_get_inventory(db, variant_id)
    return ApiResponse[AdminInventoryResponse](
        success=True,
        data=inv,
        message="Variant inventory details retrieved successfully.",
    )


@router.post(
    "",
    response_model=ApiResponse[AdminInventoryResponse],
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(rate_limit(limit=60, window_seconds=60))],
    summary="Admin initialize inventory for a variant",
)
async def admin_create_inventory(
    create_in: AdminCreateInventoryRequest = Body(...),
    admin_user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db_writer),
) -> ApiResponse[AdminInventoryResponse]:
    """
    Initializes a new inventory row for a variant with initial stock and thresholds.
    """
    inv = await InventoryService.admin_create_inventory(db, create_in, admin_user)
    return ApiResponse[AdminInventoryResponse](
        success=True,
        data=inv,
        message=f"Inventory initialized successfully for variant '{create_in.variant_id}'.",
    )


@router.patch(
    "/{variant_id}",
    response_model=ApiResponse[AdminInventoryResponse],
    dependencies=[Depends(rate_limit(limit=60, window_seconds=60))],
    summary="Admin update variant inventory settings",
)
async def admin_update_inventory(
    variant_id: str = Path(..., description="Variant UUID"),
    update_in: AdminUpdateInventoryRequest = Body(...),
    admin_user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db_writer),
) -> ApiResponse[AdminInventoryResponse]:
    """
    Updates low stock threshold and/or active state for a variant.
    """
    inv = await InventoryService.admin_update_inventory(db, variant_id, update_in, admin_user)
    return ApiResponse[AdminInventoryResponse](
        success=True,
        data=inv,
        message=f"Inventory settings updated for variant '{variant_id}'.",
    )


@router.post(
    "/{variant_id}/adjust",
    response_model=ApiResponse[AdminInventoryResponse],
    dependencies=[Depends(rate_limit(limit=60, window_seconds=60))],
    summary="Admin adjust stock with audit reason",
)
async def admin_adjust_stock(
    variant_id: str = Path(..., description="Variant UUID"),
    adjust_in: AdminAdjustStockRequest = Body(...),
    admin_user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db_writer),
) -> ApiResponse[AdminInventoryResponse]:
    """
    Adjusts stock (positive or negative) with row-locking and writes an audit transaction.
    """
    inv = await InventoryService.admin_adjust_stock(db, variant_id, adjust_in, admin_user)
    return ApiResponse[AdminInventoryResponse](
        success=True,
        data=inv,
        message=f"Stock adjusted by {adjust_in.quantity_change:+d}. New available stock is {inv.available_quantity}.",
    )


@router.get(
    "/{variant_id}/transactions",
    response_model=ApiResponse[List[InventoryTransactionResponse]],
    dependencies=[Depends(rate_limit(limit=120, window_seconds=60))],
    summary="Admin list inventory audit transactions for variant",
)
async def admin_list_transactions(
    variant_id: str = Path(..., description="Variant UUID"),
    limit: int = Query(50, ge=1, le=100, description="Items per page"),
    offset: int = Query(0, ge=0, description="Pagination offset"),
    admin_user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db_reader),
) -> ApiResponse[List[InventoryTransactionResponse]]:
    """
    Lists audit log transactions for a variant ordered newest first.
    """
    txs = await InventoryService.admin_list_transactions(db, variant_id=variant_id, limit=limit, offset=offset)
    return ApiResponse[List[InventoryTransactionResponse]](
        success=True,
        data=txs,
        message="Inventory transactions retrieved successfully.",
    )
