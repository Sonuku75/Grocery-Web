"""
Cartify Review Moderation Service Unit Tests (Module 14)

Tests moderation lifecycle state machine:
- Valid state transitions:
    PENDING -> PUBLISHED, REJECTED
    PUBLISHED -> HIDDEN, DELETED
    HIDDEN -> PUBLISHED
    REJECTED -> PUBLISHED
- Invalid state transitions:
    DELETED -> PUBLISHED, PENDING
    PUBLISHED -> PENDING
    REJECTED -> HIDDEN
- Automatic aggregate recalculation when review visibility changes
- Transactional outbox event emission for audit
"""

from datetime import datetime, timezone
from unittest.mock import AsyncMock, patch
import pytest

from app.core.errors import CartifyException
from app.models.review import Review, ReviewStatus
from app.services.review_moderation_service import (
    ALLOWED_REVIEW_TRANSITIONS,
    ReviewModerationService,
)


@pytest.fixture
def mock_db():
    return AsyncMock()


@pytest.fixture
def sample_pending_review():
    return Review(
        id="rev-mod-1",
        user_id="usr-1",
        product_id="prod-1",
        rating=5,
        title="Great product",
        body="Really enjoyed this apple.",
        status=ReviewStatus.PENDING.value,
        is_verified_purchase=True,
        helpful_count=0,
    )


class TestReviewModeration:
    def test_initial_status_determination(self):
        """Auto-publish settings affect initial status."""
        with patch("app.services.review_moderation_service.settings.REVIEW_MODERATION_AUTO_PUBLISH", True):
            assert ReviewModerationService.determine_initial_status() == ReviewStatus.PUBLISHED.value

        with patch("app.services.review_moderation_service.settings.REVIEW_MODERATION_AUTO_PUBLISH", False):
            assert ReviewModerationService.determine_initial_status() == ReviewStatus.PENDING.value

    def test_allowed_transitions_matrix(self):
        """Verify state machine transition allowance."""
        assert ReviewModerationService.can_transition(ReviewStatus.PENDING.value, ReviewStatus.PUBLISHED.value) is True
        assert ReviewModerationService.can_transition(ReviewStatus.PENDING.value, ReviewStatus.REJECTED.value) is True
        assert ReviewModerationService.can_transition(ReviewStatus.PUBLISHED.value, ReviewStatus.HIDDEN.value) is True
        assert ReviewModerationService.can_transition(ReviewStatus.PUBLISHED.value, ReviewStatus.DELETED.value) is True
        assert ReviewModerationService.can_transition(ReviewStatus.HIDDEN.value, ReviewStatus.PUBLISHED.value) is True
        assert ReviewModerationService.can_transition(ReviewStatus.REJECTED.value, ReviewStatus.PUBLISHED.value) is True

        # Impermissible transitions
        assert ReviewModerationService.can_transition(ReviewStatus.DELETED.value, ReviewStatus.PUBLISHED.value) is False
        assert ReviewModerationService.can_transition(ReviewStatus.DELETED.value, ReviewStatus.PENDING.value) is False
        assert ReviewModerationService.can_transition(ReviewStatus.PUBLISHED.value, ReviewStatus.PENDING.value) is False
        assert ReviewModerationService.can_transition(ReviewStatus.REJECTED.value, ReviewStatus.HIDDEN.value) is False

    @pytest.mark.asyncio
    async def test_valid_transition_execution(self, mock_db, sample_pending_review):
        """Successfully transitions status and recalculates aggregate if published."""
        with patch("app.services.review_aggregation_service.ReviewAggregationService.recalculate_for_product", return_value=None) as mock_recalc, \
             patch("app.services.notification_service.NotificationService.emit_outbox_event", return_value=None) as mock_outbox:

            updated = await ReviewModerationService.transition_status(
                db=mock_db,
                review=sample_pending_review,
                new_status=ReviewStatus.PUBLISHED.value,
                admin_user_id="usr-admin-1",
                reason="Review meets community guidelines",
            )

            assert updated.status == ReviewStatus.PUBLISHED.value
            mock_recalc.assert_called_once_with(mock_db, "prod-1")
            mock_outbox.assert_called_once()

    @pytest.mark.asyncio
    async def test_invalid_transition_raises_error(self, mock_db, sample_pending_review):
        """Invalid transition raises CartifyException with INVALID_REVIEW_STATUS_TRANSITION code."""
        sample_pending_review.status = ReviewStatus.DELETED.value

        with pytest.raises(CartifyException) as exc_info:
            await ReviewModerationService.transition_status(
                db=mock_db,
                review=sample_pending_review,
                new_status=ReviewStatus.PUBLISHED.value,
                admin_user_id="usr-admin-1",
            )

        assert exc_info.value.code == "INVALID_REVIEW_STATUS_TRANSITION"
        assert exc_info.value.status_code == 400
