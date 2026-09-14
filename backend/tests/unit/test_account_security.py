"""
Cartify Account Security & Hardening Tests (Module 15.1)

Tests mass-assignment protection, staged email/phone change verification,
IDOR protection, and anti-tampering boundaries.
"""

from unittest.mock import AsyncMock, patch
import pytest
from pydantic import ValidationError

from app.core.errors import CartifyException, UnauthorizedError
from app.models.account_change_request import AccountChangeRequest, ChangeType
from app.models.user import User
from app.schemas.account import ProfileUpdateRequest
from app.services.account_service import AccountService


@pytest.fixture
def mock_db():
    return AsyncMock()


@pytest.fixture
def test_user():
    return User(
        id="usr-sec-1",
        name="Pooja Hegde",
        email="pooja@cartify.com",
        phone="+919876543210",
        password_hash="mock_bcrypt_hash",
        role="customer",
        is_active=True,
        is_verified=True,
    )


class TestAccountSecurity:
    def test_mass_assignment_rejects_privileged_fields(self):
        """Rejects client attempts to modify role, is_active, is_verified, id, or email via profile."""
        with pytest.raises(ValidationError):
            ProfileUpdateRequest(role="admin")

        with pytest.raises(ValidationError):
            ProfileUpdateRequest(is_active=False)

        with pytest.raises(ValidationError):
            ProfileUpdateRequest(is_verified=True)

        with pytest.raises(ValidationError):
            ProfileUpdateRequest(id="hacked-uuid")

        with pytest.raises(ValidationError):
            ProfileUpdateRequest(email="attacker@cartify.com")

        with pytest.raises(ValidationError):
            ProfileUpdateRequest(password_hash="fakehash")

    @pytest.mark.asyncio
    async def test_email_change_requires_valid_password(self, mock_db, test_user):
        """Email change initiation fails if current password is wrong."""
        with patch("app.services.account_service.verify_password", return_value=False):
            with pytest.raises(UnauthorizedError):
                await AccountService.initiate_email_change(
                    db=mock_db,
                    user=test_user,
                    new_email="newpooja@cartify.com",
                    current_password="badpassword",
                )

    @pytest.mark.asyncio
    async def test_email_change_rejects_duplicate_or_unchanged_email(self, mock_db, test_user):
        """Rejects email change if new email is identical or already taken."""
        with patch("app.services.account_service.verify_password", return_value=True):
            # Unchanged email
            with pytest.raises(CartifyException) as exc1:
                await AccountService.initiate_email_change(
                    db=mock_db,
                    user=test_user,
                    new_email=test_user.email,
                    current_password="validpass",
                )
            assert exc1.value.code == "EMAIL_UNCHANGED"

            # Already registered email
            existing_other_user = User(id="other-usr", email="existing@cartify.com")
            with patch("app.repositories.user.UserRepository.get_by_email", AsyncMock(return_value=existing_other_user)):
                with pytest.raises(CartifyException) as exc2:
                    await AccountService.initiate_email_change(
                        db=mock_db,
                        user=test_user,
                        new_email="existing@cartify.com",
                        current_password="validpass",
                    )
                assert exc2.value.code == "EMAIL_ALREADY_IN_USE"

    @pytest.mark.asyncio
    async def test_email_change_verification_flow(self, mock_db, test_user):
        """Successfully verifies staged email change code and updates user email."""
        from app.core.security import hash_token
        valid_otp = "849201"
        valid_hash = hash_token(valid_otp)

        mock_pending = AccountChangeRequest(
            id="req-email-1",
            user_id=test_user.id,
            change_type=ChangeType.EMAIL,
            target_value="pooja.new@cartify.com",
            verification_token_hash=valid_hash,
        )

        with patch("app.repositories.account_change_request.AccountChangeRequestRepository.get_active_by_user_and_type", AsyncMock(return_value=mock_pending)), \
             patch("app.repositories.user.UserRepository.get_by_email", AsyncMock(return_value=None)), \
             patch("app.repositories.account_change_request.AccountChangeRequestRepository.mark_completed", AsyncMock(return_value=True)), \
             patch("app.services.security_event_service.SecurityEventService.record_security_event", AsyncMock()) as mock_sec_event:

            success = await AccountService.verify_email_change(
                db=mock_db,
                user=test_user,
                verification_code=valid_otp,
            )

            assert success is True
            assert test_user.email == "pooja.new@cartify.com"
            mock_sec_event.assert_called_once()
            assert mock_sec_event.call_args[1]["event_type"] == "EMAIL_CHANGED"

    @pytest.mark.asyncio
    async def test_phone_change_verification_flow(self, mock_db, test_user):
        """Successfully verifies staged phone change code and updates user phone."""
        from app.core.security import hash_token
        valid_otp = "572914"
        valid_hash = hash_token(valid_otp)

        mock_pending = AccountChangeRequest(
            id="req-phone-1",
            user_id=test_user.id,
            change_type=ChangeType.PHONE,
            target_value="+919811122233",
            verification_token_hash=valid_hash,
        )

        with patch("app.repositories.account_change_request.AccountChangeRequestRepository.get_active_by_user_and_type", AsyncMock(return_value=mock_pending)), \
             patch("app.repositories.user.UserRepository.get_by_phone", AsyncMock(return_value=None)), \
             patch("app.repositories.account_change_request.AccountChangeRequestRepository.mark_completed", AsyncMock(return_value=True)), \
             patch("app.services.security_event_service.SecurityEventService.record_security_event", AsyncMock()) as mock_sec_event:

            success = await AccountService.verify_phone_change(
                db=mock_db,
                user=test_user,
                verification_code=valid_otp,
            )

            assert success is True
            assert test_user.phone == "+919811122233"
            mock_sec_event.assert_called_once()
            assert mock_sec_event.call_args[1]["event_type"] == "PHONE_CHANGED"

    def test_phone_validation_rejects_invalid_numbers(self):
        """Rejects malformed, non-Indian, or non-mobile phone formats."""
        from app.schemas.account import InitiatePhoneChangeRequest

        # Less than 10 digits
        with pytest.raises(ValidationError):
            InitiatePhoneChangeRequest(new_phone="12345", current_password="password123")

        # Starts with invalid initial digit (e.g. 1 or 2)
        with pytest.raises(ValidationError):
            InitiatePhoneChangeRequest(new_phone="+911234567890", current_password="password123")

        # Valid Indian number formats normalize to +91XXXXXXXXXX
        req1 = InitiatePhoneChangeRequest(new_phone="9876543210", current_password="password123")
        assert req1.new_phone == "+919876543210"

        req2 = InitiatePhoneChangeRequest(new_phone="+91 98765 43210", current_password="password123")
        assert req2.new_phone == "+919876543210"

    @pytest.mark.asyncio
    async def test_email_change_rejects_invalid_otp(self, mock_db, test_user):
        """Rejects email change when invalid OTP is presented."""
        from app.core.security import hash_token
        valid_otp = "123456"

        mock_pending = AccountChangeRequest(
            id="req-email-1",
            user_id=test_user.id,
            change_type=ChangeType.EMAIL,
            target_value="new@cartify.com",
            verification_token_hash=hash_token(valid_otp),
        )

        with patch("app.repositories.account_change_request.AccountChangeRequestRepository.get_active_by_user_and_type", AsyncMock(return_value=mock_pending)):
            with pytest.raises(CartifyException) as exc:
                await AccountService.verify_email_change(
                    db=mock_db,
                    user=test_user,
                    verification_code="999999",  # Wrong code
                )
            assert exc.value.code == "INVALID_VERIFICATION_CODE"

    @pytest.mark.asyncio
    async def test_idor_cannot_cancel_other_user_deletion(self, mock_db, test_user):
        """A user cannot cancel another user's pending deletion request."""
        from app.services.account_deletion_service import AccountDeletionService

        # When checking pending deletion for user A, user B's ID yields None
        with patch("app.repositories.account_deletion.AccountDeletionRepository.get_pending_by_user_id", AsyncMock(return_value=None)):
            with pytest.raises(Exception):
                await AccountDeletionService.cancel_deletion(mock_db, test_user)

