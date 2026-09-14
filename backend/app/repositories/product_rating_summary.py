"""
Cartify Product Rating Summary Repository (Module 14)

Data access and aggregation calculations for product ratings:
- Authoritative calculation directly from published, non-deleted reviews
- Fast lookup for catalog cards, search results, and product detail pages
- Upsert transactional synchronization
"""

from datetime import datetime, timezone
from decimal import Decimal
from typing import Any, Dict, Optional
from sqlalchemy import case, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.product_rating_summary import ProductRatingSummary
from app.models.review import Review, ReviewStatus


class ProductRatingSummaryRepository:
    @classmethod
    async def get_by_product_id(
        cls,
        db: AsyncSession,
        product_id: str,
    ) -> Optional[ProductRatingSummary]:
        """
        Retrieves cached/materialized rating summary for a product.
        """
        stmt = select(ProductRatingSummary).where(
            ProductRatingSummary.product_id == product_id
        )
        res = await db.execute(stmt)
        return res.scalar_one_or_none()

    @classmethod
    async def calculate_from_reviews(
        cls,
        db: AsyncSession,
        product_id: str,
    ) -> Dict[str, Any]:
        """
        Executes authoritative database aggregate query directly on the reviews table.
        Considers ONLY PUBLISHED, non-deleted reviews.
        """
        stmt = (
            select(
                func.count(Review.id).label("total_reviews"),
                func.coalesce(func.avg(Review.rating), 0.0).label("avg_rating"),
                func.coalesce(func.sum(case((Review.rating == 1, 1), else_=0)), 0).label("r1"),
                func.coalesce(func.sum(case((Review.rating == 2, 1), else_=0)), 0).label("r2"),
                func.coalesce(func.sum(case((Review.rating == 3, 1), else_=0)), 0).label("r3"),
                func.coalesce(func.sum(case((Review.rating == 4, 1), else_=0)), 0).label("r4"),
                func.coalesce(func.sum(case((Review.rating == 5, 1), else_=0)), 0).label("r5"),
            )
            .where(
                Review.product_id == product_id,
                Review.status == ReviewStatus.PUBLISHED.value,
                Review.deleted_at.is_(None),
            )
        )
        res = await db.execute(stmt)
        row = res.first()

        total = int(row.total_reviews if row else 0)
        avg = Decimal(str(round(float(row.avg_rating if row else 0.0), 2)))
        r1 = int(row.r1 if row else 0)
        r2 = int(row.r2 if row else 0)
        r3 = int(row.r3 if row else 0)
        r4 = int(row.r4 if row else 0)
        r5 = int(row.r5 if row else 0)

        return {
            "total_reviews": total,
            "average_rating": avg,
            "rating_1_count": r1,
            "rating_2_count": r2,
            "rating_3_count": r3,
            "rating_4_count": r4,
            "rating_5_count": r5,
        }

    @classmethod
    async def upsert(
        cls,
        db: AsyncSession,
        product_id: str,
        summary_data: Dict[str, Any],
    ) -> ProductRatingSummary:
        """
        Upserts product_rating_summaries row for the specified product.
        """
        summary = await cls.get_by_product_id(db, product_id)
        now = datetime.now(timezone.utc)
        if not summary:
            summary = ProductRatingSummary(
                product_id=product_id,
                total_reviews=summary_data.get("total_reviews", 0),
                average_rating=summary_data.get("average_rating", Decimal("0.00")),
                rating_1_count=summary_data.get("rating_1_count", 0),
                rating_2_count=summary_data.get("rating_2_count", 0),
                rating_3_count=summary_data.get("rating_3_count", 0),
                rating_4_count=summary_data.get("rating_4_count", 0),
                rating_5_count=summary_data.get("rating_5_count", 0),
                updated_at=now,
            )
            db.add(summary)
        else:
            summary.total_reviews = summary_data.get("total_reviews", 0)
            summary.average_rating = summary_data.get("average_rating", Decimal("0.00"))
            summary.rating_1_count = summary_data.get("rating_1_count", 0)
            summary.rating_2_count = summary_data.get("rating_2_count", 0)
            summary.rating_3_count = summary_data.get("rating_3_count", 0)
            summary.rating_4_count = summary_data.get("rating_4_count", 0)
            summary.rating_5_count = summary_data.get("rating_5_count", 0)
            summary.updated_at = now

        await db.flush()
        return summary
