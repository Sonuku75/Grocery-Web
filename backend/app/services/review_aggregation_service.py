"""
Cartify Review Aggregation Service (Module 14)

Calculates, updates, and caches authoritative product rating summaries:
- Computes total_reviews, average_rating (Decimal), and star rating distribution (1-5)
- Derives metrics strictly from published, non-deleted reviews
- Writes transactionally to product_rating_summaries table
- Invalidates and updates Redis cache-aside entries
"""

from decimal import Decimal
import json
import logging
from typing import Any, Dict
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.redis import redis_client
from app.models.product_rating_summary import ProductRatingSummary
from app.repositories.product_rating_summary import ProductRatingSummaryRepository

logger = logging.getLogger("cartify.reviews.aggregation")

CACHE_SUMMARY_TTL = 300  # 5 minutes


class ReviewAggregationService:
    @classmethod
    def _cache_key(cls, product_id: str) -> str:
        return f"review_summary:{product_id}"

    @classmethod
    async def recalculate_for_product(
        cls,
        db: AsyncSession,
        product_id: str,
    ) -> ProductRatingSummary:
        """
        Calculates authoritatively from database reviews and persists summary.
        Invalidates relevant Redis cache.
        """
        metrics = await ProductRatingSummaryRepository.calculate_from_reviews(db, product_id)
        summary = await ProductRatingSummaryRepository.upsert(db, product_id, metrics)

        # Invalidate Redis cache
        try:
            cache_key = cls._cache_key(product_id)
            await redis_client.delete(cache_key)
        except Exception as e:
            logger.warning(f"Failed to invalidate review summary cache for {product_id}: {e}")

        return summary

    @classmethod
    async def get_summary_for_product(
        cls,
        db: AsyncSession,
        product_id: str,
    ) -> Dict[str, Any]:
        """
        Retrieves rating summary for product.
        Checks Redis cache first; on miss, loads from DB (or recalculates if absent).
        """
        cache_key = cls._cache_key(product_id)

        # 1. Check Redis Cache
        try:
            cached = await redis_client.get(cache_key)
            if cached:
                data = json.loads(cached)
                return data
        except Exception as e:
            logger.warning(f"Redis get error for {cache_key}: {e}")

        # 2. Check DB summary
        summary = await ProductRatingSummaryRepository.get_by_product_id(db, product_id)
        if not summary:
            # Calculate from authoritative reviews table
            summary = await cls.recalculate_for_product(db, product_id)

        avg_float = round(float(summary.average_rating), 1) if summary.total_reviews > 0 else 0.0

        res_dict = {
            "average_rating": avg_float,
            "total_reviews": summary.total_reviews,
            "distribution": {
                "5": summary.rating_5_count,
                "4": summary.rating_4_count,
                "3": summary.rating_3_count,
                "2": summary.rating_2_count,
                "1": summary.rating_1_count,
            },
        }

        # 3. Populate Redis Cache
        try:
            await redis_client.set(cache_key, json.dumps(res_dict), ex=CACHE_SUMMARY_TTL)
        except Exception as e:
            logger.warning(f"Redis set error for {cache_key}: {e}")

        return res_dict
