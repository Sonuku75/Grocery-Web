"""015_account_profile_tables

Revision ID: 015_account_profile_tables
Revises: 014_review_tables
Create Date: 2026-09-14 14:00:00.000000

Module 15.1: Account & Customer Profile (Database + Secure Backend Foundation)
Creates tables for:
- user_profiles (profile extension with PII minimization)
- account_security_events (audit trail for security events)
- user_sessions (session records for multi-device management)
- account_deletion_requests (non-destructive account deletion lifecycle)
- account_change_requests (staged verification for email/phone changes)
"""

from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = "015_account_profile_tables"
down_revision: Union[str, None] = "014_review_tables"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. user_profiles
    op.create_table(
        "user_profiles",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column(
            "user_id",
            sa.String(36),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("date_of_birth", sa.Date(), nullable=True),
        sa.Column("bio", sa.String(500), nullable=True),
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
        sa.UniqueConstraint("user_id", name="uq_user_profiles_user_id"),
    )
    op.create_index("ix_user_profiles_user_id", "user_profiles", ["user_id"])

    # 2. account_security_events
    op.create_table(
        "account_security_events",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column(
            "user_id",
            sa.String(36),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("event_type", sa.String(50), nullable=False),
        sa.Column("ip_address", sa.String(45), nullable=True),
        sa.Column("user_agent", sa.String(512), nullable=True),
        sa.Column("request_id", sa.String(64), nullable=True),
        sa.Column("metadata_json", sa.JSON(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
    )
    op.create_index("ix_account_security_events_user_id", "account_security_events", ["user_id"])
    op.create_index("ix_account_security_events_event_type", "account_security_events", ["event_type"])
    op.create_index(
        "ix_account_security_events_user_created",
        "account_security_events",
        ["user_id", "created_at"],
    )

    # 3. user_sessions
    op.create_table(
        "user_sessions",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column(
            "user_id",
            sa.String(36),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("session_identifier", sa.String(64), unique=True, nullable=False),
        sa.Column("device_name", sa.String(100), nullable=True),
        sa.Column("platform", sa.String(30), nullable=True),
        sa.Column("ip_address", sa.String(45), nullable=True),
        sa.Column("user_agent", sa.String(512), nullable=True),
        sa.Column(
            "last_seen_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("revoked_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index("ix_user_sessions_user_id", "user_sessions", ["user_id"])
    op.create_index("ix_user_sessions_identifier", "user_sessions", ["session_identifier"])
    op.create_index(
        "ix_user_sessions_lookup",
        "user_sessions",
        ["user_id", "revoked_at", "expires_at"],
    )

    # 4. account_deletion_requests
    op.create_table(
        "account_deletion_requests",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column(
            "user_id",
            sa.String(36),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("status", sa.String(20), server_default="PENDING", nullable=False),
        sa.Column("reason", sa.String(255), nullable=True),
        sa.Column(
            "requested_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column("scheduled_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("cancelled_at", sa.DateTime(timezone=True), nullable=True),
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
    )
    op.create_index("ix_account_deletion_user_id", "account_deletion_requests", ["user_id"])
    op.create_index(
        "ix_account_deletion_user_status",
        "account_deletion_requests",
        ["user_id", "status"],
    )

    # 5. account_change_requests
    op.create_table(
        "account_change_requests",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column(
            "user_id",
            sa.String(36),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("change_type", sa.String(20), nullable=False),
        sa.Column("target_value", sa.String(255), nullable=False),
        sa.Column("verification_token_hash", sa.String(64), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("is_verified", sa.Boolean(), server_default=sa.text("false"), nullable=False),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
    )
    op.create_index("ix_account_change_user_id", "account_change_requests", ["user_id"])
    op.create_index(
        "ix_account_change_token_hash",
        "account_change_requests",
        ["verification_token_hash"],
    )
    op.create_index(
        "ix_account_change_user_type",
        "account_change_requests",
        ["user_id", "change_type", "is_verified"],
    )


def downgrade() -> None:
    op.drop_table("account_change_requests")
    op.drop_table("account_deletion_requests")
    op.drop_table("user_sessions")
    op.drop_table("account_security_events")
    op.drop_table("user_profiles")
