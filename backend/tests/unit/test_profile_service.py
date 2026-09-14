"""
Cartify Profile Service Unit Tests (Module 15.1)

Tests profile retrieval, sanitization, validation, and mass-assignment protection.
"""

from datetime import date, datetime, timezone
from unittest.mock import AsyncMock, patch
import pytest
from pydantic import ValidationError

from app.models.user import User
from app.models.user_profile import UserProfile
from app.schemas.account import ProfileUpdateRequest
from app.services.profile_service import ProfileService


@pytest.fixture
def mock_db():
    return AsyncMock()


@pytest.fixture
def test_user():
    now = datetime.now(timezone.utc)
    return User(
        id="usr-test-456",
        name="Sunita Rao",
        email="sunita@cartify.com",
        phone="+919876543210",
        avatar_url="https://images.cartify.com/avatar.jpg",
        password_hash="mocked_bcrypt_hash",
        role="customer",
        is_active=True,
        is_verified=True,
        created_at=now,
        updated_at=now,
    )


class TestProfileService:
    def test_schema_rejects_insecure_avatar_urls(self):
        """Rejects javascript:, data:, and insecure protocols."""
        with pytest.raises(ValidationError):
            ProfileUpdateRequest(avatar_url="javascript:alert('xss')")

        with pytest.raises(ValidationError):
            ProfileUpdateRequest(avatar_url="data:text/html;base64,PHNjcmlwdD5hbGVydCgxKTwvc2NyaXB0Pg==")

        with pytest.raises(ValidationError):
            ProfileUpdateRequest(avatar_url="http://insecure.com/pic.png")

        # Valid https and local uploads pass
        valid1 = ProfileUpdateRequest(avatar_url="https://cdn.cartify.com/pic.png")
        assert valid1.avatar_url == "https://cdn.cartify.com/pic.png"

        valid2 = ProfileUpdateRequest(avatar_url="/uploads/avatars/user123.jpg")
        assert valid2.avatar_url == "/uploads/avatars/user123.jpg"

    def test_schema_validates_date_of_birth(self):
        """Requires date_of_birth to be a past date with reasonable age limits."""
        # Future date rejected
        with pytest.raises(ValidationError):
            ProfileUpdateRequest(date_of_birth=date(2050, 1, 1))

        # Too young (< 13 years old)
        today = date.today()
        with pytest.raises(ValidationError):
            ProfileUpdateRequest(date_of_birth=date(today.year - 5, 1, 1))

        # Valid date passes
        valid = ProfileUpdateRequest(date_of_birth=date(1990, 6, 15))
        assert valid.date_of_birth == date(1990, 6, 15)

    def test_schema_sanitizes_name_and_bio(self):
        """Strips HTML script tags and excessive whitespace."""
        req = ProfileUpdateRequest(
            name="  <b>Sunita</b> <script>alert(1)</script> Rao  ",
            bio="<i>Loves fresh organic vegetables</i> <script>bad()</script>",
        )
        assert req.name == "Sunita  Rao"
        assert req.bio == "Loves fresh organic vegetables"

    @pytest.mark.asyncio
    async def test_get_profile_success(self, mock_db, test_user):
        """ProfileService.get_profile returns combined User and UserProfile data."""
        mock_profile = UserProfile(
            user_id=test_user.id,
            date_of_birth=date(1992, 3, 20),
            bio="Foodie & chef",
        )

        with patch("app.repositories.user.UserRepository.get_by_id", AsyncMock(return_value=test_user)), \
             patch("app.repositories.user_profile.UserProfileRepository.get_by_user_id", AsyncMock(return_value=mock_profile)), \
             patch("app.repositories.account_deletion.AccountDeletionRepository.get_pending_by_user_id", AsyncMock(return_value=None)):

            res = await ProfileService.get_profile(mock_db, test_user.id)

            assert res.id == test_user.id
            assert res.name == "Sunita Rao"
            assert res.email == "sunita@cartify.com"
            assert res.date_of_birth == date(1992, 3, 20)
            assert res.bio == "Foodie & chef"
            assert res.has_pending_deletion is False

    @pytest.mark.asyncio
    async def test_update_profile_success(self, mock_db, test_user):
        """ProfileService.update_profile correctly updates User and UserProfile records."""
        req = ProfileUpdateRequest(
            name="Sunita K. Rao",
            bio="Updated bio for tester",
        )

        with patch("app.repositories.user.UserRepository.update", AsyncMock()) as mock_user_update, \
             patch("app.repositories.user_profile.UserProfileRepository.upsert", AsyncMock()) as mock_profile_upsert, \
             patch("app.services.security_event_service.SecurityEventService.record_security_event", AsyncMock()) as mock_sec_event, \
             patch.object(ProfileService, "get_profile", AsyncMock()) as mock_get_prof:

            await ProfileService.update_profile(
                db=mock_db,
                user=test_user,
                data=req,
                ip_address="192.168.1.5",
                user_agent="TestAgent",
            )

            mock_user_update.assert_called_once()
            mock_profile_upsert.assert_called_once_with(mock_db, test_user.id, {"bio": "Updated bio for tester"})
            mock_sec_event.assert_called_once()
