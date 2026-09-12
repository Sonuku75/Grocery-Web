"""
Unit tests for Cartify Security & Cryptography utilities (Module 1)
"""

from datetime import timedelta
import pytest
from app.core.security import (
    UserRole,
    create_access_token,
    decode_access_token,
    generate_secure_token,
    get_password_hash,
    hash_token,
    verify_password,
)

def test_password_hashing():
    raw = "SecureSecretPassword123!"
    hashed = get_password_hash(raw)
    assert hashed != raw
    assert verify_password(raw, hashed) is True
    assert verify_password("WrongPassword", hashed) is False

def test_password_truncation_72_bytes():
    # Enforces native bcrypt 72-byte safe handling
    long_pwd = "A" * 100
    hashed = get_password_hash(long_pwd)
    assert verify_password("A" * 72, hashed) is True
    assert verify_password("A" * 100, hashed) is True
    assert verify_password("B" * 72, hashed) is False

def test_generate_secure_token():
    token1 = generate_secure_token(32)
    token2 = generate_secure_token(32)
    assert isinstance(token1, str)
    assert len(token1) >= 40  # 32 bytes base64 urlsafe is ~43 chars
    assert token1 != token2

def test_hash_token():
    raw = "sample_raw_token_xyz"
    hash1 = hash_token(raw)
    hash2 = hash_token(raw)
    assert len(hash1) == 64  # SHA-256 hex digest length
    assert hash1 == hash2
    assert hash1 != hash_token("different_token")

def test_jwt_generation_and_decoding():
    user_id = "user_test_uuid_123"
    token = create_access_token(subject=user_id, role=UserRole.ADMIN)
    assert isinstance(token, str)

    payload = decode_access_token(token)
    assert payload is not None
    assert payload.get("sub") == user_id
    assert payload.get("role") == UserRole.ADMIN
    assert payload.get("type") == "access"

def test_jwt_expired():
    user_id = "user_expired_uuid"
    # Token expired 1 hour ago
    token = create_access_token(
        subject=user_id,
        role=UserRole.CUSTOMER,
        expires_delta=timedelta(hours=-1),
    )
    payload = decode_access_token(token)
    assert payload is None

def test_invalid_jwt():
    assert decode_access_token("invalid.token.structure") is None
