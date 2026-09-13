"""007_cart_tables

Revision ID: 007_cart_tables
Revises: 006_wishlist_table
Create Date: 2026-09-13 03:40:00.000000

Module 7: Cart & Cart Management
Creates carts and cart_items tables:
- carts: user_id unique FK with cascade delete, timestamps
- cart_items: cart_id, product_id, variant_id FKs with cascade delete
- Quantity bounded check constraint: 1 <= quantity <= 99
- Unique constraint: uq_cart_items_cart_variant (cart_id, variant_id)
- Lookup indexes on cart_id, variant_id, product_id
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = "007_cart_tables"
down_revision: Union[str, None] = "006_wishlist_table"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. carts table
    op.create_table(
        "carts",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column(
            "user_id",
            sa.String(36),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
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
        sa.UniqueConstraint("user_id", name="uq_carts_user_id"),
    )
    op.create_index("idx_carts_user_id", "carts", ["user_id"])

    # 2. cart_items table
    op.create_table(
        "cart_items",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column(
            "cart_id",
            sa.String(36),
            sa.ForeignKey("carts.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "product_id",
            sa.String(36),
            sa.ForeignKey("products.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "variant_id",
            sa.String(36),
            sa.ForeignKey("product_variants.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("quantity", sa.Integer(), nullable=False, server_default="1"),
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
        sa.UniqueConstraint("cart_id", "variant_id", name="uq_cart_items_cart_variant"),
        sa.CheckConstraint("quantity >= 1 AND quantity <= 99", name="chk_cart_item_quantity_range"),
    )
    op.create_index("idx_cart_items_cart_id", "cart_items", ["cart_id"])
    op.create_index("idx_cart_items_variant_id", "cart_items", ["variant_id"])
    op.create_index("idx_cart_items_product_id", "cart_items", ["product_id"])


def downgrade() -> None:
    op.drop_index("idx_cart_items_product_id", table_name="cart_items")
    op.drop_index("idx_cart_items_variant_id", table_name="cart_items")
    op.drop_index("idx_cart_items_cart_id", table_name="cart_items")
    op.drop_table("cart_items")

    op.drop_index("idx_carts_user_id", table_name="carts")
    op.drop_table("carts")
