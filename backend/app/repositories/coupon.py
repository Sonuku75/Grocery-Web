"""
Cartify Coupon Repository (Module 8)

Data access and query management for coupons and user coupon usages:
- Normalized code lookups (case-insensitive uppercase)
- Timezone-aware active public coupons querying
- User usage counting and limits
- Administrative coupon listing and filtering
"""

from datetime import datetime, timezone
from decimal import Decimal
from typing import List, Optional, Tuple
from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.coupon import Coupon, CouponUsage
from app.schemas.coupon import CouponCreateRequest


class CouponRepository:
    @classmethod
    async def get_by_id(cls, db: AsyncSession, coupon_id: str) -> Optional[Coupon]:
        """
        Retrieves a coupon by primary key UUID.
        """
        stmt = select(Coupon).where(Coupon.id == coupon_id)
        res = await db.execute(stmt)
        return res.scalar_one_or_none()

    @classmethod
    async def get_by_code(cls, db: AsyncSession, code: str) -> Optional[Coupon]:
        """
        Retrieves a coupon by its code (normalized to uppercase).
        """
        normalized_code = code.strip().upper()
        stmt = select(Coupon).where(Coupon.code == normalized_code)
        res = await db.execute(stmt)
        return res.scalar_one_or_none()

    @classmethod
    async def get_active_public_coupons(
        cls, db: AsyncSession, limit: int = 50, offset: int = 0
    ) -> List[Coupon]:
        """
        Retrieves all currently active, valid, and unexhausted coupons for public listing.
        """
        now = datetime.now(timezone.utc)
        stmt = (
            select(Coupon)
            .where(
                Coupon.is_active.is_(True),
                Coupon.starts_at <= now,
                Coupon.expires_at > now,
                or_(
                    Coupon.usage_limit.is_(None),
                    Coupon.used_count < Coupon.usage_limit,
                ),
            )
            .order_by(Coupon.created_at.desc())
            .offset(offset)
            .limit(limit)
        )
        res = await db.execute(stmt)
        return list(res.scalars().all())

    @classmethod
    async def count_active_public_coupons(cls, db: AsyncSession) -> int:
        """
        Counts total active public coupons.
        """
        now = datetime.now(timezone.utc)
        stmt = (
            select(func.count(Coupon.id))
            .where(
                Coupon.is_active.is_(True),
                Coupon.starts_at <= now,
                Coupon.expires_at > now,
                or_(
                    Coupon.usage_limit.is_(None),
                    Coupon.used_count < Coupon.usage_limit,
                ),
            )
        )
        res = await db.execute(stmt)
        return int(res.scalar_one() or 0)

    @classmethod
    async def list_admin_coupons(
        cls,
        db: AsyncSession,
        is_active: Optional[bool] = None,
        search: Optional[str] = None,
        limit: int = 50,
        offset: int = 0,
    ) -> Tuple[List[Coupon], int]:
        """
        Retrieves coupons for admin management with optional active filtering and search.
        """
        base_stmt = select(Coupon)
        count_stmt = select(func.count(Coupon.id))

        filters = []
        if is_active is not None:
            filters.append(Coupon.is_active == is_active)
        if search and search.strip():
            pattern = f"%{search.strip()}%"
            filters.append(
                or_(
                    Coupon.code.ilike(pattern),
                    Coupon.name.ilike(pattern),
                )
            )

        if filters:
            base_stmt = base_stmt.where(*filters)
            count_stmt = count_stmt.where(*filters)

        base_stmt = base_stmt.order_by(Coupon.created_at.desc()).offset(offset).limit(limit)

        items_res = await db.execute(base_stmt)
        count_res = await db.execute(count_stmt)

        items = list(items_res.scalars().all())
        total = int(count_res.scalar_one() or 0)
        return items, total

    @classmethod
    async def get_user_usage(
        cls, db: AsyncSession, coupon_id: str, user_id: str
    ) -> Optional[CouponUsage]:
        """
        Retrieves per-user usage record for a given coupon.
        """
        stmt = select(CouponUsage).where(
            CouponUsage.coupon_id == coupon_id,
            CouponUsage.user_id == user_id,
        )
        res = await db.execute(stmt)
        return res.scalar_one_or_none()

    @classmethod
    async def create_coupon(
        cls, db: AsyncSession, coupon_in: CouponCreateRequest
    ) -> Coupon:
        """
        Creates and persists a new coupon.
        """
        coupon = Coupon(
            code=coupon_in.code.strip().upper(),
            name=coupon_in.name.strip(),
            description=coupon_in.description.strip() if coupon_in.description else None,
            discount_type=coupon_in.discount_type.value,
            discount_value=coupon_in.discount_value,
            minimum_order_value=coupon_in.minimum_order_value,
            maximum_discount=coupon_in.maximum_discount,
            starts_at=coupon_in.starts_at,
            expires_at=coupon_in.expires_at,
            usage_limit=coupon_in.usage_limit,
            per_user_usage_limit=coupon_in.per_user_usage_limit,
            is_active=coupon_in.is_active,
        )
        db.add(coupon)
        await db.flush()
        return coupon

    @classmethod
    async def update_coupon(
        cls, db: AsyncSession, coupon: Coupon, update_data: dict
    ) -> Coupon:
        """
        Updates fields on an existing coupon.
        """
        for field, val in update_data.items():
            if val is not None:
                if field == "discount_type" and hasattr(val, "value"):
                    setattr(coupon, field, val.value)
                else:
                    setattr(coupon, field, val)
        await db.flush()
        return coupon

    @classmethod
    async def record_usage(
        cls, db: AsyncSession, coupon: Coupon, user_id: str
    ) -> CouponUsage:
        """
        Increments usage counters for a coupon and customer.
        Called during order placement (Module 10).
        """
        usage = await cls.get_user_usage(db, coupon.id, user_id)
        if usage is None:
            usage = CouponUsage(
                coupon_id=coupon.id,
                user_id=user_id,
                usage_count=1,
            )
            db.add(usage)
        else:
            usage.usage_count += 1

        coupon.used_count += 1
        await db.flush()
        return usage
