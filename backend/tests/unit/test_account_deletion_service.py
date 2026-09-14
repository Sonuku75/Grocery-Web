"""
Cartify Account Deletion Service Unit Tests (Module 15.1)

Tests safe account deletion scheduling, password verification, active order constraints,
and cancellation workflows.
"""

from datetime import datetime, timezone
from unittest.mock import AsyncMock, patch
import pytest

from app.core.errors import CartifyException, UnauthorizedError
from app.models.account_deletion import AccountDeletionRequest, AccountDeletionStatus
from app.models.user import User
from app.services.account_deletion_service import AccountDeletionService


@pytest.fixture
def mock_db():
    return AsyncMock()


@pytest.fixture
def test_user():
    return User(
        id="usr-del-1",
        name="Amitabh Bachchan",
        email="amitabh@cartify.com",
        password_hash="$2b$12$e86g5qD/qJ60c2u8D0J/v.2F7q9zD1L5oK4T2w1N0o9P8m7l6k5j4",  # fake bcrypt hash
    )


class TestAccountDeletionService:
    @pytest.mark.asyncio
    async def test_request_deletion_rejects_wrong_password(self, mock_db, test_user):
        """Rejects deletion scheduling when provided password does not match."""
        with patch("app.services.account_deletion_service.verify_password", return_value=False):
            with pytest.raises(UnauthorizedError) as exc:
                await AccountDeletionService.request_deletion(
                    db=mock_db,
                    user=test_user,
                    current_password="wrongpassword",
                )
            assert "Incorrect password" in str(exc.value)

    @pytest.mark.asyncio
    async def test_request_deletion_blocks_if_active_orders_exist(self, mock_db, test_user):
        """Prevents deletion request if customer has active in-flight orders."""
        with patch("app.services.account_deletion_service.verify_password", return_value=True), \
             patch("app.repositories.account_deletion.AccountDeletionRepository.get_pending_by_user_id", AsyncMock(return_value=None)), \
             patch.object(AccountDeletionService, "has_active_orders", AsyncMock(return_value=True)):

            with pytest.raises(CartifyException) as exc:
                await AccountDeletionService.request_deletion(
                    db=mock_db,
                    user=test_user,
                    current_password="validpassword",
                )
            assert exc.value.code == "ACTIVE_ORDERS_EXIST"

    @pytest.mark.asyncio
    async def test_request_deletion_success_schedules_grace_period(self, mock_db, test_user):
        """Successfully schedules deletion with 30-day grace period and emits security event."""
        now = datetime.now(timezone.utc)
        mock_record = AccountDeletionRequest(
            id="del-req-1",
            user_id=test_user.id,
            status=AccountDeletionStatus.PENDING,
            requested_at=now,
            scheduled_at=now,
        )

        with patch("app.services.account_deletion_service.verify_password", return_value=True), \
             patch("app.repositories.account_deletion.AccountDeletionRepository.get_pending_by_user_id", AsyncMock(return_value=None)), \
             patch.object(AccountDeletionService, "has_active_orders", AsyncMock(return_value=False)), \
             patch("app.repositories.account_deletion.AccountDeletionRepository.create", AsyncMock(return_value=mock_record)), \
             patch("app.services.security_event_service.SecurityEventService.record_security_event", AsyncMock()) as mock_sec_event:

            res = await AccountDeletionService.request_deletion(
                db=mock_db,
                user=test_user,
                current_password="validpassword",
                reason="Moving abroad",
            )

            assert res.id == "del-req-1"
            assert res.status == AccountDeletionStatus.PENDING
            assert res.grace_period_days == 30
            mock_sec_event.assert_called_once()
            call_kwargs = mock_sec_event.call_args[1]
            assert call_kwargs["event_type"] == "ACCOUNT_DELETION_REQUESTED"

    @pytest.mark.asyncio
    async def test_cancel_deletion_success(self, mock_db, test_user):
        """Cancels an existing pending deletion request."""
        mock_pending = AccountDeletionRequest(
            id="del-req-1",
            user_id=test_user.id,
            status=AccountDeletionStatus.PENDING,
        )

        with patch("app.repositories.account_deletion.AccountDeletionRepository.get_pending_by_user_id", AsyncMock(return_value=mock_pending)), \
             patch("app.repositories.account_deletion.AccountDeletionRepository.cancel", AsyncMock(return_value=True)), \
             patch("app.services.security_event_service.SecurityEventService.record_security_event", AsyncMock()) as mock_sec_event:

            cancelled = await AccountDeletionService.cancel_deletion(mock_db, test_user)

            assert cancelled is True
            mock_sec_event.assert_called_once()
            call_kwargs = mock_sec_event.call_args[1]
            assert call_kwargs["event_type"] == "ACCOUNT_DELETION_CANCELLED"
