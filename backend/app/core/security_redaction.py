"""
Security Redaction and Cryptographic Utilities (Module 12)

Bank-grade data sanitization, constant-time comparisons, and payload redaction
to protect sensitive credentials, PCI data, signatures, and tokens.
"""

import hmac
import re
from typing import Any, Dict, List, Union


# Sensitive key keywords to redact recursively in dictionaries and logs
SENSITIVE_FIELD_NAMES = {
    "password",
    "secret",
    "key_secret",
    "razorpay_key_secret",
    "webhook_secret",
    "signature",
    "token",
    "access_token",
    "refresh_token",
    "cvv",
    "cvc",
    "card_number",
    "card_token",
    "authorization",
    "client_secret",
    "private_key",
    "api_key",
    "device_token",
    "push_token",
}

# Regex for detecting 13 to 19 digit potential credit/debit card numbers
CARD_NUMBER_PATTERN = re.compile(r"\b(?:\d[ -]*?){13,19}\b")


def safe_str_cmp(val_a: Union[str, bytes, None], val_b: Union[str, bytes, None]) -> bool:
    """
    Constant-time comparison of two strings or bytes to prevent timing attacks.
    """
    if val_a is None or val_b is None:
        return False

    if isinstance(val_a, str):
        val_a = val_a.encode("utf-8")
    if isinstance(val_b, str):
        val_b = val_b.encode("utf-8")

    return hmac.compare_digest(val_a, val_b)


def mask_card_number(card_number: str) -> str:
    """
    Masks payment card number, preserving only the last 4 digits.
    Example: '4111111111111234' -> '************1234'
    """
    cleaned = re.sub(r"\D", "", card_number)
    if len(cleaned) < 4:
        return "****"
    return f"{'*' * (len(cleaned) - 4)}{cleaned[-4:]}"


def mask_device_token(token: str) -> str:
    """
    Masks device push token preserving first 6 and last 4 characters.
    Example: 'fcm_tok_abcdef123456789' -> 'fcm_to...6789'
    """
    if not token or len(token) <= 10:
        return "******"
    return f"{token[:6]}...{token[-4:]}"


def mask_phone_number(phone: str) -> str:
    """
    Masks phone number preserving country prefix and last 4 digits.
    Example: '+919876543210' -> '+91******3210'
    """
    if not phone or len(phone) < 4:
        return "****"
    cleaned = re.sub(r"[^\d+]", "", phone)
    prefix = ""
    digits = cleaned
    if cleaned.startswith("+"):
        prefix = cleaned[:3]
        digits = cleaned[3:]
    if len(digits) <= 4:
        return f"{prefix}****"
    return f"{prefix}{'*' * (len(digits) - 4)}{digits[-4:]}"


def redact_sensitive_payload(data: Any) -> Any:
    """
    Recursively redacts sensitive keys and patterns from dictionary/list payloads.
    Safe for structured logging and exception contexts.
    """
    if isinstance(data, dict):
        redacted = {}
        for key, value in data.items():
            lower_key = str(key).lower()
            if any(sensitive in lower_key for sensitive in SENSITIVE_FIELD_NAMES):
                if lower_key in {"card_number", "pan"} and isinstance(value, str):
                    redacted[key] = mask_card_number(value)
                else:
                    redacted[key] = "[REDACTED]"
            else:
                redacted[key] = redact_sensitive_payload(value)
        return redacted

    elif isinstance(data, list):
        return [redact_sensitive_payload(item) for item in data]

    elif isinstance(data, tuple):
        return tuple(redact_sensitive_payload(item) for item in data)

    elif isinstance(data, str):
        # Redact raw card numbers embedded in strings
        def _replace_card(match: re.Match) -> str:
            raw = match.group(0)
            digits = re.sub(r"\D", "", raw)
            if 13 <= len(digits) <= 19:
                return mask_card_number(digits)
            return raw

        return CARD_NUMBER_PATTERN.sub(_replace_card, data)

    return data
