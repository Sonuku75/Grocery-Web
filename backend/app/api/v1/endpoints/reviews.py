"""
Cartify Customer Reviews API (Module 14)

Customer and public review endpoints:
- GET  /api/v1/products/{product_id}/reviews: Cursor-paginated public reviews with sorting and filters
- POST /api/v1/products/{product_id}/reviews: Purchase-verified customer review submission
- GET  /api/v1/products/{product_id}/review-summary: Public star rating distribution and averages
- GET  /api/v1/products/{product_id}/eligibility: Verified-purchase eligibility check for writing reviews
- GET  /api/v1/reviews/{review_id}: Single review detail (published only, or review owner/admin)
- PATCH /api/v1/reviews/{review_id}: Edit own review rating, title, or body
- DELETE /api/v1/reviews/{review_id}: Soft-delete own review
- POST /api/v1/reviews/{review_id}/helpful: Mark review as helpful (idempotent, atomic count)
- DELETE /api/v1/reviews/{review_id}/helpful: Remove helpful vote
- POST /api/v1/reviews/{review_id}/reports: Flag review for moderation
- GET  /api/v1/users/me/reviews: Customer's own submitted review history
"""

from typing import Optional
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import (
    get_current_active_user,
    get_db_reader,
    get_db_writer,
    get_optional_user,
    rate_limit,
)
from app.core.config import settings
from app.models.user import User
from app.schemas.common import ApiResponse
from app.schemas.review import (
    ReviewCreateRequest,
    ReviewEligibilityResponse,
    ReviewHelpfulResponse,
    ReviewListResponse,
    ReviewPublicResponse,
    ReviewReportCreateRequest,
    ReviewReportResponse,
    ReviewSummaryResponse,
    ReviewUpdateRequest,
    ReviewUserListResponse,
    ReviewableOrderItem,
)
from app.services.review_aggregation_service import ReviewAggregationService
from app.services.review_eligibility_service import ReviewEligibilityService
from app.services.review_service import ReviewService

router = APIRouter(tags=["Reviews"])


# --------------------------------------------------------------------------
# Product Reviews & Summary
# --------------------------------------------------------------------------

@router.get(
    "/products/{product_id}/reviews",
    response_model=ApiResponse[ReviewListResponse],
    dependencies=[Depends(rate_limit(limit=300, window_seconds=60))],
    summary="List published product reviews with cursor pagination and filters",
)
async def list_product_reviews(
    product_id: str,
    rating: Optional[int] = Query(None, ge=1, le=5, description="Filter by star rating (1-5)"),
    verified_only: bool = Query(False, description="Filter only verified purchases"),
    sort: str = Query("MOST_RECENT", description="Sort option: MOST_RECENT, MOST_HELPFUL, HIGHEST_RATING, LOWEST_RATING"),
    limit: int = Query(settings.REVIEW_PAGE_SIZE_DEFAULT, ge=1, le=settings.REVIEW_PAGE_SIZE_MAX),
    cursor: Optional[str] = Query(None, description="Opaque pagination cursor"),
    current_user: Optional[User] = Depends(get_optional_user),
    db: AsyncSession = Depends(get_db_reader),
) -> ApiResponse[ReviewListResponse]:
    """
    Public endpoint retrieving published reviews for a product.
    Masks customer PII and internal identifiers.
    """
    result = await ReviewService.list_product_reviews(
        db=db,
        product_id=product_id,
        rating=rating,
        verified_only=verified_only,
        sort=sort,
        limit=limit,
        cursor=cursor,
        current_user=current_user,
    )
    return ApiResponse(
        success=True,
        data=ReviewListResponse(**result),
        message="Reviews retrieved successfully.",
    )


@router.post(
    "/products/{product_id}/reviews",
    response_model=ApiResponse[ReviewPublicResponse],
    status_code=status.HTTP_201_CREATED,
    summary="Submit a verified-purchase customer review",
)
async def create_product_review(
    product_id: str,
    payload: ReviewCreateRequest,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db_writer),
) -> ApiResponse[ReviewPublicResponse]:
    """
    Creates a new customer review following server-authoritative purchase and delivery verification.
    Clients cannot specify user_id, is_verified_purchase, status, or helpful_count.
    """
    review = await ReviewService.create_review(
        db=db,
        current_user=current_user,
        product_id=product_id,
        order_item_id=payload.order_item_id,
        rating=payload.rating,
        title=payload.title,
        body=payload.body,
    )
    await db.commit()

    return ApiResponse(
        success=True,
        data=ReviewPublicResponse(
            id=review.id,
            rating=review.rating,
            title=review.title,
            body=review.body,
            status=review.status,
            is_verified_purchase=review.is_verified_purchase,
            helpful_count=review.helpful_count,
            created_at=review.created_at,
            reviewer_name=ReviewService.mask_reviewer_name(current_user.name),
            user_voted_helpful=False,
            is_own_review=True,
        ),
        message="Review submitted successfully.",
    )


@router.get(
    "/products/{product_id}/review-summary",
    response_model=ApiResponse[ReviewSummaryResponse],
    dependencies=[Depends(rate_limit(limit=300, window_seconds=60))],
    summary="Get authoritative rating summary and star distribution",
)
async def get_product_review_summary(
    product_id: str,
    db: AsyncSession = Depends(get_db_reader),
) -> ApiResponse[ReviewSummaryResponse]:
    """
    Returns public rating statistics (average rating, total reviews, 1-5 star distribution).
    Backed by Redis cache-aside and authoritative PostgreSQL transactional aggregates.
    """
    summary = await ReviewAggregationService.get_summary_for_product(db=db, product_id=product_id)
    return ApiResponse(
        success=True,
        data=ReviewSummaryResponse(**summary),
        message="Review summary retrieved successfully.",
    )


@router.get(
    "/products/{product_id}/eligibility",
    response_model=ApiResponse[ReviewEligibilityResponse],
    summary="Check if current customer can review this product",
)
async def check_review_eligibility(
    product_id: str,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db_reader),
) -> ApiResponse[ReviewEligibilityResponse]:
    """
    Verifies if authenticated customer has purchased and received this product,
    returning eligible order item IDs for review creation.
    """
    can_review, reason, items = await ReviewEligibilityService.can_review_product(
        db=db,
        user_id=current_user.id,
        product_id=product_id,
    )

    reviewable_items = [
        ReviewableOrderItem(
            order_item_id=item.id,
            order_id=item.order_id,
            order_number=item.order.order_number if item.order else "",
            product_id=item.product_id or product_id,
            product_name=item.product_name,
            variant_name=item.variant_name,
            delivered_at=item.order.created_at if item.order else None,
        )
        for item in items
    ]

    return ApiResponse(
        success=True,
        data=ReviewEligibilityResponse(
            can_review=can_review,
            reason=reason,
            reviewable_items=reviewable_items,
        ),
        message="Review eligibility evaluated.",
    )


# --------------------------------------------------------------------------
# Individual Review Actions
# --------------------------------------------------------------------------

@router.get(
    "/reviews/{review_id}",
    response_model=ApiResponse[ReviewPublicResponse],
    summary="Get individual review details",
)
async def get_review(
    review_id: str,
    current_user: Optional[User] = Depends(get_optional_user),
    db: AsyncSession = Depends(get_db_reader),
) -> ApiResponse[ReviewPublicResponse]:
    """
    Retrieves a review by ID.
    Only published reviews are accessible to the general public.
    """
    review = await ReviewService.get_review_by_id(
        db=db,
        review_id=review_id,
        current_user=current_user,
    )
    is_own = bool(current_user and current_user.id == review.user_id)
    return ApiResponse(
        success=True,
        data=ReviewPublicResponse(
            id=review.id,
            rating=review.rating,
            title=review.title,
            body=review.body,
            status=review.status,
            is_verified_purchase=review.is_verified_purchase,
            helpful_count=review.helpful_count,
            created_at=review.created_at,
            reviewer_name=ReviewService.mask_reviewer_name(review.user.name if review.user else None),
            is_own_review=is_own,
        ),
        message="Review details retrieved.",
    )


@router.patch(
    "/reviews/{review_id}",
    response_model=ApiResponse[ReviewPublicResponse],
    summary="Update own review",
)
async def update_review(
    review_id: str,
    payload: ReviewUpdateRequest,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db_writer),
) -> ApiResponse[ReviewPublicResponse]:
    """
    Allows review author to edit their own rating, title, or body.
    Internal fields (status, helpful_count, is_verified_purchase) cannot be modified.
    """
    review = await ReviewService.update_review(
        db=db,
        current_user=current_user,
        review_id=review_id,
        rating=payload.rating,
        title=payload.title,
        body=payload.body,
    )
    await db.commit()

    return ApiResponse(
        success=True,
        data=ReviewPublicResponse(
            id=review.id,
            rating=review.rating,
            title=review.title,
            body=review.body,
            status=review.status,
            is_verified_purchase=review.is_verified_purchase,
            helpful_count=review.helpful_count,
            created_at=review.created_at,
            reviewer_name=ReviewService.mask_reviewer_name(current_user.name),
            is_own_review=True,
        ),
        message="Review updated successfully.",
    )


@router.delete(
    "/reviews/{review_id}",
    response_model=ApiResponse[dict],
    summary="Delete own review",
)
async def delete_review(
    review_id: str,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db_writer),
) -> ApiResponse[dict]:
    """
    Soft-deletes review and automatically updates rating aggregates.
    """
    await ReviewService.delete_review(
        db=db,
        current_user=current_user,
        review_id=review_id,
    )
    await db.commit()

    return ApiResponse(
        success=True,
        data={"review_id": review_id, "deleted": True},
        message="Review deleted successfully.",
    )


@router.post(
    "/reviews/{review_id}/helpful",
    response_model=ApiResponse[ReviewHelpfulResponse],
    summary="Mark review as helpful",
)
async def vote_helpful(
    review_id: str,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db_writer),
) -> ApiResponse[ReviewHelpfulResponse]:
    """
    Customer marks a review as helpful.
    Unique constraint prevents multiple votes from the same user.
    """
    res = await ReviewService.vote_helpful(
        db=db,
        current_user=current_user,
        review_id=review_id,
    )
    await db.commit()

    return ApiResponse(
        success=True,
        data=ReviewHelpfulResponse(**res),
        message="Review marked as helpful.",
    )


@router.delete(
    "/reviews/{review_id}/helpful",
    response_model=ApiResponse[ReviewHelpfulResponse],
    summary="Remove helpful mark from review",
)
async def remove_helpful_vote(
    review_id: str,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db_writer),
) -> ApiResponse[ReviewHelpfulResponse]:
    """
    Removes previously submitted helpful vote.
    """
    res = await ReviewService.remove_helpful_vote(
        db=db,
        current_user=current_user,
        review_id=review_id,
    )
    await db.commit()

    return ApiResponse(
        success=True,
        data=ReviewHelpfulResponse(**res),
        message="Helpful mark removed.",
    )


@router.post(
    "/reviews/{review_id}/reports",
    response_model=ApiResponse[ReviewReportResponse],
    status_code=status.HTTP_201_CREATED,
    summary="Report an inappropriate review",
)
async def report_review(
    review_id: str,
    payload: ReviewReportCreateRequest,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db_writer),
) -> ApiResponse[ReviewReportResponse]:
    """
    Submits a moderation report for a review.
    Prevents repeated abuse by enforcing unique reporting per user per review.
    """
    report = await ReviewService.report_review(
        db=db,
        current_user=current_user,
        review_id=review_id,
        reason=payload.reason.value,
        description=payload.description,
    )
    await db.commit()

    return ApiResponse(
        success=True,
        data=ReviewReportResponse(
            id=report.id,
            review_id=report.review_id,
            reason=report.reason,
            description=report.description,
            status=report.status,
            created_at=report.created_at,
        ),
        message="Review report submitted successfully.",
    )


# --------------------------------------------------------------------------
# Customer Review History
# --------------------------------------------------------------------------

@router.get(
    "/users/me/reviews",
    response_model=ApiResponse[ReviewUserListResponse],
    summary="Get customer's submitted reviews",
)
async def get_my_reviews(
    limit: int = Query(settings.REVIEW_PAGE_SIZE_DEFAULT, ge=1, le=settings.REVIEW_PAGE_SIZE_MAX),
    offset: int = Query(0, ge=0),
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db_reader),
) -> ApiResponse[ReviewUserListResponse]:
    """
    Retrieves all reviews submitted by the authenticated customer.
    """
    result = await ReviewService.list_user_reviews(
        db=db,
        current_user=current_user,
        limit=limit,
        offset=offset,
    )
    return ApiResponse(
        success=True,
        data=ReviewUserListResponse(**result),
        message="Customer reviews retrieved successfully.",
    )
