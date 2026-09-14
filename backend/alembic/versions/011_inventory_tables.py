"""011_inventory_tables

Revision ID: 011_inventory_tables
Revises: 010_order_tables
Create Date: 2026-09-13 23:55:00.000000

Module 11: Inventory Management
Creates inventory tracking tables, audit transactions, and concurrency constraints:
- inventory: variant-level stock, reservations, and low-stock thresholds
- inventory_transactions: immutable audit log tracking every quantity mutation with actor and references
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = "011_inventory_tables"
down_revision: Union[str, None] = "010_order_tables"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. inventory table
    op.create_table(
        "inventory",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column(
            "variant_id",
            sa.String(36),
            sa.ForeignKey("product_variants.id", ondelete="CASCADE"),
            nullable=False,
            unique=True,
        ),
        sa.Column("quantity", sa.Integer(), server_default="0", nullable=False),
        sa.Column("reserved_quantity", sa.Integer(), server_default="0", nullable=False),
        sa.Column("low_stock_threshold", sa.Integer(), server_default="5", nullable=False),
        sa.Column("is_active", sa.Boolean(), server_default="true", nullable=False),
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
            onupdate=sa.func.now(),
            nullable=False,
        ),
        sa.CheckConstraint("quantity >= 0", name="chk_inventory_quantity_non_negative"),
        sa.CheckConstraint("reserved_quantity >= 0", name="chk_inventory_reserved_non_negative"),
        sa.CheckConstraint("low_stock_threshold >= 0", name="chk_inventory_low_stock_non_negative"),
        sa.CheckConstraint("reserved_quantity <= quantity", name="chk_inventory_reserved_le_quantity"),
    )

    op.create_index("idx_inventory_variant_id", "inventory", ["variant_id"])
    op.create_index("idx_inventory_is_active", "inventory", ["is_active"])
    op.create_index("idx_inventory_variant_active", "inventory", ["variant_id", "is_active"])
    op.create_index("idx_inventory_qty_reserved", "inventory", ["quantity", "reserved_quantity"])

    # 2. inventory_transactions table
    op.create_table(
        "inventory_transactions",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column(
            "inventory_id",
            sa.String(36),
            sa.ForeignKey("inventory.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "variant_id",
            sa.String(36),
            sa.ForeignKey("product_variants.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("transaction_type", sa.String(32), nullable=False),
        sa.Column("quantity_change", sa.Integer(), nullable=False),
        sa.Column("quantity_before", sa.Integer(), nullable=False),
        sa.Column("quantity_after", sa.Integer(), nullable=False),
        sa.Column("reference_type", sa.String(64), nullable=True),
        sa.Column("reference_id", sa.String(64), nullable=True),
        sa.Column("reason", sa.String(255), nullable=True),
        sa.Column(
            "created_by_user_id",
            sa.String(36),
            sa.ForeignKey("users.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
    )

    op.create_index("idx_inv_trans_inventory_id", "inventory_transactions", ["inventory_id"])
    op.create_index("idx_inv_trans_variant_id", "inventory_transactions", ["variant_id"])
    op.create_index("idx_inv_trans_type", "inventory_transactions", ["transaction_type"])
    op.create_index("idx_inv_trans_variant_created", "inventory_transactions", ["variant_id", "created_at"])
    op.create_index("idx_inv_trans_ref", "inventory_transactions", ["reference_type", "reference_id"])


def downgrade() -> None:
    op.drop_table("inventory_transactions")
    op.drop_table("inventory")
