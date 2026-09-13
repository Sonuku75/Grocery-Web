"""006_wishlist_table

Revision ID: 006_wishlist_table
Revises: 005_search_indexes
Create Date: 2026-09-13 03:15:00.000000

Module 6: Wishlist & Favorites
Creates wishlist_items table:
- UUID primary key
- user_id foreign key (CASCADE on delete)
- product_id foreign key (CASCADE on delete)
- timezone-aware created_at timestamp
- database-enforced unique constraint uq_wishlist_user_product
- composite keyset pagination index idx_wishlist_keyset (user_id, created_at, id)
- user_id and product_id lookup indexes
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = "006_wishlist_table"
down_revision: Union[str, None] = "005_search_indexes"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "wishlist_items",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column(
            "user_id",
            sa.String(36),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "product_id",
            sa.String(36),
            sa.ForeignKey("products.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.UniqueConstraint("user_id", "product_id", name="uq_wishlist_user_product"),
    )
    op.create_index("idx_wishlist_user_id", "wishlist_items", ["user_id"])
    op.create_index("idx_wishlist_product_id", "wishlist_items", ["product_id"])
    op.create_index("idx_wishlist_keyset", "wishlist_items", ["user_id", "created_at", "id"])


def downgrade() -> None:
    op.drop_index("idx_wishlist_keyset", table_name="wishlist_items")
    op.drop_index("idx_wishlist_product_id", table_name="wishlist_items")
    op.drop_index("idx_wishlist_user_id", table_name="wishlist_items")
    op.drop_table("wishlist_items")
