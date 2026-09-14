"""
Cartify Review Service (Module 14)

Primary application orchestration for product reviews, ratings, helpful voting, and reporting:
- Authenticated customer review lifecycle with server-authoritative purchase verification
- Strict rate limiting integration per authenticated user action
- Transactional creation, update, and soft-delete
- XSS prevention and safe text normalization
- Mass-assignment protection (client can never set status, is_verified_purchase, or helpful_count)
- Privacy-preserving reviewer name masking (no PII or internal IDs exposed)
- Atomic rating summary synchronization and cache invalidation
- Transactional Outbox integration (REVIEW_SUBMITTED, REVIEW_REPORTED)
"""

from datetime import datetime, timezone
import html
import logging
import re
from typing import Any, Dict, List, Optional, Set, Tuple
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.errors import CartifyException, ForbiddenError, NotFoundError
from app.models.review import Review, ReviewStatus
from app.models.review_report import ReportReason, ReportStatus, ReviewReport
from app.models.user import User
from app.repositories.review import ReviewRepository
from app.repositories.review_helpful_vote import ReviewHelpfulVoteRepository
from app.repositories.review_report import ReviewReportRepository
from app.services.notification_service import NotificationService
from app.services.rate_limiter import SlidingWindowRateLimiter
from app.services.review_aggregation_service import ReviewAggregationService
from app.services.review_eligibility_service import ReviewEligibilityService
from app.services.review_moderation_service import ReviewModerationService

logger = logging.getLogger("cartify.reviews.service")


class ReviewService:
    @staticmethod
    def sanitize_text(text: str, max_length: int = 3000) -> str:
        """
        Sanitizes untrusted customer input:
        - Strips HTML tags
        - Trims surrounding whitespace
        - Escapes special characters
        - Truncates to max allowed length
        """
        if not text:
            return ""
        # Strip HTML tags
        clean = re.sub(r"<[^>]*>", "", text)
        # Normalize whitespace
        clean = " ".join(clean.split())
        # Strip leading/trailing
        clean = clean.strip()
        # Escape any lingering HTML entities
        clean = html.escape(clean)
        return clean[:max_length]

    @staticmethod
    def mask_reviewer_name(name: Optional[str]) -> str:
        """
        Produces a privacy-safe public representation of customer name:
        e.g., 'Alex Robinson' -> 'Alex R.'
        e.g., 'Priya' -> 'Priya S.' or 'P****'
        """
        if not name or not name.strip():
            return "Verified Customer"
        parts = name.strip().split()
        if len(parts) >= 2:
            return f"{parts[0]} {parts[-1][0].upper()}."
        first = parts[0]
        if len(first) > 2:
            return f"{first[0]}***{first[-1]}"
        return f"{first[0]}***"

    @classmethod
    async def create_review(
        cls,
        db: AsyncSession,
        current_user: User,
        product_id: str,
        order_item_id: str,
        rating: int,
        title: str,
        body: str,
    ) -> Review:
        """
        Creates a new customer review following strict purchase and eligibility verification.
        """
        # 1. Rate limiting check for authenticated user
        await SlidingWindowRateLimiter.check_and_raise(
            identifier=f"review_create:{current_user.id}",
            limit=10,
            window_seconds=60,
        )

        # 2. Input validation
        if not (1 <= rating <= 5):
            raise CartifyException(
                status_code=400,
                message="Rating must be an integer between 1 and 5.",
                code="INVALID_RATING",
            )

        clean_title = cls.sanitize_text(title, max_length=150)
        clean_body = cls.sanitize_text(body, max_length=3000)

        if not clean_title or len(clean_title) < 2:
            raise CartifyException(
                status_code=400,
                message="Review title must be at least 2 characters long.",
                code="INVALID_REVIEW_CONTENT",
            )

        if not clean_body or len(clean_body) < 5:
            raise CartifyException(
                status_code=400,
                message="Review body must be at least 5 characters long.",
                code="INVALID_REVIEW_CONTENT",
            )

        # 3. Server-authoritative purchase & ownership verification
        order_item = await ReviewEligibilityService.verify_order_item_for_review(
            db=db,
            user_id=current_user.id,
            product_id=product_id,
            order_item_id=order_item_id,
        )

        # 4. Status determination via moderation service
        status = ReviewModerationService.determine_initial_status()

        # 5. Persist review with server-derived properties
        review_data = {
            "user_id": current_user.id,
            "product_id": product_id,
            "order_id": order_item.order_id,
            "order_item_id": order_item.id,
            "rating": rating,
            "title": clean_title,
            "body": clean_body,
            "status": status,
            "is_verified_purchase": True,  # Server-derived
            "helpful_count": 0,
        }

        try:
            review = await ReviewRepository.create(db, review_data)
        except IntegrityError:
            await db.rollback()
            raise CartifyException(
                status_code=409,
                message="A review has already been submitted for this purchase.",
                code="REVIEW_ALREADY_EXISTS",
            )

        # 6. Recalculate aggregates if published
        if status == ReviewStatus.PUBLISHED.value:
            await ReviewAggregationService.recalculate_for_product(db, product_id)

        # 7. Emit transactional outbox event
        try:
            await NotificationService.emit_outbox_event(
                db=db,
                event_type="REVIEW_SUBMITTED",
                aggregate_type="REVIEW",
                aggregate_id=review.id,
                payload={
                    "review_id": review.id,
                    "product_id": product_id,
                    "user_id": current_user.id,
                    "rating": rating,
                    "status": status,
                },
                user_id=current_user.id,
                idempotency_key=f"REVIEW_SUBMITTED:{review.id}",
            )
        except Exception as e:
            logger.warning(f"Could not emit REVIEW_SUBMITTED event: {e}")

        return review

    @classmethod
    async def get_review_by_id(
        cls,
        db: AsyncSession,
        review_id: str,
        current_user: Optional[User] = None,
    ) -> Review:
        """
        Retrieves a review by ID.
        Public callers can only view PUBLISHED, non-deleted reviews.
        Review owners and admins can view their own non-published reviews.
        """
        review = await ReviewRepository.get_by_id(db, review_id, include_deleted=False)
        if not review:
            raise CartifyException(
                status_code=404,
                message="The requested review was not found.",
                code="REVIEW_NOT_FOUND",
            )

        # Non-published review visibility
        if review.status != ReviewStatus.PUBLISHED.value:
            is_owner = current_user and current_user.id == review.user_id
            is_admin = current_user and getattr(current_user, "role", "") == "admin"
            if not (is_owner or is_admin):
                raise CartifyException(
                    status_code=404,
                    message="The requested review was not found or is awaiting moderation.",
                    code="REVIEW_NOT_PUBLISHED",
                )

        return review

    @classmethod
    async def update_review(
        cls,
        db: AsyncSession,
        current_user: User,
        review_id: str,
        rating: Optional[int] = None,
        title: Optional[str] = None,
        body: Optional[str] = None,
    ) -> Review:
        """
        Allows review owner to update rating, title, and body.
        Strictly prevents mass assignment (user_id, status, helpful_count, etc.).
        """
        await SlidingWindowRateLimiter.check_and_raise(
            identifier=f"review_update:{current_user.id}",
            limit=15,
            window_seconds=60,
        )

        review = await ReviewRepository.get_by_id(db, review_id, include_deleted=False)
        if not review:
            raise CartifyException(
                status_code=404,
                message="The requested review was not found.",
                code="REVIEW_NOT_FOUND",
            )

        # Ownership authorization check (IDOR prevention)
        if review.user_id != current_user.id:
            raise CartifyException(
                status_code=403,
                message="You do not have permission to modify this review.",
                code="REVIEW_ACCESS_DENIED",
            )

        update_data: Dict[str, Any] = {}
        rating_changed = False

        if rating is not None:
            if not (1 <= rating <= 5):
                raise CartifyException(
                    status_code=400,
                    message="Rating must be an integer between 1 and 5.",
                    code="INVALID_RATING",
                )
            if review.rating != rating:
                update_data["rating"] = rating
                rating_changed = True

        if title is not None:
            clean_title = cls.sanitize_text(title, max_length=150)
            if not clean_title or len(clean_title) < 2:
                raise CartifyException(
                    status_code=400,
                    message="Review title must be at least 2 characters long.",
                    code="INVALID_REVIEW_CONTENT",
                )
            update_data["title"] = clean_title

        if body is not None:
            clean_body = cls.sanitize_text(body, max_length=3000)
            if not clean_body or len(clean_body) < 5:
                raise CartifyException(
                    status_code=400,
                    message="Review body must be at least 5 characters long.",
                    code="INVALID_REVIEW_CONTENT",
                )
            update_data["body"] = clean_body

        if update_data:
            review = await ReviewRepository.update(db, review, update_data)

            # If rating changed on a published review, recalculate rating summary
            if rating_changed and review.status == ReviewStatus.PUBLISHED.value:
                await ReviewAggregationService.recalculate_for_product(db, review.product_id)

        return review

    @classmethod
    async def delete_review(
        cls,
        db: AsyncSession,
        current_user: User,
        review_id: str,
    ) -> None:
        """
        Soft-deletes a review. Only the owner or an admin can delete.
        """
        await SlidingWindowRateLimiter.check_and_raise(
            identifier=f"review_delete:{current_user.id}",
            limit=15,
            window_seconds=60,
        )

        review = await ReviewRepository.get_by_id(db, review_id, include_deleted=False)
        if not review:
            raise CartifyException(
                status_code=404,
                message="The requested review was not found.",
                code="REVIEW_NOT_FOUND",
            )

        is_owner = review.user_id == current_user.id
        is_admin = getattr(current_user, "role", "") == "admin"
        if not (is_owner or is_admin):
            raise CartifyException(
                status_code=403,
                message="You do not have permission to delete this review.",
                code="REVIEW_ACCESS_DENIED",
            )

        product_id = review.product_id
        was_published = review.status == ReviewStatus.PUBLISHED.value

        await ReviewRepository.soft_delete(db, review)

        # Recalculate summary if deleted review was published
        if was_published:
            await ReviewAggregationService.recalculate_for_product(db, product_id)

    @classmethod
    async def list_product_reviews(
        cls,
        db: AsyncSession,
        product_id: str,
        rating: Optional[int] = None,
        verified_only: bool = False,
        sort: str = "MOST_RECENT",
        limit: int = 20,
        cursor: Optional[str] = None,
        current_user: Optional[User] = None,
    ) -> Dict[str, Any]:
        """
        Public listing for published, non-deleted reviews.
        Masks user identities to protect privacy.
        """
        items, next_cursor, total = await ReviewRepository.list_for_product(
            db=db,
            product_id=product_id,
            rating=rating,
            verified_only=verified_only,
            sort=sort,
            limit=limit,
            cursor=cursor,
        )

        # Batch resolve helpful votes for authenticated caller
        user_voted_ids: Set[str] = set()
        if current_user and items:
            item_ids = [r.id for r in items]
            user_voted_ids = await ReviewHelpfulVoteRepository.get_user_voted_review_ids(
                db=db,
                user_id=current_user.id,
                review_ids=item_ids,
            )

        serialized_reviews = []
        for r in items:
            reviewer_name = cls.mask_reviewer_name(r.user.name if r.user else None)
            is_own = bool(current_user and current_user.id == r.user_id)
            serialized_reviews.append({
                "id": r.id,
                "rating": r.rating,
                "title": r.title,
                "body": r.body,
                "status": r.status,
                "is_verified_purchase": r.is_verified_purchase,
                "helpful_count": r.helpful_count,
                "created_at": r.created_at,
                "reviewer_name": reviewer_name,
                "user_voted_helpful": r.id in user_voted_ids,
                "is_own_review": is_own,
            })

        # Fetch product rating summary
        summary = await ReviewAggregationService.get_summary_for_product(db, product_id)

        return {
            "items": serialized_reviews,
            "next_cursor": next_cursor,
            "total": total,
            "summary": summary,
        }

    @classmethod
    async def list_user_reviews(
        cls,
        db: AsyncSession,
        current_user: User,
        limit: int = 20,
        offset: int = 0,
    ) -> Dict[str, Any]:
        """
        Lists customer's own submitted reviews (including PENDING).
        """
        items, total = await ReviewRepository.list_for_user(
            db=db,
            user_id=current_user.id,
            limit=limit,
            offset=offset,
        )

        serialized = []
        for r in items:
            serialized.append({
                "id": r.id,
                "product_id": r.product_id,
                "product_name": r.product.name if r.product else "Product",
                "product_slug": r.product.slug if r.product else None,
                "product_image_url": r.product.image_url if r.product else None,
                "order_id": r.order_id,
                "rating": r.rating,
                "title": r.title,
                "body": r.body,
                "status": r.status,
                "is_verified_purchase": r.is_verified_purchase,
                "helpful_count": r.helpful_count,
                "created_at": r.created_at,
                "updated_at": r.updated_at,
            })

        return {
            "items": serialized,
            "total": total,
            "limit": limit,
            "offset": offset,
        }

    @classmethod
    async def vote_helpful(
        cls,
        db: AsyncSession,
        current_user: User,
        review_id: str,
    ) -> Dict[str, Any]:
        """
        Customer marks review as helpful.
        Safe against concurrency races and duplicate votes.
        """
        await SlidingWindowRateLimiter.check_and_raise(
            identifier=f"review_vote:{current_user.id}",
            limit=30,
            window_seconds=60,
        )

        review = await ReviewRepository.get_by_id(db, review_id, include_deleted=False)
        if not review or review.status != ReviewStatus.PUBLISHED.value:
            raise CartifyException(
                status_code=404,
                message="Review not found or not published.",
                code="REVIEW_NOT_FOUND",
            )

        # Check existing vote
        already_voted = await ReviewHelpfulVoteRepository.has_voted(
            db=db,
            review_id=review_id,
            user_id=current_user.id,
        )
        if already_voted:
            raise CartifyException(
                status_code=409,
                message="You have already marked this review as helpful.",
                code="HELPFUL_VOTE_DUPLICATE",
            )

        try:
            await ReviewHelpfulVoteRepository.add_vote(
                db=db,
                review_id=review_id,
                user_id=current_user.id,
            )
            await ReviewRepository.atomic_increment_helpful(db, review_id)
        except IntegrityError:
            await db.rollback()
            raise CartifyException(
                status_code=409,
                message="You have already marked this review as helpful.",
                code="HELPFUL_VOTE_DUPLICATE",
            )

        updated_review = await ReviewRepository.get_by_id(db, review_id)
        return {
            "review_id": review_id,
            "helpful_count": updated_review.helpful_count if updated_review else review.helpful_count + 1,
            "user_voted_helpful": True,
        }

    @classmethod
    async def remove_helpful_vote(
        cls,
        db: AsyncSession,
        current_user: User,
        review_id: str,
    ) -> Dict[str, Any]:
        """
        Removes customer's helpful vote. Safe against repeated calls.
        """
        await SlidingWindowRateLimiter.check_and_raise(
            identifier=f"review_vote:{current_user.id}",
            limit=30,
            window_seconds=60,
        )

        removed = await ReviewHelpfulVoteRepository.remove_vote(
            db=db,
            review_id=review_id,
            user_id=current_user.id,
        )
        if removed:
            await ReviewRepository.atomic_decrement_helpful(db, review_id)

        updated_review = await ReviewRepository.get_by_id(db, review_id)
        return {
            "review_id": review_id,
            "helpful_count": updated_review.helpful_count if updated_review else 0,
            "user_voted_helpful": False,
        }

    @classmethod
    async def report_review(
        cls,
        db: AsyncSession,
        current_user: User,
        review_id: str,
        reason: str,
        description: Optional[str] = None,
    ) -> ReviewReport:
        """
        Submits an abuse / moderation report for a review.
        Prevents duplicate reporting by the same user.
        """
        await SlidingWindowRateLimiter.check_and_raise(
            identifier=f"review_report:{current_user.id}",
            limit=5,
            window_seconds=60,
        )

        review = await ReviewRepository.get_by_id(db, review_id, include_deleted=False)
        if not review:
            raise CartifyException(
                status_code=404,
                message="The review you are reporting was not found.",
                code="REVIEW_NOT_FOUND",
            )

        # Check duplicate report
        already_reported = await ReviewReportRepository.has_reported(
            db=db,
            review_id=review_id,
            user_id=current_user.id,
        )
        if already_reported:
            raise CartifyException(
                status_code=409,
                message="You have already submitted a report for this review.",
                code="REVIEW_REPORT_DUPLICATE",
            )

        valid_reasons = {r.value for r in ReportReason}
        if reason.upper() not in valid_reasons:
            raise CartifyException(
                status_code=400,
                message=f"Invalid report reason. Must be one of: {', '.join(valid_reasons)}.",
                code="VALIDATION_ERROR",
            )

        clean_desc = cls.sanitize_text(description or "", max_length=1000)

        report_data = {
            "review_id": review_id,
            "user_id": current_user.id,
            "reason": reason.upper(),
            "description": clean_desc,
            "status": ReportStatus.PENDING.value,
        }

        try:
            report = await ReviewReportRepository.create(db, report_data)
        except IntegrityError:
            await db.rollback()
            raise CartifyException(
                status_code=409,
                message="You have already submitted a report for this review.",
                code="REVIEW_REPORT_DUPLICATE",
            )

        # Emit outbox event for moderation queue
        try:
            await NotificationService.emit_outbox_event(
                db=db,
                event_type="REVIEW_REPORTED",
                aggregate_type="REVIEW",
                aggregate_id=review_id,
                payload={
                    "report_id": report.id,
                    "review_id": review_id,
                    "reporter_user_id": current_user.id,
                    "reason": reason.upper(),
                },
                user_id=current_user.id,
                idempotency_key=f"REVIEW_REPORTED:{report.id}",
            )
        except Exception as e:
            logger.warning(f"Failed to emit REVIEW_REPORTED event: {e}")

        return report
