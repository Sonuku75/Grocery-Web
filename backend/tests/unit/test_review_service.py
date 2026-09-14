"""
Cartify Review Service Unit Tests (Module 14)

Tests core ReviewService business logic and validation:
- Input sanitization (XSS stripping, HTML entity handling, length limits)
- Privacy masking of customer names (no PII leakage)
- Rating integer bounds validation (1-5)
- Title & body length constraints
- Review ownership validation during edit and delete operations
"""

from unittest.mock import AsyncMock, patch
import pytest

from app.core.errors import CartifyException
from app.models.review import Review, ReviewStatus
from app.models.user import User
from app.services.review_service import ReviewService


@pytest.fixture
def mock_db():
    return AsyncMock()


@pytest.fixture
def customer_user():
    return User(
        id="usr-test-1",
        name="Ananya Sharma",
        email="ananya@cartify.com",
        role="customer",
        is_active=True,
    )


class TestReviewService:
    def test_text_sanitization_strips_html(self):
        """Removes malicious script and HTML tags safely."""
        malicious = "<script>alert('xss')</script><b>Great</b> apples!"
        sanitized = ReviewService.sanitize_text(malicious)
        assert "<script>" not in sanitized
        assert "<b>" not in sanitized
        assert "Great apples!" in sanitized

    def test_text_sanitization_truncates_length(self):
        """Enforces maximum string boundary."""
        oversized = "a" * 5000
        sanitized = ReviewService.sanitize_text(oversized, max_length=150)
        assert len(sanitized) == 150

    def test_mask_reviewer_name_privacy(self):
        """Masks customer name to prevent PII exposure."""
        assert ReviewService.mask_reviewer_name("Ananya Sharma") == "Ananya S."
        assert ReviewService.mask_reviewer_name("Rahul") == "R***l"
        assert ReviewService.mask_reviewer_name("") == "Verified Customer"
        assert ReviewService.mask_reviewer_name(None) == "Verified Customer"

    @pytest.mark.asyncio
    async def test_invalid_rating_rejected(self, mock_db, customer_user):
        """Ratings less than 1 or greater than 5 are rejected with INVALID_RATING."""
        with patch("app.services.rate_limiter.SlidingWindowRateLimiter.check_and_raise", return_value=None):
            for bad_rating in [0, 6, -1, 10]:
                with pytest.raises(CartifyException) as exc_info:
                    await ReviewService.create_review(
                        db=mock_db,
                        current_user=customer_user,
                        product_id="prod-1",
                        order_item_id="item-1",
                        rating=bad_rating,
                        title="Good product",
                        body="Very fresh and crisp apples.",
                    )
                assert exc_info.value.code == "INVALID_RATING"

    @pytest.mark.asyncio
    async def test_short_title_rejected(self, mock_db, customer_user):
        """Title with less than 2 characters is rejected."""
        with patch("app.services.rate_limiter.SlidingWindowRateLimiter.check_and_raise", return_value=None):
            with pytest.raises(CartifyException) as exc_info:
                await ReviewService.create_review(
                    db=mock_db,
                    current_user=customer_user,
                    product_id="prod-1",
                    order_item_id="item-1",
                    rating=5,
                    title="A",  # Too short
                    body="Very fresh and crisp apples.",
                )
            assert exc_info.value.code == "INVALID_REVIEW_CONTENT"

    @pytest.mark.asyncio
    async def test_short_body_rejected(self, mock_db, customer_user):
        """Body with less than 5 characters is rejected."""
        with patch("app.services.rate_limiter.SlidingWindowRateLimiter.check_and_raise", return_value=None):
            with pytest.raises(CartifyException) as exc_info:
                await ReviewService.create_review(
                    db=mock_db,
                    current_user=customer_user,
                    product_id="prod-1",
                    order_item_id="item-1",
                    rating=5,
                    title="Great apple",
                    body="Good",  # 4 chars < 5
                )
            assert exc_info.value.code == "INVALID_REVIEW_CONTENT"
