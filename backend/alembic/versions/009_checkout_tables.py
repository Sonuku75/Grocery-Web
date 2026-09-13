"""009_checkout_tables

Revision ID: 009_checkout_tables
Revises: 008_coupon_tables
Create Date: 2026-09-13 04:45:00.000000

Module 9: Checkout
Creates checkout_sessions table:
- checkout_sessions: tracks purchase preparation state, pricing snapshots, address/items snapshots,
  idempotency keys, and authoritative server-side totals.
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = "009_checkout_tables"
down_revision: Union[str, None] = "008_coupon_tables"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "checkout_sessions",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column(
            "user_id",
            sa.String(36),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "cart_id",
            sa.String(36),
            sa.ForeignKey("carts.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "address_id",
            sa.String(36),
            sa.ForeignKey("addresses.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column(
            "coupon_id",
            sa.String(36),
            sa.ForeignKey("coupons.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("status", sa.String(32), server_default="ACTIVE", nullable=False),
        sa.Column("delivery_method", sa.String(64), server_default="STANDARD", nullable=False),
        sa.Column("delivery_slot", sa.String(128), nullable=True),
        sa.Column("subtotal", sa.Numeric(10, 2), nullable=False),
        sa.Column("discount_amount", sa.Numeric(10, 2), server_default="0.00", nullable=False),
        sa.Column("delivery_fee", sa.Numeric(10, 2), server_default="0.00", nullable=False),
        sa.Column("tax_amount", sa.Numeric(10, 2), server_default="0.00", nullable=False),
        sa.Column("total_amount", sa.Numeric(10, 2), nullable=False),
        sa.Column("currency", sa.String(8), server_default="INR", nullable=False),
        sa.Column("address_snapshot", sa.JSON(), nullable=True),
        sa.Column("items_snapshot", sa.JSON(), nullable=True),
        sa.Column("idempotency_key", sa.String(128), nullable=True),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
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
        sa.CheckConstraint("subtotal >= 0", name="chk_checkout_subtotal_non_negative"),
        sa.CheckConstraint("total_amount >= 0", name="chk_checkout_total_non_negative"),
    )
    op.create_index("idx_checkout_sessions_user_status", "checkout_sessions", ["user_id", "status"])
    op.create_index("idx_checkout_sessions_expires_at", "checkout_sessions", ["expires_at"])
    op.create_index("idx_checkout_sessions_idempotency", "checkout_sessions", ["idempotency_key"])
    op.create_index("idx_checkout_sessions_cart_id", "checkout_sessions", ["cart_id"])


def downgrade() -> None:
    op.drop_index("idx_checkout_sessions_cart_id", table_name="checkout_sessions")
    op.drop_index("idx_checkout_sessions_idempotency", table_name="checkout_sessions")
    op.drop_index("idx_checkout_sessions_expires_at", table_name="checkout_sessions")
    op.drop_index("idx_checkout_sessions_user_status", table_name="checkout_sessions")
    op.drop_table("checkout_sessions")
