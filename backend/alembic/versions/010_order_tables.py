"""010_order_tables

Revision ID: 010_order_tables
Revises: 009_checkout_tables
Create Date: 2026-09-13 05:10:00.000000

Module 10: Orders & Order Management
Creates permanent order tables, item snapshots, status history, and idempotency tracking:
- orders: primary order entity storing purchase-time address & pricing snapshots
- order_items: immutable item records preserving price, SKU, product, and variant snapshots
- order_status_history: audit log tracking each status transition with timestamp and actor
- idempotency_keys: database-backed deduplication preventing duplicate orders
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = "010_order_tables"
down_revision: Union[str, None] = "009_checkout_tables"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. orders table
    op.create_table(
        "orders",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column(
            "user_id",
            sa.String(36),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("order_number", sa.String(64), unique=True, nullable=False),
        sa.Column("status", sa.String(32), server_default="PENDING", nullable=False),
        sa.Column("payment_status", sa.String(32), server_default="PENDING", nullable=False),
        sa.Column("fulfillment_status", sa.String(32), server_default="UNFULFILLED", nullable=False),
        sa.Column("currency", sa.String(8), server_default="INR", nullable=False),
        sa.Column("subtotal", sa.Numeric(10, 2), nullable=False),
        sa.Column("discount_amount", sa.Numeric(10, 2), server_default="0.00", nullable=False),
        sa.Column("delivery_fee", sa.Numeric(10, 2), server_default="0.00", nullable=False),
        sa.Column("tax_amount", sa.Numeric(10, 2), server_default="0.00", nullable=False),
        sa.Column("total_amount", sa.Numeric(10, 2), nullable=False),
        sa.Column("coupon_code", sa.String(64), nullable=True),
        sa.Column("coupon_discount_amount", sa.Numeric(10, 2), server_default="0.00", nullable=False),
        # Recipient & Address Snapshot
        sa.Column("recipient_name", sa.String(255), nullable=False),
        sa.Column("phone", sa.String(32), nullable=False),
        sa.Column("address_line_1", sa.String(255), nullable=False),
        sa.Column("address_line_2", sa.String(255), nullable=True),
        sa.Column("landmark", sa.String(255), nullable=True),
        sa.Column("city", sa.String(100), nullable=False),
        sa.Column("state", sa.String(100), nullable=False),
        sa.Column("country", sa.String(64), server_default="India", nullable=False),
        sa.Column("postal_code", sa.String(32), nullable=False),
        sa.Column("address_label", sa.String(32), server_default="Home", nullable=True),
        sa.Column("latitude", sa.Numeric(10, 7), nullable=True),
        sa.Column("longitude", sa.Numeric(10, 7), nullable=True),
        # Delivery Method & Slot
        sa.Column("delivery_method", sa.String(64), server_default="STANDARD", nullable=False),
        sa.Column("delivery_slot", sa.String(128), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column(
            "checkout_session_id",
            sa.String(36),
            sa.ForeignKey("checkout_sessions.id", ondelete="SET NULL"),
            nullable=True,
        ),
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
        sa.CheckConstraint("subtotal >= 0", name="chk_orders_subtotal_non_negative"),
        sa.CheckConstraint("total_amount >= 0", name="chk_orders_total_non_negative"),
    )
    op.create_index("idx_orders_user_id_created_at", "orders", ["user_id", "created_at"])
    op.create_index("idx_orders_status", "orders", ["status"])
    op.create_index("idx_orders_order_number", "orders", ["order_number"], unique=True)
    op.create_index("idx_orders_checkout_session_id", "orders", ["checkout_session_id"])

    # 2. order_items table
    op.create_table(
        "order_items",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column(
            "order_id",
            sa.String(36),
            sa.ForeignKey("orders.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "product_id",
            sa.String(36),
            sa.ForeignKey("products.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column(
            "variant_id",
            sa.String(36),
            sa.ForeignKey("product_variants.id", ondelete="SET NULL"),
            nullable=True,
        ),
        # Purchase-time Snapshots
        sa.Column("product_name", sa.String(255), nullable=False),
        sa.Column("variant_name", sa.String(255), nullable=True),
        sa.Column("sku", sa.String(100), nullable=True),
        sa.Column("unit_value", sa.String(50), nullable=True),
        sa.Column("unit_type", sa.String(50), nullable=True),
        sa.Column("unit_price", sa.Numeric(10, 2), nullable=False),
        sa.Column("mrp", sa.Numeric(10, 2), nullable=True),
        sa.Column("quantity", sa.Integer(), nullable=False),
        sa.Column("discount_amount", sa.Numeric(10, 2), server_default="0.00", nullable=False),
        sa.Column("line_total", sa.Numeric(10, 2), nullable=False),
        sa.Column("thumbnail_url", sa.String(1024), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.CheckConstraint("quantity >= 1", name="chk_order_items_quantity"),
        sa.CheckConstraint("unit_price >= 0", name="chk_order_items_unit_price"),
        sa.CheckConstraint("line_total >= 0", name="chk_order_items_line_total"),
    )
    op.create_index("idx_order_items_order_id", "order_items", ["order_id"])
    op.create_index("idx_order_items_product_id", "order_items", ["product_id"])
    op.create_index("idx_order_items_variant_id", "order_items", ["variant_id"])

    # 3. order_status_history table
    op.create_table(
        "order_status_history",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column(
            "order_id",
            sa.String(36),
            sa.ForeignKey("orders.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("old_status", sa.String(32), nullable=True),
        sa.Column("new_status", sa.String(32), nullable=False),
        sa.Column(
            "changed_by_user_id",
            sa.String(36),
            sa.ForeignKey("users.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("reason", sa.Text(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
    )
    op.create_index("idx_order_status_history_order_id", "order_status_history", ["order_id"])
    op.create_index("idx_order_status_history_created_at", "order_status_history", ["created_at"])

    # 4. idempotency_keys table
    op.create_table(
        "idempotency_keys",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column(
            "user_id",
            sa.String(36),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("key", sa.String(128), nullable=False),
        sa.Column("request_hash", sa.String(128), nullable=True),
        sa.Column("response_status", sa.Integer(), nullable=False),
        sa.Column("response_body", sa.JSON(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint("user_id", "key", name="uq_idempotency_user_key"),
    )
    op.create_index("idx_idempotency_lookup", "idempotency_keys", ["user_id", "key"])
    op.create_index("idx_idempotency_expires_at", "idempotency_keys", ["expires_at"])


def downgrade() -> None:
    op.drop_table("idempotency_keys")
    op.drop_table("order_status_history")
    op.drop_table("order_items")
    op.drop_table("orders")
