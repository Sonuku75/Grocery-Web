"""003_categories_table

Revision ID: 003_categories_table
Revises: 002_addresses_table
Create Date: 2026-09-11 22:10:00.000000

Module 3: Categories & Subcategories Management
Creates categories table with self-referencing foreign key, unique slug, and query-optimizing indexes.
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = "003_categories_table"
down_revision: Union[str, None] = "002_addresses_table"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

def upgrade() -> None:
    op.create_table(
        "categories",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("name", sa.String(100), nullable=False),
        sa.Column("slug", sa.String(120), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("icon", sa.String(64), server_default="Compass", nullable=True),
        sa.Column("image_url", sa.String(1024), nullable=True),
        sa.Column(
            "parent_id",
            sa.String(36),
            sa.ForeignKey("categories.id", ondelete="CASCADE"),
            nullable=True,
        ),
        sa.Column("is_active", sa.Boolean(), server_default=sa.text("true"), nullable=False),
        sa.Column("sort_order", sa.Integer(), server_default=sa.text("0"), nullable=False),
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
    )
    op.create_index("ix_categories_slug", "categories", ["slug"], unique=True)
    op.create_index("ix_categories_parent_id", "categories", ["parent_id"])
    op.create_index("ix_categories_is_active", "categories", ["is_active"])
    op.create_index("idx_categories_active_sort", "categories", ["is_active", "sort_order", "name"])
    op.create_index("idx_categories_parent_active", "categories", ["parent_id", "is_active", "sort_order"])

def downgrade() -> None:
    op.drop_table("categories")
