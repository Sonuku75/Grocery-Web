"""
Cartify Coupon Service (Module 8)

Domain business logic for coupon evaluation, discount calculations, and administration:
- Authoritative server-side calculations (PERCENTAGE with cap, FIXED_AMOUNT)
- Strict multi-step validation order (existence -> active -> date -> global limit -> user limit -> min value)
- Discount bounded: 0 <= discount <= subtotal
- Admin management with collision checking and data integrity
"""

import logging
from datetime import datetime, timezone
from decimal import Decimal
from typing import List, Optional, Tuple, Union
from fastapi import status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.errors import CartifyException, NotFoundError
from app.models.coupon import Coupon, DiscountType as ModelDiscountType
from app.repositories.coupon import CouponRepository
from app.schemas.coupon import (
    CouponCreateRequest,
    CouponDetailResponse,
    CouponListResponse,
    CouponSummary,
    CouponUpdateRequest,
    DiscountType,
)

logger = logging.getLogger("cartify.coupon")


class CouponService:
    @classmethod
    def calculate_discount(cls, coupon: Optional[Coupon], subtotal: Decimal) -> Decimal:
        """
        Calculates the exact discount for a given coupon and subtotal.
        Guaranteed: 0 <= discount <= subtotal.
        """
        if not coupon or subtotal <= Decimal("0.00"):
            return Decimal("0.00")

        subtotal_dec = Decimal(str(subtotal))
        discount_val = Decimal(str(coupon.discount_value))

        dtype = coupon.discount_type.upper() if isinstance(coupon.discount_type, str) else coupon.discount_type.value
        if dtype == DiscountType.PERCENTAGE.value:
            raw_discount = (subtotal_dec * discount_val / Decimal("100")).quantize(Decimal("0.01"))
            if coupon.maximum_discount is not None:
                max_discount = Decimal(str(coupon.maximum_discount)).quantize(Decimal("0.01"))
                raw_discount = min(raw_discount, max_discount)
        else:
            # FIXED_AMOUNT
            raw_discount = discount_val.quantize(Decimal("0.01"))

        # Discount cannot exceed subtotal and cannot be negative
        discount = min(raw_discount, subtotal_dec)
        discount = max(Decimal("0.00"), discount)
        return discount.quantize(Decimal("0.01"))

    @classmethod
    async def validate_coupon(
        cls,
        db: AsyncSession,
        code_or_coupon: Union[str, Coupon],
        subtotal: Decimal,
        user_id: Optional[str] = None,
    ) -> Tuple[bool, str, Optional[Coupon], Decimal]:
        """
        Validates coupon eligibility against an order/cart subtotal and user.
        Returns (is_valid, message, coupon_model, calculated_discount).
        """
        if isinstance(code_or_coupon, str):
            coupon = await CouponRepository.get_by_code(db, code_or_coupon)
            if not coupon:
                return False, f"Coupon code '{code_or_coupon.strip().upper()}' not found.", None, Decimal("0.00")
        else:
            coupon = code_or_coupon

        if not coupon.is_active:
            return False, f"Coupon '{coupon.code}' is no longer active.", coupon, Decimal("0.00")

        now = datetime.now(timezone.utc)
        starts_at = coupon.starts_at if coupon.starts_at.tzinfo else coupon.starts_at.replace(tzinfo=timezone.utc)
        expires_at = coupon.expires_at if coupon.expires_at.tzinfo else coupon.expires_at.replace(tzinfo=timezone.utc)

        if now < starts_at:
            return False, f"Coupon '{coupon.code}' is not valid yet.", coupon, Decimal("0.00")

        if now > expires_at:
            return False, f"Coupon '{coupon.code}' has expired.", coupon, Decimal("0.00")

        if coupon.usage_limit is not None and coupon.used_count >= coupon.usage_limit:
            return False, f"Coupon '{coupon.code}' has reached its total usage limit.", coupon, Decimal("0.00")

        if user_id and coupon.per_user_usage_limit is not None:
            user_usage = await CouponRepository.get_user_usage(db, coupon.id, user_id)
            if user_usage and user_usage.usage_count >= coupon.per_user_usage_limit:
                return (
                    False,
                    f"You have reached the maximum allowed uses for coupon '{coupon.code}'.",
                    coupon,
                    Decimal("0.00"),
                )

        min_val = Decimal(str(coupon.minimum_order_value or "0.00"))
        subtotal_dec = Decimal(str(subtotal))
        if subtotal_dec < min_val:
            return (
                False,
                f"Cart subtotal (₹{subtotal_dec}) is below the minimum required amount of ₹{min_val} for coupon '{coupon.code}'.",
                coupon,
                Decimal("0.00"),
            )

        discount = cls.calculate_discount(coupon, subtotal_dec)
        return True, "Coupon applied successfully!", coupon, discount

    @classmethod
    async def get_public_coupons(
        cls, db: AsyncSession, limit: int = 50, offset: int = 0
    ) -> CouponListResponse:
        """
        Retrieves active public coupons for promotion / offers display.
        """
        coupons = await CouponRepository.get_active_public_coupons(db, limit=limit, offset=offset)
        total = await CouponRepository.count_active_public_coupons(db)
        items = [CouponSummary.model_validate(c) for c in coupons]
        return CouponListResponse(items=items, total=total)

    @classmethod
    async def admin_list_coupons(
        cls,
        db: AsyncSession,
        is_active: Optional[bool] = None,
        search: Optional[str] = None,
        limit: int = 50,
        offset: int = 0,
    ) -> Tuple[List[CouponDetailResponse], int]:
        """
        Retrieves coupons for admin dashboard.
        """
        coupons, total = await CouponRepository.list_admin_coupons(
            db, is_active=is_active, search=search, limit=limit, offset=offset
        )
        items = [CouponDetailResponse.model_validate(c) for c in coupons]
        return items, total

    @classmethod
    async def admin_create_coupon(
        cls, db: AsyncSession, coupon_in: CouponCreateRequest
    ) -> CouponDetailResponse:
        """
        Creates a new coupon code.
        """
        code = coupon_in.code.strip().upper()
        existing = await CouponRepository.get_by_code(db, code)
        if existing:
            raise CartifyException(
                status_code=status.HTTP_400_BAD_REQUEST,
                message=f"A coupon with code '{code}' already exists.",
                code="COUPON_ALREADY_EXISTS",
            )

        coupon = await CouponRepository.create_coupon(db, coupon_in)
        return CouponDetailResponse.model_validate(coupon)

    @classmethod
    async def admin_update_coupon(
        cls, db: AsyncSession, coupon_id: str, coupon_update: CouponUpdateRequest
    ) -> CouponDetailResponse:
        """
        Updates an existing coupon.
        """
        coupon = await CouponRepository.get_by_id(db, coupon_id)
        if not coupon:
            raise NotFoundError("Coupon", coupon_id)

        update_data = coupon_update.model_dump(exclude_unset=True)

        # Cross-field validations if dates or discount values are modified
        new_starts_at = update_data.get("starts_at", coupon.starts_at)
        new_expires_at = update_data.get("expires_at", coupon.expires_at)
        if new_expires_at <= new_starts_at:
            raise CartifyException(
                status_code=status.HTTP_400_BAD_REQUEST,
                message="expires_at must be strictly after starts_at.",
                code="INVALID_COUPON_DATES",
            )

        new_dtype = update_data.get("discount_type", coupon.discount_type)
        if hasattr(new_dtype, "value"):
            new_dtype = new_dtype.value
        new_dtype_str = str(new_dtype).upper()

        new_val = update_data.get("discount_value", coupon.discount_value)
        if new_dtype_str == DiscountType.PERCENTAGE.value:
            if Decimal(str(new_val)) <= 0 or Decimal(str(new_val)) > 100:
                raise CartifyException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    message="Percentage discount must be between 1 and 100.",
                    code="INVALID_DISCOUNT_VALUE",
                )

        updated_coupon = await CouponRepository.update_coupon(db, coupon, update_data)
        return CouponDetailResponse.model_validate(updated_coupon)
