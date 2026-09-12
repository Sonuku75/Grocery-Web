"""002_addresses_table

Revision ID: 002_addresses_table
Revises: 001_auth_tables
Create Date: 2026-09-11 21:00:00.000000

Module 2: Location & Address Management
Creates addresses table with foreign key to users and query-supporting indexes.
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = "002_addresses_table"
down_revision: Union[str, None] = "001_auth_tables"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

def upgrade() -> None:
    op.create_table(
        "addresses",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column(
            "user_id",
            sa.String(36),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("label", sa.String(50), server_default="Home", nullable=False),
        sa.Column("recipient_name", sa.String(100), nullable=False),
        sa.Column("phone", sa.String(20), nullable=False),
        sa.Column("address_line_1", sa.String(255), nullable=False),
        sa.Column("address_line_2", sa.String(255), nullable=True),
        sa.Column("landmark", sa.String(255), nullable=True),
        sa.Column("city", sa.String(100), nullable=False),
        sa.Column("state", sa.String(100), nullable=False),
        sa.Column("country", sa.String(100), server_default="India", nullable=False),
        sa.Column("postal_code", sa.String(20), nullable=False),
        sa.Column("latitude", sa.Float(), nullable=True),
        sa.Column("longitude", sa.Float(), nullable=True),
        sa.Column("is_default", sa.Boolean(), server_default=sa.text("false"), nullable=False),
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
    op.create_index("ix_addresses_user_id", "addresses", ["user_id"])
    op.create_index("idx_addresses_user_default", "addresses", ["user_id", "is_default"])
    op.create_index("ix_addresses_postal_code", "addresses", ["postal_code"])

def downgrade() -> None:
    op.drop_table("addresses")
