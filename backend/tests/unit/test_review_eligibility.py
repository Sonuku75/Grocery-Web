"""
Cartify Review Eligibility Service Unit Tests (Module 14)

Tests purchase and review eligibility rules:
- Successfully delivered order items are reviewable
- Non-delivered orders (PENDING, PROCESSING, SHIPPED) are rejected
- Cancelled and failed orders are rejected
- Non-owner order items cannot be reviewed (IDOR protection)
- Mismatched product IDs are rejected
- Existing non-deleted review prevents duplicate reviews
"""

from datetime import datetime, timezone
from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock, patch
import pytest

from app.core.errors import CartifyException
from app.models.order import FulfillmentStatus, Order, OrderItem, OrderStatus
from app.models.product import Product
from app.models.review import Review
from app.services.review_eligibility_service import ReviewEligibilityService


@pytest.fixture
def mock_db():
    return AsyncMock()


@pytest.fixture
def sample_delivered_order():
    return Order(
        id="ord-del-1",
        user_id="usr-cust-1",
        order_number="CRT-20260914-111111",
        status=OrderStatus.DELIVERED.value,
        fulfillment_status=FulfillmentStatus.DELIVERED.value,
        subtotal=Decimal("100.00"),
        total_amount=Decimal("100.00"),
        recipient_name="Test Customer",
        phone="9876543210",
        address_line_1="Test St",
        city="Bengaluru",
        state="Karnataka",
        country="India",
        postal_code="560001",
    )


@pytest.fixture
def sample_delivered_item(sample_delivered_order):
    item = OrderItem(
        id="item-del-1",
        order_id="ord-del-1",
        product_id="prod-apple-1",
        product_name="Fresh Royal Gala Apples",
        unit_price=Decimal("100.00"),
        quantity=1,
        line_total=Decimal("100.00"),
    )
    item.order = sample_delivered_order
    return item


class TestReviewEligibility:
    @pytest.mark.asyncio
    async def test_delivered_item_is_eligible_for_review(self, mock_db, sample_delivered_item):
        """Verified purchaser with delivered order item passes validation."""
        with patch.object(mock_db, "execute") as mock_exec, \
             patch("app.repositories.review.ReviewRepository.get_by_order_item", return_value=None):
            mock_res = MagicMock()
            mock_res.scalar_one_or_none.return_value = sample_delivered_item
            mock_exec.return_value = mock_res

            verified_item = await ReviewEligibilityService.verify_order_item_for_review(
                db=mock_db,
                user_id="usr-cust-1",
                product_id="prod-apple-1",
                order_item_id="item-del-1",
            )
            assert verified_item.id == "item-del-1"

    @pytest.mark.asyncio
    async def test_non_delivered_order_rejected(self, mock_db, sample_delivered_item):
        """Order in PENDING or PROCESSING state cannot be reviewed."""
        sample_delivered_item.order.status = OrderStatus.PROCESSING.value
        sample_delivered_item.order.fulfillment_status = FulfillmentStatus.PROCESSING.value

        with patch.object(mock_db, "execute") as mock_exec:
            mock_res = MagicMock()
            mock_res.scalar_one_or_none.return_value = sample_delivered_item
            mock_exec.return_value = mock_res

            with pytest.raises(CartifyException) as exc_info:
                await ReviewEligibilityService.verify_order_item_for_review(
                    db=mock_db,
                    user_id="usr-cust-1",
                    product_id="prod-apple-1",
                    order_item_id="item-del-1",
                )
            assert exc_info.value.code == "REVIEW_NOT_ELIGIBLE"

    @pytest.mark.asyncio
    async def test_cancelled_order_rejected(self, mock_db, sample_delivered_item):
        """Cancelled orders cannot be reviewed."""
        sample_delivered_item.order.status = OrderStatus.CANCELLED.value

        with patch.object(mock_db, "execute") as mock_exec:
            mock_res = MagicMock()
            mock_res.scalar_one_or_none.return_value = sample_delivered_item
            mock_exec.return_value = mock_res

            with pytest.raises(CartifyException) as exc_info:
                await ReviewEligibilityService.verify_order_item_for_review(
                    db=mock_db,
                    user_id="usr-cust-1",
                    product_id="prod-apple-1",
                    order_item_id="item-del-1",
                )
            assert exc_info.value.code == "REVIEW_NOT_ELIGIBLE"

    @pytest.mark.asyncio
    async def test_other_user_order_item_rejected(self, mock_db, sample_delivered_item):
        """User A attempting to review User B's order item is rejected (IDOR protection)."""
        with patch.object(mock_db, "execute") as mock_exec:
            mock_res = MagicMock()
            mock_res.scalar_one_or_none.return_value = sample_delivered_item
            mock_exec.return_value = mock_res

            with pytest.raises(CartifyException) as exc_info:
                await ReviewEligibilityService.verify_order_item_for_review(
                    db=mock_db,
                    user_id="usr-attacker-2",  # Different user
                    product_id="prod-apple-1",
                    order_item_id="item-del-1",
                )
            assert exc_info.value.code == "REVIEW_ACCESS_DENIED"
            assert exc_info.value.status_code == 403

    @pytest.mark.asyncio
    async def test_product_mismatch_rejected(self, mock_db, sample_delivered_item):
        """Order item product_id mismatch is rejected."""
        with patch.object(mock_db, "execute") as mock_exec:
            mock_res = MagicMock()
            mock_res.scalar_one_or_none.return_value = sample_delivered_item
            mock_exec.return_value = mock_res

            with pytest.raises(CartifyException) as exc_info:
                await ReviewEligibilityService.verify_order_item_for_review(
                    db=mock_db,
                    user_id="usr-cust-1",
                    product_id="prod-banana-99",  # Different product
                    order_item_id="item-del-1",
                )
            assert exc_info.value.code == "REVIEW_NOT_ELIGIBLE"

    @pytest.mark.asyncio
    async def test_duplicate_review_on_same_item_rejected(self, mock_db, sample_delivered_item):
        """If item already has an existing review, a duplicate submission is blocked."""
        existing_rev = Review(id="rev-1", user_id="usr-cust-1", product_id="prod-apple-1", rating=5)

        with patch.object(mock_db, "execute") as mock_exec, \
             patch("app.repositories.review.ReviewRepository.get_by_order_item", return_value=existing_rev):
            mock_res = MagicMock()
            mock_res.scalar_one_or_none.return_value = sample_delivered_item
            mock_exec.return_value = mock_res

            with pytest.raises(CartifyException) as exc_info:
                await ReviewEligibilityService.verify_order_item_for_review(
                    db=mock_db,
                    user_id="usr-cust-1",
                    product_id="prod-apple-1",
                    order_item_id="item-del-1",
                )
            assert exc_info.value.code == "REVIEW_ALREADY_EXISTS"
            assert exc_info.value.status_code == 409
