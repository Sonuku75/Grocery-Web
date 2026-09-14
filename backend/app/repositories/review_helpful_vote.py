"""
Cartify Review Helpful Vote Repository (Module 14)

Data access for customer helpful votes:
- Unique vote lookup and existence checks
- Safe transaction insertion and deletion
- Batch user vote resolution for list responses
"""

from typing import List, Optional, Set
from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.review_helpful_vote import ReviewHelpfulVote


class ReviewHelpfulVoteRepository:
    @classmethod
    async def get_vote(
        cls,
        db: AsyncSession,
        review_id: str,
        user_id: str,
    ) -> Optional[ReviewHelpfulVote]:
        """
        Retrieves specific user's vote on a review.
        """
        stmt = select(ReviewHelpfulVote).where(
            ReviewHelpfulVote.review_id == review_id,
            ReviewHelpfulVote.user_id == user_id,
        )
        res = await db.execute(stmt)
        return res.scalar_one_or_none()

    @classmethod
    async def has_voted(
        cls,
        db: AsyncSession,
        review_id: str,
        user_id: str,
    ) -> bool:
        """
        Quick existence check for helpful vote.
        """
        vote = await cls.get_vote(db, review_id, user_id)
        return vote is not None

    @classmethod
    async def add_vote(
        cls,
        db: AsyncSession,
        review_id: str,
        user_id: str,
    ) -> ReviewHelpfulVote:
        """
        Creates a new helpful vote within current transaction.
        """
        vote = ReviewHelpfulVote(review_id=review_id, user_id=user_id)
        db.add(vote)
        await db.flush()
        return vote

    @classmethod
    async def remove_vote(
        cls,
        db: AsyncSession,
        review_id: str,
        user_id: str,
    ) -> bool:
        """
        Deletes existing helpful vote. Returns True if a record was removed.
        """
        stmt = (
            delete(ReviewHelpfulVote)
            .where(
                ReviewHelpfulVote.review_id == review_id,
                ReviewHelpfulVote.user_id == user_id,
            )
            .execution_options(synchronize_session="fetch")
        )
        res = await db.execute(stmt)
        await db.flush()
        return (res.rowcount or 0) > 0

    @classmethod
    async def get_user_voted_review_ids(
        cls,
        db: AsyncSession,
        user_id: str,
        review_ids: List[str],
    ) -> Set[str]:
        """
        Batch resolves which reviews the user has marked as helpful.
        Eliminates N+1 queries when rendering a review list.
        """
        if not review_ids:
            return set()
        stmt = select(ReviewHelpfulVote.review_id).where(
            ReviewHelpfulVote.user_id == user_id,
            ReviewHelpfulVote.review_id.in_(review_ids),
        )
        res = await db.execute(stmt)
        return set(res.scalars().all())
