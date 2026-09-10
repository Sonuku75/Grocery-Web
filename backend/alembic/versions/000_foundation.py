"""000_foundation

Revision ID: 000_foundation
Revises: 
Create Date: 2026-09-10 12:00:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = "000_foundation"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

def upgrade() -> None:
    # Foundation migration: ensures uuid extension is available in PostgreSQL
    op.execute('CREATE EXTENSION IF NOT EXISTS "uuid-ossp"')

def downgrade() -> None:
    pass
