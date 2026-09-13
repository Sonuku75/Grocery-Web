"""005_search_indexes

Revision ID: 005_search_indexes
Revises: 004_products_tables
Create Date: 2026-09-13 02:30:00.000000

Module 5: Search & Product Discovery
Creates search-optimized btree indexes for fast prefix and substring search:
- idx_products_active_name on products (is_active, name)
- idx_products_name on products (name)
"""
from typing import Sequence, Union
from alembic import op

revision: str = "005_search_indexes"
down_revision: Union[str, None] = "004_products_tables"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_index(
        "idx_products_active_name",
        "products",
        ["is_active", "name"],
        unique=False,
    )
    op.create_index(
        "idx_products_name",
        "products",
        ["name"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index("idx_products_name", table_name="products")
    op.drop_index("idx_products_active_name", table_name="products")
