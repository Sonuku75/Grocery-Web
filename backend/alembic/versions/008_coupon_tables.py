"""008_coupon_tables

Revision ID: 008_coupon_tables
Revises: 007_cart_tables
Create Date: 2026-09-13 04:05:00.000000

Module 8: Coupons & Offers
Creates coupons and coupon_usages tables:
- coupons: uppercase unique code, discount_type, values, validity window, limits
- coupon_usages: tracks per-user coupon consumption with unique (coupon_id, user_id)
- carts: adds nullable coupon_id foreign key with SET NULL on delete
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = "008_coupon_tables"
down_revision: Union[str, None] = "007_cart_tables"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. coupons table
    op.create_table(
        "coupons",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("code", sa.String(64), nullable=False),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("discount_type", sa.String(32), nullable=False),
        sa.Column("discount_value", sa.Numeric(10, 2), nullable=False),
        sa.Column("minimum_order_value", sa.Numeric(10, 2), server_default="0.00", nullable=False),
        sa.Column("maximum_discount", sa.Numeric(10, 2), nullable=True),
        sa.Column("starts_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("usage_limit", sa.Integer(), nullable=True),
        sa.Column("per_user_usage_limit", sa.Integer(), nullable=True),
        sa.Column("used_count", sa.Integer(), server_default="0", nullable=False),
        sa.Column("is_active", sa.Boolean(), server_default=sa.text("true"), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.UniqueConstraint("code", name="uq_coupons_code"),
        sa.CheckConstraint("discount_value > 0", name="chk_coupon_discount_value_positive"),
        sa.CheckConstraint("minimum_order_value >= 0", name="chk_coupon_min_order_non_negative"),
    )
    op.create_index("idx_coupons_code", "coupons", ["code"])
    op.create_index("idx_coupons_active_validity", "coupons", ["is_active", "starts_at", "expires_at"])

    # 2. coupon_usages table
    op.create_table(
        "coupon_usages",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column(
            "coupon_id",
            sa.String(36),
            sa.ForeignKey("coupons.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "user_id",
            sa.String(36),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("usage_count", sa.Integer(), server_default="1", nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.UniqueConstraint("coupon_id", "user_id", name="uq_coupon_usages_coupon_user"),
    )
    op.create_index("idx_coupon_usages_lookup", "coupon_usages", ["coupon_id", "user_id"])

    # 3. Add coupon_id to carts
    op.add_column(
        "carts",
        sa.Column(
            "coupon_id",
            sa.String(36),
            sa.ForeignKey("coupons.id", ondelete="SET NULL"),
            nullable=True,
        ),
    )
    op.create_index("idx_carts_coupon_id", "carts", ["coupon_id"])


def downgrade() -> None:
    op.drop_index("idx_carts_coupon_id", table_name="carts")
    op.drop_column("carts", "coupon_id")

    op.drop_index("idx_coupon_usages_lookup", table_name="coupon_usages")
    op.drop_table("coupon_usages")

    op.drop_index("idx_coupons_active_validity", table_name="coupons")
    op.drop_index("idx_coupons_code", table_name="coupons")
    op.drop_table("coupons")
