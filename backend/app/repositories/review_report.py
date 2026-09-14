"""
Cartify Review Report Repository (Module 14)

Data access for review moderation reports:
- Uniqueness / spam abuse protection checks per (review_id, user_id)
- Report persistence and audit lifecycle
- Admin reporting queue with status filtering
"""

from datetime import datetime, timezone
from typing import List, Optional, Tuple
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.review_report import ReviewReport, ReportStatus


class ReviewReportRepository:
    @classmethod
    async def get_by_id(
        cls,
        db: AsyncSession,
        report_id: str,
    ) -> Optional[ReviewReport]:
        """
        Retrieves a report by its primary key ID.
        """
        stmt = (
            select(ReviewReport)
            .options(
                selectinload(ReviewReport.review),
                selectinload(ReviewReport.user),
            )
            .where(ReviewReport.id == report_id)
        )
        res = await db.execute(stmt)
        return res.scalar_one_or_none()

    @classmethod
    async def has_reported(
        cls,
        db: AsyncSession,
        review_id: str,
        user_id: str,
    ) -> bool:
        """
        Checks if the user has already reported this review.
        """
        stmt = select(ReviewReport.id).where(
            ReviewReport.review_id == review_id,
            ReviewReport.user_id == user_id,
        )
        res = await db.execute(stmt)
        return res.scalar_one_or_none() is not None

    @classmethod
    async def create(
        cls,
        db: AsyncSession,
        report_data: dict,
    ) -> ReviewReport:
        """
        Persists a new review report.
        """
        report = ReviewReport(**report_data)
        db.add(report)
        await db.flush()
        return report

    @classmethod
    async def list_reports(
        cls,
        db: AsyncSession,
        status: Optional[str] = None,
        review_id: Optional[str] = None,
        limit: int = 50,
        offset: int = 0,
    ) -> Tuple[List[ReviewReport], int]:
        """
        Lists reports for admin moderation with optional filters.
        """
        limit = min(max(1, limit), 100)
        base_where = []
        if status and status.strip():
            base_where.append(ReviewReport.status == status.strip().upper())
        if review_id and review_id.strip():
            base_where.append(ReviewReport.review_id == review_id.strip())

        count_stmt = select(func.count(ReviewReport.id))
        if base_where:
            count_stmt = count_stmt.where(*base_where)
        count_res = await db.execute(count_stmt)
        total_count = int(count_res.scalar_one() or 0)

        stmt = (
            select(ReviewReport)
            .options(
                selectinload(ReviewReport.review),
                selectinload(ReviewReport.user),
            )
            .order_by(ReviewReport.created_at.desc())
            .offset(offset)
            .limit(limit)
        )
        if base_where:
            stmt = stmt.where(*base_where)

        res = await db.execute(stmt)
        items = list(res.scalars().all())
        return items, total_count

    @classmethod
    async def update_status(
        cls,
        db: AsyncSession,
        report: ReviewReport,
        new_status: str,
    ) -> ReviewReport:
        """
        Updates report status (e.g. REVIEWED, DISMISSED, ACTION_TAKEN).
        """
        report.status = new_status
        report.updated_at = datetime.now(timezone.utc)
        await db.flush()
        return report
