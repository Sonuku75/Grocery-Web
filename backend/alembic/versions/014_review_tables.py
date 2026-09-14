"""014_review_tables

Revision ID: 014_review_tables
Revises: 013_notification_tables
Create Date: 2026-09-14 12:00:00.000000

Module 14: Reviews & Ratings (High-Security Master Implementation)
Creates tables for customer reviews, ratings, helpful votes, reports, and transactional rating summaries:
- reviews
- review_helpful_votes
- review_reports
- product_rating_summaries
"""

from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from decimal import Decimal

revision: str = "014_review_tables"
down_revision: Union[str, None] = "013_notification_tables"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. reviews
    op.create_table(
        "reviews",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column(
            "user_id",
            sa.String(36),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
            index=True,
        ),
        sa.Column(
            "product_id",
            sa.String(36),
            sa.ForeignKey("products.id", ondelete="CASCADE"),
            nullable=False,
            index=True,
        ),
        sa.Column(
            "order_id",
            sa.String(36),
            sa.ForeignKey("orders.id", ondelete="SET NULL"),
            nullable=True,
            index=True,
        ),
        sa.Column(
            "order_item_id",
            sa.String(36),
            sa.ForeignKey("order_items.id", ondelete="SET NULL"),
            nullable=True,
            index=True,
        ),
        sa.Column("rating", sa.Integer(), nullable=False),
        sa.Column("title", sa.String(150), nullable=False),
        sa.Column("body", sa.Text(), nullable=False),
        sa.Column("status", sa.String(32), nullable=False, server_default="PUBLISHED"),
        sa.Column("is_verified_purchase", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("helpful_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("CURRENT_TIMESTAMP"),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("CURRENT_TIMESTAMP"),
        ),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.CheckConstraint("rating >= 1 AND rating <= 5", name="chk_reviews_rating_range"),
        sa.CheckConstraint("helpful_count >= 0", name="chk_reviews_helpful_count_non_negative"),
        sa.UniqueConstraint("order_item_id", name="uq_reviews_order_item_id"),
        sa.UniqueConstraint("user_id", "product_id", "order_id", name="uq_reviews_user_product_order"),
    )
    op.create_index("idx_reviews_product_status", "reviews", ["product_id", "status"])
    op.create_index("idx_reviews_product_rating", "reviews", ["product_id", "rating"])
    op.create_index("idx_reviews_product_created", "reviews", ["product_id", "created_at"])
    op.create_index("idx_reviews_user_created", "reviews", ["user_id", "created_at"])
    op.create_index("idx_reviews_deleted_at", "reviews", ["deleted_at"])

    # 2. review_helpful_votes
    op.create_table(
        "review_helpful_votes",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column(
            "review_id",
            sa.String(36),
            sa.ForeignKey("reviews.id", ondelete="CASCADE"),
            nullable=False,
            index=True,
        ),
        sa.Column(
            "user_id",
            sa.String(36),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
            index=True,
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("CURRENT_TIMESTAMP"),
        ),
        sa.UniqueConstraint("review_id", "user_id", name="uq_review_helpful_votes_review_user"),
    )
    op.create_index("idx_helpful_votes_review_id", "review_helpful_votes", ["review_id"])
    op.create_index("idx_helpful_votes_user_id", "review_helpful_votes", ["user_id"])

    # 3. review_reports
    op.create_table(
        "review_reports",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column(
            "review_id",
            sa.String(36),
            sa.ForeignKey("reviews.id", ondelete="CASCADE"),
            nullable=False,
            index=True,
        ),
        sa.Column(
            "user_id",
            sa.String(36),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
            index=True,
        ),
        sa.Column("reason", sa.String(50), nullable=False),
        sa.Column("description", sa.String(1000), nullable=True),
        sa.Column("status", sa.String(32), nullable=False, server_default="PENDING"),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("CURRENT_TIMESTAMP"),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("CURRENT_TIMESTAMP"),
        ),
        sa.UniqueConstraint("review_id", "user_id", name="uq_review_reports_review_user"),
    )
    op.create_index("idx_review_reports_review_id", "review_reports", ["review_id"])
    op.create_index("idx_review_reports_user_id", "review_reports", ["user_id"])
    op.create_index("idx_review_reports_status", "review_reports", ["status"])

    # 4. product_rating_summaries
    op.create_table(
        "product_rating_summaries",
        sa.Column(
            "product_id",
            sa.String(36),
            sa.ForeignKey("products.id", ondelete="CASCADE"),
            primary_key=True,
        ),
        sa.Column("total_reviews", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("average_rating", sa.Numeric(3, 2), nullable=False, server_default="0.00"),
        sa.Column("rating_1_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("rating_2_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("rating_3_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("rating_4_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("rating_5_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("CURRENT_TIMESTAMP"),
        ),
        sa.CheckConstraint("total_reviews >= 0", name="chk_rating_summary_total_reviews"),
        sa.CheckConstraint("average_rating >= 0 AND average_rating <= 5", name="chk_rating_summary_avg_range"),
        sa.CheckConstraint(
            "rating_1_count >= 0 AND rating_2_count >= 0 AND rating_3_count >= 0 AND rating_4_count >= 0 AND rating_5_count >= 0",
            name="chk_rating_summary_counts_non_negative",
        ),
    )


def downgrade() -> None:
    op.drop_table("product_rating_summaries")
    op.drop_table("review_reports")
    op.drop_table("review_helpful_votes")
    op.drop_table("reviews")
