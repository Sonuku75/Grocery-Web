"""
Cartify Account & Profile Schemas (Module 15.1)

Strict Pydantic v2 schemas providing mass-assignment protection (extra="forbid"),
input sanitization, URL scheme whitelisting, and privacy-preserving response models.
"""

from datetime import date, datetime, timezone
import re
from typing import Optional
from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator


# Disallowed URL schemes for avatar URLs
FORBIDDEN_URL_SCHEMES = ("javascript:", "data:", "vbscript:", "file:")


def sanitize_input_text(val: Optional[str], max_len: int = 500) -> Optional[str]:
    """Strips HTML script blocks, tags, and control characters."""
    if val is None:
        return None
    # Strip script blocks completely
    cleaned = re.sub(r"<script[^>]*>.*?</script>", "", val, flags=re.IGNORECASE | re.DOTALL)
    # Strip style blocks completely
    cleaned = re.sub(r"<style[^>]*>.*?</style>", "", cleaned, flags=re.IGNORECASE | re.DOTALL)
    # Strip remaining HTML tags
    cleaned = re.sub(r"<[^>]*>", "", cleaned)
    # Remove control characters except standard whitespace
    cleaned = "".join(ch for ch in cleaned if ch == "\n" or ch == "\t" or not ch.isspace() or ch == " ")
    cleaned = cleaned.strip()
    return cleaned[:max_len]


class ProfileUpdateRequest(BaseModel):
    """
    Customer profile update payload.
    Mass-assignment protected: only explicit profile fields permitted.
    """
    model_config = ConfigDict(extra="forbid")

    name: Optional[str] = Field(None, min_length=2, max_length=100)
    phone: Optional[str] = Field(None, min_length=10, max_length=15)
    avatar_url: Optional[str] = Field(None, max_length=1024)
    date_of_birth: Optional[date] = None
    bio: Optional[str] = Field(None, max_length=500)

    @field_validator("phone")
    @classmethod
    def validate_phone(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return None
        cleaned = re.sub(r"[\s\-\(\)]", "", v)
        if cleaned.startswith("+91"):
            digits = cleaned[3:]
        elif cleaned.startswith("0"):
            digits = cleaned[1:]
        else:
            digits = cleaned
        if not re.match(r"^[6-9]\d{9}$", digits):
            raise ValueError("Invalid Indian mobile number. Must be 10 digits starting with 6, 7, 8, or 9.")
        return f"+91{digits}"

    @field_validator("name")
    @classmethod
    def validate_name(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return None
        cleaned = sanitize_input_text(v, max_len=100)
        if not cleaned or len(cleaned) < 2:
            raise ValueError("Name must be at least 2 characters long after trimming.")
        return cleaned

    @field_validator("bio")
    @classmethod
    def validate_bio(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return None
        return sanitize_input_text(v, max_len=500)

    @field_validator("avatar_url")
    @classmethod
    def validate_avatar_url(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return None
        v_lower = v.strip().lower()
        for forbidden in FORBIDDEN_URL_SCHEMES:
            if v_lower.startswith(forbidden):
                raise ValueError(f"Insecure URL scheme is forbidden: '{forbidden}'")
        # Ensure only https:// or trusted local /uploads/ paths
        if not (v_lower.startswith("https://") or v_lower.startswith("/uploads/")):
            raise ValueError("Avatar URL must begin with 'https://' or '/uploads/'.")
        return v.strip()

    @field_validator("date_of_birth")
    @classmethod
    def validate_date_of_birth(cls, v: Optional[date]) -> Optional[date]:
        if v is None:
            return None
        today = date.today()
        if v >= today:
            raise ValueError("Date of birth must be a past date.")
        # Age check: minimum 13 years old, maximum 120 years old
        age = today.year - v.year - ((today.month, today.day) < (v.month, v.day))
        if age < 13:
            raise ValueError("User must be at least 13 years old.")
        if age > 120:
            raise ValueError("Please provide a valid date of birth.")
        return v


class AccountProfileResponse(BaseModel):
    """
    Public-safe customer account profile response.
    Never exposes passwords, tokens, or private audit internals.
    """
    model_config = ConfigDict(from_attributes=True)

    id: str
    name: str
    email: str
    phone: Optional[str] = None
    avatar_url: Optional[str] = None
    date_of_birth: Optional[date] = None
    bio: Optional[str] = None
    is_verified: bool
    created_at: datetime
    has_pending_deletion: bool = False


class UserSessionResponse(BaseModel):
    """
    Active device session info for multi-device management.
    Never exposes raw tokens or session hashes.
    """
    model_config = ConfigDict(from_attributes=True)

    id: str
    device_name: Optional[str] = None
    platform: Optional[str] = None
    ip_address: Optional[str] = None
    last_seen_at: datetime
    created_at: datetime
    expires_at: datetime
    is_current: bool = False


class SecurityEventSummaryResponse(BaseModel):
    """
    Sanitized audit log response with PII masking.
    """
    model_config = ConfigDict(from_attributes=True)

    id: str
    event_type: str
    created_at: datetime
    ip_address: Optional[str] = None
    user_agent_summary: Optional[str] = None


class InitiateEmailChangeRequest(BaseModel):
    """Initiate an email change workflow."""
    model_config = ConfigDict(extra="forbid")

    new_email: EmailStr
    current_password: str = Field(..., min_length=6, description="Current password for identity confirmation")


class VerifyEmailChangeRequest(BaseModel):
    """Verify an email change code/token. Accepts either 'token' or 'verification_code'."""
    model_config = ConfigDict(extra="forbid")

    token: Optional[str] = Field(None, min_length=6, max_length=64)
    verification_code: Optional[str] = Field(None, min_length=6, max_length=64)

    @property
    def code(self) -> str:
        res = self.token or self.verification_code
        if not res:
            raise ValueError("Either 'token' or 'verification_code' must be provided.")
        return res


class InitiatePhoneChangeRequest(BaseModel):
    """Initiate a phone number update workflow."""
    model_config = ConfigDict(extra="forbid")

    new_phone: str = Field(..., min_length=10, max_length=15)
    current_password: str = Field(..., min_length=6, description="Current password for identity confirmation")

    @field_validator("new_phone")
    @classmethod
    def validate_indian_phone(cls, v: str) -> str:
        cleaned = re.sub(r"[\s\-\(\)]", "", v)
        if cleaned.startswith("+91"):
            digits = cleaned[3:]
        elif cleaned.startswith("0"):
            digits = cleaned[1:]
        else:
            digits = cleaned
        if not re.match(r"^[6-9]\d{9}$", digits):
            raise ValueError("Invalid Indian mobile number. Must be 10 digits starting with 6, 7, 8, or 9.")
        return f"+91{digits}"


class VerifyPhoneChangeRequest(BaseModel):
    """Verify a phone change code/token. Accepts either 'token' or 'verification_code'."""
    model_config = ConfigDict(extra="forbid")

    token: Optional[str] = Field(None, min_length=6, max_length=64)
    verification_code: Optional[str] = Field(None, min_length=6, max_length=64)

    @property
    def code(self) -> str:
        res = self.token or self.verification_code
        if not res:
            raise ValueError("Either 'token' or 'verification_code' must be provided.")
        return res


class AccountChangePasswordRequest(BaseModel):
    """Change current authenticated user password."""
    model_config = ConfigDict(extra="forbid")

    current_password: str = Field(..., min_length=6, description="Current password for identity confirmation")
    new_password: str = Field(..., min_length=8, description="New password (minimum 8 characters)")

    @field_validator("new_password")
    @classmethod
    def validate_different_password(cls, v: str, info) -> str:
        current = info.data.get("current_password")
        if current and v == current:
            raise ValueError("New password must be different from current password.")
        return v


class AccountSecuritySummaryResponse(BaseModel):
    """Safe security posture overview for customer account."""
    model_config = ConfigDict(from_attributes=True)

    email_verified: bool
    phone_verified: bool
    active_sessions: int
    has_pending_deletion: bool
    last_security_event_at: Optional[datetime] = None
    password_last_changed_at: Optional[datetime] = None


class SessionRevokeResponse(BaseModel):
    """Response returned when sessions are revoked."""
    revoked_count: int
    message: str


class AccountDeletionRequestSchema(BaseModel):
    """Request non-destructive account deletion with grace period."""
    model_config = ConfigDict(extra="forbid")

    current_password: str = Field(..., min_length=6, description="Current password for confirmation")
    reason: Optional[str] = Field(None, max_length=255)


class AccountDeletionResponse(BaseModel):
    """Response confirming account deletion scheduling."""
    model_config = ConfigDict(from_attributes=True)

    id: str
    status: str
    requested_at: datetime
    scheduled_at: datetime
    grace_period_days: int = 30


class AccountDeletionCancelResponse(BaseModel):
    """Response returned when account deletion request is cancelled."""
    message: str

