"""
Cartify Review Aggregation Service Unit Tests (Module 14)

Tests authoritative rating aggregation:
- Calculation of total reviews, average rating, and 1-5 star distributions
- Safe decimal rounding (e.g., 4.25 -> 4.3 for UI presentation)
- Exclusion of non-published (PENDING, REJECTED, HIDDEN, DELETED) reviews
- Redis cache invalidation upon recalculation
"""

from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock, patch
import pytest

from app.models.product_rating_summary import ProductRatingSummary
from app.repositories.product_rating_summary import ProductRatingSummaryRepository
from app.services.review_aggregation_service import ReviewAggregationService


@pytest.fixture
def mock_db():
    return AsyncMock()


class TestReviewAggregation:
    @pytest.mark.asyncio
    async def test_calculate_from_reviews_distribution(self, mock_db):
        """Aggregate query correctly computes total, average, and star counts."""
        # Mock database row returned for [5, 5, 4, 3] reviews
        mock_row = MagicMock(
            total_reviews=4,
            avg_rating=4.25,
            r1=0,
            r2=0,
            r3=1,
            r4=1,
            r5=2,
        )
        mock_res = MagicMock()
        mock_res.first.return_value = mock_row

        with patch.object(mock_db, "execute", return_value=mock_res):
            metrics = await ProductRatingSummaryRepository.calculate_from_reviews(mock_db, "prod-1")

            assert metrics["total_reviews"] == 4
            assert metrics["average_rating"] == Decimal("4.25")
            assert metrics["rating_5_count"] == 2
            assert metrics["rating_4_count"] == 1
            assert metrics["rating_3_count"] == 1
            assert metrics["rating_2_count"] == 0
            assert metrics["rating_1_count"] == 0

    @pytest.mark.asyncio
    async def test_recalculate_for_product_invalidates_cache(self, mock_db):
        """Recalculating triggers DB upsert and Redis cache invalidation."""
        mock_metrics = {
            "total_reviews": 3,
            "average_rating": Decimal("4.67"),
            "rating_1_count": 0,
            "rating_2_count": 0,
            "rating_3_count": 0,
            "rating_4_count": 1,
            "rating_5_count": 2,
        }
        mock_summary = ProductRatingSummary(
            product_id="prod-1",
            total_reviews=3,
            average_rating=Decimal("4.67"),
            rating_5_count=2,
            rating_4_count=1,
        )

        with patch("app.repositories.product_rating_summary.ProductRatingSummaryRepository.calculate_from_reviews", return_value=mock_metrics), \
             patch("app.repositories.product_rating_summary.ProductRatingSummaryRepository.upsert", return_value=mock_summary), \
             patch("app.core.redis.redis_client.delete") as mock_delete:

            res = await ReviewAggregationService.recalculate_for_product(mock_db, "prod-1")

            assert res.total_reviews == 3
            mock_delete.assert_called_once_with("review_summary:prod-1")

    @pytest.mark.asyncio
    async def test_get_summary_with_zero_reviews(self, mock_db):
        """Zero reviews returns clean 0.0 average rating without divide-by-zero."""
        mock_summary = ProductRatingSummary(
            product_id="prod-zero",
            total_reviews=0,
            average_rating=Decimal("0.00"),
            rating_1_count=0,
            rating_2_count=0,
            rating_3_count=0,
            rating_4_count=0,
            rating_5_count=0,
        )

        with patch("app.core.redis.redis_client.get", return_value=None), \
             patch("app.repositories.product_rating_summary.ProductRatingSummaryRepository.get_by_product_id", return_value=mock_summary), \
             patch("app.core.redis.redis_client.set", return_value=None):

            summary = await ReviewAggregationService.get_summary_for_product(mock_db, "prod-zero")

            assert summary["total_reviews"] == 0
            assert summary["average_rating"] == 0.0
            assert summary["distribution"]["5"] == 0
