"""
Cartify Security Foundation (Module 0)

Provides:
- Native bcrypt password hashing and verification
- JWT access and refresh token generation and decoding
- Role definitions prepared for Module 1 User Authentication
"""

from datetime import datetime, timedelta, timezone
from typing import Any, Dict, Optional, Union
import bcrypt
from jose import jwt, JWTError
from app.core.config import settings

# Supported system roles
class UserRole:
    CUSTOMER = "customer"
    ADMIN = "admin"
    STORE_MANAGER = "store_manager"
    DELIVERY_PARTNER = "delivery_partner"

def get_password_hash(password: str) -> str:
    """Generates a secure bcrypt password hash (enforcing 72-byte max for bcrypt)."""
    pwd_bytes = password.encode("utf-8")[:72]
    salt = bcrypt.gensalt()
    return bcrypt.hashpw(pwd_bytes, salt).decode("utf-8")

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verifies a plain text password against a bcrypt hash."""
    try:
        pwd_bytes = plain_password.encode("utf-8")[:72]
        hash_bytes = hashed_password.encode("utf-8")
        return bcrypt.checkpw(pwd_bytes, hash_bytes)
    except Exception:
        return False

def create_access_token(
    subject: Union[str, Any],
    role: str = UserRole.CUSTOMER,
    expires_delta: Optional[timedelta] = None,
) -> str:
    """Creates a signed JWT access token."""
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)

    to_encode = {
        "sub": str(subject),
        "role": role,
        "type": "access",
        "exp": expire,
        "iat": datetime.now(timezone.utc),
    }
    return jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)

def decode_access_token(token: str) -> Optional[Dict[str, Any]]:
    """Decodes and validates a JWT token. Returns payload dict or None."""
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        return payload
    except (JWTError, Exception):
        return None
