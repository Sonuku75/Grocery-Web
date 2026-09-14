"""
Unit tests for Payment Security, Constant-time Comparison, and Secret Redaction (Module 12)
"""

from decimal import Decimal
import pytest

from app.core.security_redaction import (
    mask_card_number,
    redact_sensitive_payload,
    safe_str_cmp,
)


def test_safe_str_cmp():
    """Verify constant-time comparison against timing attacks."""
    assert safe_str_cmp("secret123", "secret123") is True
    assert safe_str_cmp("secret123", "secret124") is False
    assert safe_str_cmp("secret123", "secret") is False
    assert safe_str_cmp(None, "secret") is False
    assert safe_str_cmp("secret", None) is False
    assert safe_str_cmp(b"bytes_token", b"bytes_token") is True
    assert safe_str_cmp(b"bytes_token", b"other_token") is False


def test_mask_card_number():
    """Verify payment card masking preserves only the last 4 digits."""
    assert mask_card_number("4111 1111 1111 1234") == "************1234"
    assert mask_card_number("4111111111111234") == "************1234"
    assert mask_card_number("123") == "****"


def test_redact_sensitive_payload_dict():
    """Verify sensitive keys in payloads are redacted."""
    payload = {
        "order_id": "ord_123",
        "user_email": "user@cartify.com",
        "payment_signature": "sig_abc123xyz",
        "razorpay_key_secret": "super_secret_key",
        "client_secret": "pi_sec_999",
        "card_token": "tok_visa_444",
        "nested": {
            "cvv": "123",
            "password": "my_password",
            "amount": 499.0,
            "currency": "INR",
        },
        "list_items": [
            {"access_token": "jwt.token.here", "id": "1"},
            {"public_info": "safe"},
        ],
    }

    redacted = redact_sensitive_payload(payload)

    assert redacted["order_id"] == "ord_123"
    assert redacted["payment_signature"] == "[REDACTED]"
    assert redacted["razorpay_key_secret"] == "[REDACTED]"
    assert redacted["client_secret"] == "[REDACTED]"
    assert redacted["card_token"] == "[REDACTED]"
    assert redacted["nested"]["cvv"] == "[REDACTED]"
    assert redacted["nested"]["password"] == "[REDACTED]"
    assert redacted["nested"]["amount"] == 499.0
    assert redacted["list_items"][0]["access_token"] == "[REDACTED]"
    assert redacted["list_items"][1]["public_info"] == "safe"


def test_redact_sensitive_payload_embedded_card():
    """Verify PAN card numbers in strings are masked."""
    text = "Payment processed with card 4111111111111234 on terminal"
    redacted = redact_sensitive_payload(text)
    assert "4111111111111234" not in redacted
    assert "************1234" in redacted
