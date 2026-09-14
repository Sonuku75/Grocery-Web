"""
Cartify Admin Reviews API (Module 14)

Administrative review moderation endpoints:
- GET   /api/v1/admin/reviews: Paginated review moderation queue with status/product filters
- GET   /api/v1/admin/reviews/{review_id}: Full administrative review detail
- PATCH /api/v1/admin/reviews/{review_id}/status: State-machine compliant status transition
- POST  /api/v1/admin/reviews/{review_id}/hide: Hide review from public display
- POST  /api/v1/admin/reviews/{review_id}/restore: Restore hidden review to public display
- GET   /api/v1/admin/reviews/reports: Review abuse and moderation reports queue
"""

from typing import Optional
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db_reader, get_db_writer, require_admin
from app.core.errors import CartifyException
from app.models.review import ReviewStatus
from app.models.user import User
from app.repositories.review import ReviewRepository
from app.repositories.review_report import ReviewReportRepository
from app.schemas.common import ApiResponse
from app.schemas.review import (
    AdminReviewDetailResponse,
    AdminReviewStatusUpdateRequest,
    ReviewReportResponse,
)
from app.services.review_moderation_service import ReviewModerationService

router = APIRouter(prefix="/admin/reviews", tags=["Admin Reviews"])


@router.get(
    "",
    response_model=ApiResponse[dict],
    summary="List reviews for admin moderation",
)
async def admin_list_reviews(
    status: Optional[str] = Query(None, description="Filter by status: PENDING, PUBLISHED, REJECTED, HIDDEN, DELETED"),
    product_id: Optional[str] = Query(None, description="Filter by product ID"),
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    current_admin: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db_reader),
) -> ApiResponse[dict]:
    """
    Administrative listing of reviews across all lifecycle statuses.
    Requires ADMIN role.
    """
    items, total = await ReviewRepository.list_admin_reviews(
        db=db,
        status=status,
        product_id=product_id,
        limit=limit,
        offset=offset,
    )
    serialized = [
        AdminReviewDetailResponse(
            id=r.id,
            user_id=r.user_id,
            product_id=r.product_id,
            product_name=r.product.name if r.product else None,
            order_id=r.order_id,
            order_item_id=r.order_item_id,
            rating=r.rating,
            title=r.title,
            body=r.body,
            status=r.status,
            is_verified_purchase=r.is_verified_purchase,
            helpful_count=r.helpful_count,
            created_at=r.created_at,
            updated_at=r.updated_at,
            deleted_at=r.deleted_at,
        ).model_dump()
        for r in items
    ]
    return ApiResponse(
        success=True,
        data={"items": serialized, "total": total, "limit": limit, "offset": offset},
        message="Admin reviews retrieved successfully.",
    )


@router.get(
    "/{review_id}",
    response_model=ApiResponse[AdminReviewDetailResponse],
    summary="Get full review details for admin",
)
async def admin_get_review(
    review_id: str,
    current_admin: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db_reader),
) -> ApiResponse[AdminReviewDetailResponse]:
    """
    Retrieves complete review record including internal IDs and timestamps.
    """
    review = await ReviewRepository.get_by_id(db, review_id, include_deleted=True)
    if not review:
        raise CartifyException(
            status_code=404,
            message=f"Review with identifier '{review_id}' was not found.",
            code="REVIEW_NOT_FOUND",
        )

    return ApiResponse(
        success=True,
        data=AdminReviewDetailResponse(
            id=review.id,
            user_id=review.user_id,
            product_id=review.product_id,
            product_name=review.product.name if review.product else None,
            order_id=review.order_id,
            order_item_id=review.order_item_id,
            rating=review.rating,
            title=review.title,
            body=review.body,
            status=review.status,
            is_verified_purchase=review.is_verified_purchase,
            helpful_count=review.helpful_count,
            created_at=review.created_at,
            updated_at=review.updated_at,
            deleted_at=review.deleted_at,
        ),
        message="Review details retrieved.",
    )


@router.patch(
    "/{review_id}/status",
    response_model=ApiResponse[AdminReviewDetailResponse],
    summary="Moderate review status",
)
async def admin_update_review_status(
    review_id: str,
    payload: AdminReviewStatusUpdateRequest,
    current_admin: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db_writer),
) -> ApiResponse[AdminReviewDetailResponse]:
    """
    Transitions review status through the moderation state machine.
    Automatically triggers product rating recalculation and audit outbox emission.
    """
    review = await ReviewRepository.get_by_id(db, review_id, include_deleted=True)
    if not review:
        raise CartifyException(
            status_code=404,
            message=f"Review with identifier '{review_id}' was not found.",
            code="REVIEW_NOT_FOUND",
        )

    updated_review = await ReviewModerationService.transition_status(
        db=db,
        review=review,
        new_status=payload.status.value,
        admin_user_id=current_admin.id,
        reason=payload.reason,
    )
    await db.commit()

    return ApiResponse(
        success=True,
        data=AdminReviewDetailResponse(
            id=updated_review.id,
            user_id=updated_review.user_id,
            product_id=updated_review.product_id,
            product_name=updated_review.product.name if updated_review.product else None,
            order_id=updated_review.order_id,
            order_item_id=updated_review.order_item_id,
            rating=updated_review.rating,
            title=updated_review.title,
            body=updated_review.body,
            status=updated_review.status,
            is_verified_purchase=updated_review.is_verified_purchase,
            helpful_count=updated_review.helpful_count,
            created_at=updated_review.created_at,
            updated_at=updated_review.updated_at,
            deleted_at=updated_review.deleted_at,
        ),
        message=f"Review status transitioned to {updated_review.status}.",
    )


@router.post(
    "/{review_id}/hide",
    response_model=ApiResponse[AdminReviewDetailResponse],
    summary="Hide review from public",
)
async def admin_hide_review(
    review_id: str,
    reason: Optional[str] = Query(None, description="Reason for hiding review"),
    current_admin: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db_writer),
) -> ApiResponse[AdminReviewDetailResponse]:
    """
    Convenience action to hide a published review.
    """
    review = await ReviewRepository.get_by_id(db, review_id, include_deleted=False)
    if not review:
        raise CartifyException(
            status_code=404,
            message=f"Review with identifier '{review_id}' was not found.",
            code="REVIEW_NOT_FOUND",
        )

    updated_review = await ReviewModerationService.transition_status(
        db=db,
        review=review,
        new_status=ReviewStatus.HIDDEN.value,
        admin_user_id=current_admin.id,
        reason=reason or "Admin requested review hide",
    )
    await db.commit()

    return ApiResponse(
        success=True,
        data=AdminReviewDetailResponse(
            id=updated_review.id,
            user_id=updated_review.user_id,
            product_id=updated_review.product_id,
            product_name=updated_review.product.name if updated_review.product else None,
            order_id=updated_review.order_id,
            order_item_id=updated_review.order_item_id,
            rating=updated_review.rating,
            title=updated_review.title,
            body=updated_review.body,
            status=updated_review.status,
            is_verified_purchase=updated_review.is_verified_purchase,
            helpful_count=updated_review.helpful_count,
            created_at=updated_review.created_at,
            updated_at=updated_review.updated_at,
            deleted_at=updated_review.deleted_at,
        ),
        message="Review hidden successfully.",
    )


@router.post(
    "/{review_id}/restore",
    response_model=ApiResponse[AdminReviewDetailResponse],
    summary="Restore hidden review to public display",
)
async def admin_restore_review(
    review_id: str,
    reason: Optional[str] = Query(None, description="Reason for restoring review"),
    current_admin: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db_writer),
) -> ApiResponse[AdminReviewDetailResponse]:
    """
    Convenience action to restore a hidden review back to PUBLISHED status.
    """
    review = await ReviewRepository.get_by_id(db, review_id, include_deleted=False)
    if not review:
        raise CartifyException(
            status_code=404,
            message=f"Review with identifier '{review_id}' was not found.",
            code="REVIEW_NOT_FOUND",
        )

    updated_review = await ReviewModerationService.transition_status(
        db=db,
        review=review,
        new_status=ReviewStatus.PUBLISHED.value,
        admin_user_id=current_admin.id,
        reason=reason or "Admin restored review",
    )
    await db.commit()

    return ApiResponse(
        success=True,
        data=AdminReviewDetailResponse(
            id=updated_review.id,
            user_id=updated_review.user_id,
            product_id=updated_review.product_id,
            product_name=updated_review.product.name if updated_review.product else None,
            order_id=updated_review.order_id,
            order_item_id=updated_review.order_item_id,
            rating=updated_review.rating,
            title=updated_review.title,
            body=updated_review.body,
            status=updated_review.status,
            is_verified_purchase=updated_review.is_verified_purchase,
            helpful_count=updated_review.helpful_count,
            created_at=updated_review.created_at,
            updated_at=updated_review.updated_at,
            deleted_at=updated_review.deleted_at,
        ),
        message="Review restored successfully.",
    )


@router.get(
    "/reports/queue",
    response_model=ApiResponse[dict],
    summary="List customer review reports for moderation",
)
async def admin_list_reports(
    status: Optional[str] = Query(None, description="Filter by status: PENDING, REVIEWED, DISMISSED, ACTION_TAKEN"),
    review_id: Optional[str] = Query(None, description="Filter by review ID"),
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    current_admin: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db_reader),
) -> ApiResponse[dict]:
    """
    Retrieves customer abuse and spam reports for review moderation.
    """
    items, total = await ReviewReportRepository.list_reports(
        db=db,
        status=status,
        review_id=review_id,
        limit=limit,
        offset=offset,
    )
    serialized = [
        ReviewReportResponse(
            id=r.id,
            review_id=r.review_id,
            reason=r.reason,
            description=r.description,
            status=r.status,
            created_at=r.created_at,
        ).model_dump()
        for r in items
    ]
    return ApiResponse(
        success=True,
        data={"items": serialized, "total": total, "limit": limit, "offset": offset},
        message="Review reports retrieved successfully.",
    )
