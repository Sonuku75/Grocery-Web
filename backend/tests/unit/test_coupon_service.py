"""
Unit tests for Cartify CouponService (Module 8)

Validates core coupon business logic:
1. Percentage discount calculation
2. Percentage discount capped by maximum_discount
3. Fixed amount discount calculation
4. Fixed amount discount capped by subtotal (cannot exceed subtotal)
5. Zero or negative subtotal yields 0.00 discount
6. Validation fails for nonexistent coupon code
7. Validation fails for inactive coupon
8. Validation fails for future starts_at date
9. Validation fails for expired coupon
10. Validation fails when global usage_limit is reached
11. Validation fails when per_user_usage_limit is reached
12. Validation fails when subtotal < minimum_order_value
13. Validation succeeds and calculates correct discount
14. Admin create coupon duplicate code rejected (400)
15. Admin create coupon invalid percentage rejected (422 / 400)
16. Admin create coupon expires_at <= starts_at rejected (422 / 400)
"""

from datetime import datetime, timedelta, timezone
from decimal import Decimal
from unittest.mock import AsyncMock, patch
import pytest

from app.core.errors import CartifyException, NotFoundError
from app.models.coupon import Coupon, CouponUsage, DiscountType
from app.schemas.coupon import CouponCreateRequest, CouponUpdateRequest
from app.services.coupon_service import CouponService


@pytest.fixture
def base_coupon():
    now = datetime.now(timezone.utc)
    return Coupon(
        id="coup-1",
        code="SAVE20",
        name="Save 20% Off",
        description="20% off up to ₹200 on orders over ₹500",
        discount_type="PERCENTAGE",
        discount_value=Decimal("20.00"),
        minimum_order_value=Decimal("500.00"),
        maximum_discount=Decimal("200.00"),
        starts_at=now - timedelta(days=1),
        expires_at=now + timedelta(days=30),
        usage_limit=100,
        per_user_usage_limit=2,
        used_count=10,
        is_active=True,
    )


@pytest.fixture
def fixed_coupon():
    now = datetime.now(timezone.utc)
    return Coupon(
        id="coup-2",
        code="FLAT150",
        name="Flat ₹150 Off",
        description="Flat ₹150 off on orders over ₹400",
        discount_type="FIXED_AMOUNT",
        discount_value=Decimal("150.00"),
        minimum_order_value=Decimal("400.00"),
        maximum_discount=None,
        starts_at=now - timedelta(days=1),
        expires_at=now + timedelta(days=30),
        usage_limit=50,
        per_user_usage_limit=1,
        used_count=5,
        is_active=True,
    )


# ==============================================================================
# 1, 2, 3, 4, 5: Discount Calculations
# ==============================================================================

def test_calculate_discount_percentage(base_coupon):
    """20% of 600 = 120.00 (below cap of 200)"""
    discount = CouponService.calculate_discount(base_coupon, Decimal("600.00"))
    assert discount == Decimal("120.00")


def test_calculate_discount_percentage_capped_by_maximum_discount(base_coupon):
    """20% of 2000 = 400.00, but capped at 200.00"""
    discount = CouponService.calculate_discount(base_coupon, Decimal("2000.00"))
    assert discount == Decimal("200.00")


def test_calculate_discount_fixed_amount(fixed_coupon):
    """Flat 150 off 500 = 150.00"""
    discount = CouponService.calculate_discount(fixed_coupon, Decimal("500.00"))
    assert discount == Decimal("150.00")


def test_calculate_discount_fixed_amount_capped_by_subtotal(fixed_coupon):
    """Flat 150 off 100 = 100.00 (cannot exceed subtotal)"""
    discount = CouponService.calculate_discount(fixed_coupon, Decimal("100.00"))
    assert discount == Decimal("100.00")


def test_calculate_discount_zero_subtotal(base_coupon):
    """Subtotal of 0 or negative yields 0.00"""
    assert CouponService.calculate_discount(base_coupon, Decimal("0.00")) == Decimal("0.00")
    assert CouponService.calculate_discount(base_coupon, Decimal("-10.00")) == Decimal("0.00")
    assert CouponService.calculate_discount(None, Decimal("500.00")) == Decimal("0.00")


# ==============================================================================
# 6, 7, 8, 9, 10, 11, 12, 13: Coupon Validations
# ==============================================================================

@pytest.mark.asyncio
async def test_validate_coupon_nonexistent_code():
    db = AsyncMock()
    with patch("app.services.coupon_service.CouponRepository.get_by_code", return_value=None):
        valid, msg, coup, discount = await CouponService.validate_coupon(
            db, "INVALIDCODE", Decimal("1000.00")
        )
        assert valid is False
        assert "not found" in msg
        assert coup is None
        assert discount == Decimal("0.00")


@pytest.mark.asyncio
async def test_validate_coupon_inactive(base_coupon):
    base_coupon.is_active = False
    db = AsyncMock()
    valid, msg, coup, discount = await CouponService.validate_coupon(
        db, base_coupon, Decimal("1000.00")
    )
    assert valid is False
    assert "no longer active" in msg
    assert discount == Decimal("0.00")


@pytest.mark.asyncio
async def test_validate_coupon_future_start_date(base_coupon):
    now = datetime.now(timezone.utc)
    base_coupon.starts_at = now + timedelta(days=5)
    base_coupon.expires_at = now + timedelta(days=15)
    db = AsyncMock()
    valid, msg, coup, discount = await CouponService.validate_coupon(
        db, base_coupon, Decimal("1000.00")
    )
    assert valid is False
    assert "not valid yet" in msg
    assert discount == Decimal("0.00")


@pytest.mark.asyncio
async def test_validate_coupon_expired(base_coupon):
    now = datetime.now(timezone.utc)
    base_coupon.starts_at = now - timedelta(days=10)
    base_coupon.expires_at = now - timedelta(days=1)
    db = AsyncMock()
    valid, msg, coup, discount = await CouponService.validate_coupon(
        db, base_coupon, Decimal("1000.00")
    )
    assert valid is False
    assert "has expired" in msg
    assert discount == Decimal("0.00")


@pytest.mark.asyncio
async def test_validate_coupon_global_usage_limit_reached(base_coupon):
    base_coupon.usage_limit = 10
    base_coupon.used_count = 10
    db = AsyncMock()
    valid, msg, coup, discount = await CouponService.validate_coupon(
        db, base_coupon, Decimal("1000.00")
    )
    assert valid is False
    assert "total usage limit" in msg
    assert discount == Decimal("0.00")


@pytest.mark.asyncio
async def test_validate_coupon_per_user_limit_reached(base_coupon):
    base_coupon.per_user_usage_limit = 2
    mock_usage = CouponUsage(coupon_id=base_coupon.id, user_id="user-1", usage_count=2)
    db = AsyncMock()
    with patch("app.services.coupon_service.CouponRepository.get_user_usage", return_value=mock_usage):
        valid, msg, coup, discount = await CouponService.validate_coupon(
            db, base_coupon, Decimal("1000.00"), user_id="user-1"
        )
        assert valid is False
        assert "maximum allowed uses" in msg
        assert discount == Decimal("0.00")


@pytest.mark.asyncio
async def test_validate_coupon_below_minimum_order_value(base_coupon):
    """base_coupon requires min order value of ₹500"""
    db = AsyncMock()
    valid, msg, coup, discount = await CouponService.validate_coupon(
        db, base_coupon, Decimal("499.00")
    )
    assert valid is False
    assert "below the minimum required amount" in msg
    assert discount == Decimal("0.00")


@pytest.mark.asyncio
async def test_validate_coupon_valid_success(base_coupon):
    """Valid coupon: 20% on 800 = 160"""
    db = AsyncMock()
    with patch("app.services.coupon_service.CouponRepository.get_user_usage", return_value=None):
        valid, msg, coup, discount = await CouponService.validate_coupon(
            db, base_coupon, Decimal("800.00"), user_id="user-1"
        )
        assert valid is True
        assert "applied successfully" in msg
        assert coup is not None
        assert discount == Decimal("160.00")


# ==============================================================================
# 14, 15, 16: Admin Operations
# ==============================================================================

@pytest.mark.asyncio
async def test_admin_create_coupon_duplicate_code_rejected(base_coupon):
    now = datetime.now(timezone.utc)
    payload = CouponCreateRequest(
        code="SAVE20",
        name="Another Save 20",
        discount_type="PERCENTAGE",
        discount_value=Decimal("20.00"),
        starts_at=now,
        expires_at=now + timedelta(days=10),
    )
    db = AsyncMock()
    with patch("app.services.coupon_service.CouponRepository.get_by_code", return_value=base_coupon):
        with pytest.raises(CartifyException) as exc_info:
            await CouponService.admin_create_coupon(db, payload)
        assert exc_info.value.status_code == 400
        assert exc_info.value.code == "COUPON_ALREADY_EXISTS"


def test_admin_create_coupon_invalid_percentage_rejected():
    now = datetime.now(timezone.utc)
    with pytest.raises(ValueError, match="Percentage discount must be between 1 and 100"):
        CouponCreateRequest(
            code="INVALID105",
            name="Invalid 105 Percent",
            discount_type="PERCENTAGE",
            discount_value=Decimal("105.00"),
            starts_at=now,
            expires_at=now + timedelta(days=10),
        )


def test_admin_create_coupon_expires_before_starts_rejected():
    now = datetime.now(timezone.utc)
    with pytest.raises(ValueError, match="expires_at must be strictly after starts_at"):
        CouponCreateRequest(
            code="TIMEWARP",
            name="Time Warp",
            discount_type="FIXED_AMOUNT",
            discount_value=Decimal("50.00"),
            starts_at=now,
            expires_at=now - timedelta(days=1),
        )
