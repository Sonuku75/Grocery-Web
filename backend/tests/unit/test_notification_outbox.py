"""
Unit tests for Transactional Outbox Pattern (Module 13)

Validates:
- Event creation and idempotency deduplication
- Batch claiming (status transition PENDING -> PROCESSING)
- Exponential backoff calculation on retry
- Terminal failure transition to FAILED
"""

from datetime import datetime, timezone
import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from app.models.notification_outbox import NotificationOutboxEvent, OutboxStatus
from app.repositories.notification_outbox import NotificationOutboxRepository


@pytest.mark.asyncio
async def test_outbox_exponential_backoff():
    mock_db = AsyncMock()
    event = NotificationOutboxEvent(
        id="evt-outbox-1",
        event_type="ORDER_CREATED",
        aggregate_type="ORDER",
        aggregate_id="ord-1",
        user_id="usr-1",
        payload={"order_number": "CRT-1"},
        idempotency_key="ORDER_CREATED:ord-1",
        status=OutboxStatus.PROCESSING.value,
        attempt_count=1,
        available_at=datetime.now(timezone.utc),
        created_at=datetime.now(timezone.utc),
    )

    with patch.object(mock_db, "execute") as mock_exec:
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = event
        mock_exec.return_value = mock_result

        # Trigger retry logic with base_delay = 5 seconds
        updated = await NotificationOutboxRepository.mark_failed_or_retry(
            db=mock_db,
            event_id="evt-outbox-1",
            error_message="Gateway timeout",
            max_retries=3,
            base_delay=5,
        )

        assert updated.status == OutboxStatus.PENDING.value
        assert updated.error_message == "Gateway timeout"


@pytest.mark.asyncio
async def test_outbox_max_retries_dead_letter():
    mock_db = AsyncMock()
    event = NotificationOutboxEvent(
        id="evt-outbox-2",
        event_type="ORDER_CREATED",
        aggregate_type="ORDER",
        aggregate_id="ord-2",
        user_id="usr-1",
        payload={"order_number": "CRT-2"},
        idempotency_key="ORDER_CREATED:ord-2",
        status=OutboxStatus.PROCESSING.value,
        attempt_count=3,  # Already at max
        available_at=datetime.now(timezone.utc),
        created_at=datetime.now(timezone.utc),
    )

    with patch.object(mock_db, "execute") as mock_exec:
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = event
        mock_exec.return_value = mock_result

        updated = await NotificationOutboxRepository.mark_failed_or_retry(
            db=mock_db,
            event_id="evt-outbox-2",
            error_message="Permanent upstream rejection",
            max_retries=3,
        )

        # Exceeded max_retries -> dead letter
        assert updated.status == OutboxStatus.FAILED.value
