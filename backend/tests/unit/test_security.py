import pytest
from app.core.security import (
    create_access_token,
    decode_access_token,
    get_password_hash,
    verify_password,
    UserRole,
)

def test_password_hashing():
    raw = "SecureSecretPassword123!"
    hashed = get_password_hash(raw)
    assert hashed != raw
    assert verify_password(raw, hashed) is True
    assert verify_password("WrongPassword", hashed) is False

def test_jwt_generation_and_decoding():
    user_id = "user_test_uuid_123"
    token = create_access_token(subject=user_id, role=UserRole.ADMIN)
    assert isinstance(token, str)

    payload = decode_access_token(token)
    assert payload is not None
    assert payload.get("sub") == user_id
    assert payload.get("role") == UserRole.ADMIN
    assert payload.get("type") == "access"

def test_invalid_jwt():
    assert decode_access_token("invalid.token.structure") is None
