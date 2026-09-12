"""
Cartify Security & Cryptography Foundation (Module 1)

Provides:
- Native bcrypt password hashing and verification
- Cryptographically secure token generation and SHA-256 hashing
- JWT access token generation and validation
- Role definitions for authorization (CUSTOMER, ADMIN)
"""

import hashlib
import secrets
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, Optional, Union
import bcrypt
from jose import jwt, JWTError
from app.core.config import settings

class UserRole:
    CUSTOMER = "customer"
    ADMIN = "admin"

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

def generate_secure_token(nbytes: int = 32) -> str:
    """Generates a cryptographically secure random URL-safe string."""
    return secrets.token_urlsafe(nbytes)

def hash_token(token: str) -> str:
    """Computes the SHA-256 hex digest of a raw token for secure database persistence."""
    return hashlib.sha256(token.encode("utf-8")).hexdigest()

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
    return jwt.encode(to_encode, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)

def decode_access_token(token: str) -> Optional[Dict[str, Any]]:
    """Decodes and validates a JWT token. Returns payload dict or None."""
    try:
        payload = jwt.decode(token, settings.JWT_SECRET_KEY, algorithms=[settings.JWT_ALGORITHM])
        return payload
    except (JWTError, Exception):
        return None
