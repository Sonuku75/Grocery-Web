"""012_payment_tables

Revision ID: 012_payment_tables
Revises: 011_inventory_tables
Create Date: 2026-09-14 07:45:00.000000

Module 12: Payments & High-Security Payment Infrastructure
Creates bank-grade payment processing, status auditing, webhook ingestion, and refund tracking tables:
- payments: provider-agnostic payment records with authoritative monetary values
- payment_status_history: append-only audit trail for status transitions
- payment_webhook_events: idempotent deduplication table for inbound gateway webhooks
- payment_refunds: full and partial refund records with strict balance constraints
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = "012_payment_tables"
down_revision: Union[str, None] = "011_inventory_tables"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. payments table
    op.create_table(
        "payments",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column(
            "order_id",
            sa.String(36),
            sa.ForeignKey("orders.id", ondelete="RESTRICT"),
            nullable=False,
            index=True,
        ),
        sa.Column(
            "user_id",
            sa.String(36),
            sa.ForeignKey("users.id", ondelete="RESTRICT"),
            nullable=False,
            index=True,
        ),
        sa.Column("provider", sa.String(32), nullable=False, index=True),
        sa.Column("provider_payment_id", sa.String(128), nullable=True, index=True),
        sa.Column("provider_order_id", sa.String(128), nullable=True, index=True),
        sa.Column("payment_method", sa.String(32), nullable=False, index=True),
        sa.Column("amount", sa.Numeric(10, 2), nullable=False),
        sa.Column("currency", sa.String(8), server_default="INR", nullable=False),
        sa.Column("status", sa.String(32), server_default="PENDING", nullable=False, index=True),
        sa.Column("failure_code", sa.String(64), nullable=True),
        sa.Column("failure_message", sa.Text(), nullable=True),
        sa.Column("payment_metadata", sa.JSON(), nullable=True),
        sa.Column("paid_at", sa.DateTime(timezone=True), nullable=True),
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
        sa.CheckConstraint("amount >= 0", name="chk_payments_amount_non_negative"),
    )
    op.create_index("idx_payments_order_id", "payments", ["order_id"])
    op.create_index("idx_payments_user_id", "payments", ["user_id"])
    op.create_index("idx_payments_status", "payments", ["status"])
    op.create_index("idx_payments_provider_order", "payments", ["provider", "provider_order_id"])
    op.create_index("idx_payments_provider_payment", "payments", ["provider", "provider_payment_id"])

    # 2. payment_status_history table (append-only audit log)
    op.create_table(
        "payment_status_history",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column(
            "payment_id",
            sa.String(36),
            sa.ForeignKey("payments.id", ondelete="CASCADE"),
            nullable=False,
            index=True,
        ),
        sa.Column("old_status", sa.String(32), nullable=True),
        sa.Column("new_status", sa.String(32), nullable=False),
        sa.Column("reason", sa.String(255), nullable=True),
        sa.Column("provider_event_reference", sa.String(128), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
    )
    op.create_index("idx_payment_status_history_payment_id", "payment_status_history", ["payment_id"])
    op.create_index("idx_payment_status_history_created_at", "payment_status_history", ["created_at"])

    # 3. payment_webhook_events table (idempotent deduplication)
    op.create_table(
        "payment_webhook_events",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("provider", sa.String(32), nullable=False),
        sa.Column("provider_event_id", sa.String(128), nullable=False),
        sa.Column("event_type", sa.String(64), nullable=False),
        sa.Column("payload_hash", sa.String(64), nullable=False),
        sa.Column("payload", sa.JSON(), nullable=False),
        sa.Column("processing_status", sa.String(32), server_default="RECEIVED", nullable=False, index=True),
        sa.Column("processed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.UniqueConstraint("provider", "provider_event_id", name="uq_payment_webhooks_provider_event"),
    )
    op.create_index("idx_payment_webhooks_status", "payment_webhook_events", ["processing_status"])
    op.create_index("idx_payment_webhooks_provider_event", "payment_webhook_events", ["provider", "provider_event_id"])

    # 4. payment_refunds table (partial and full refund tracking)
    op.create_table(
        "payment_refunds",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column(
            "payment_id",
            sa.String(36),
            sa.ForeignKey("payments.id", ondelete="RESTRICT"),
            nullable=False,
            index=True,
        ),
        sa.Column("provider_refund_id", sa.String(128), nullable=True, index=True),
        sa.Column("amount", sa.Numeric(10, 2), nullable=False),
        sa.Column("currency", sa.String(8), server_default="INR", nullable=False),
        sa.Column("reason", sa.String(255), nullable=True),
        sa.Column("status", sa.String(32), server_default="PENDING", nullable=False, index=True),
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
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            onupdate=sa.func.now(),
            nullable=False,
        ),
        sa.CheckConstraint("amount > 0", name="chk_payment_refunds_amount_positive"),
    )
    op.create_index("idx_payment_refunds_payment_id", "payment_refunds", ["payment_id"])
    op.create_index("idx_payment_refunds_status", "payment_refunds", ["status"])


def downgrade() -> None:
    op.drop_table("payment_refunds")
    op.drop_table("payment_webhook_events")
    op.drop_table("payment_status_history")
    op.drop_table("payments")
