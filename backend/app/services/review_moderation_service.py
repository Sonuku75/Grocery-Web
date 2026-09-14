"""
Cartify Review Moderation Service (Module 14)

Centralized state machine and moderation logic for product reviews:
- Enforces valid status transitions:
    PENDING -> PUBLISHED, REJECTED
    PUBLISHED -> HIDDEN, DELETED
    HIDDEN -> PUBLISHED
    REJECTED -> PUBLISHED
    DELETED -> Terminal
- Emits transactional outbox events (REVIEW_MODERATED) for auditing and notifications
- Automatically triggers rating recalculation whenever a review's published status changes
"""

import logging
from typing import Optional, Set
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.errors import CartifyException
from app.models.review import Review, ReviewStatus
from app.repositories.review import ReviewRepository
from app.services.notification_service import NotificationService

logger = logging.getLogger("cartify.reviews.moderation")

ALLOWED_REVIEW_TRANSITIONS = {
    ReviewStatus.PENDING.value: {ReviewStatus.PUBLISHED.value, ReviewStatus.REJECTED.value},
    ReviewStatus.PUBLISHED.value: {ReviewStatus.HIDDEN.value, ReviewStatus.DELETED.value},
    ReviewStatus.HIDDEN.value: {ReviewStatus.PUBLISHED.value, ReviewStatus.DELETED.value},
    ReviewStatus.REJECTED.value: {ReviewStatus.PUBLISHED.value},
    ReviewStatus.DELETED.value: set(),
}


class ReviewModerationService:
    @classmethod
    def determine_initial_status(cls) -> str:
        """
        Determines the review status at creation time based on application policy.
        """
        if settings.REVIEW_MODERATION_AUTO_PUBLISH:
            return ReviewStatus.PUBLISHED.value
        return ReviewStatus.PENDING.value

    @classmethod
    def can_transition(cls, current_status: str, new_status: str) -> bool:
        """
        Checks if status transition is permissible under the moderation state machine.
        """
        if current_status == new_status:
            return True
        allowed = ALLOWED_REVIEW_TRANSITIONS.get(current_status, set())
        return new_status in allowed

    @classmethod
    async def transition_status(
        cls,
        db: AsyncSession,
        review: Review,
        new_status: str,
        admin_user_id: Optional[str] = None,
        reason: Optional[str] = None,
    ) -> Review:
        """
        Enforces state transition, updates review, triggers rating recalculation,
        and logs audit outbox event.
        """
        old_status = review.status
        new_status = new_status.upper()

        if not cls.can_transition(old_status, new_status):
            raise CartifyException(
                status_code=400,
                message=f"Cannot transition review status from '{old_status}' to '{new_status}'.",
                code="INVALID_REVIEW_STATUS_TRANSITION",
                details={"current_status": old_status, "target_status": new_status},
            )

        if old_status == new_status:
            return review

        # Update status
        review.status = new_status
        await db.flush()

        # Recalculate rating summary if published visibility changed
        if old_status == ReviewStatus.PUBLISHED.value or new_status == ReviewStatus.PUBLISHED.value:
            from app.services.review_aggregation_service import ReviewAggregationService
            await ReviewAggregationService.recalculate_for_product(db, review.product_id)

        # Emit audit/notification outbox event
        try:
            await NotificationService.emit_outbox_event(
                db=db,
                event_type="REVIEW_MODERATED",
                aggregate_type="REVIEW",
                aggregate_id=review.id,
                payload={
                    "review_id": review.id,
                    "product_id": review.product_id,
                    "user_id": review.user_id,
                    "old_status": old_status,
                    "new_status": new_status,
                    "moderated_by": admin_user_id,
                    "reason": reason,
                },
                user_id=review.user_id,
                idempotency_key=f"REVIEW_MODERATED:{review.id}:{new_status}",
            )
        except Exception as e:
            logger.error(f"Failed to emit REVIEW_MODERATED outbox event: {e}")

        return review
