"""
Unit tests for NotificationTemplateService (Module 13)

Validates:
- Mustache variable interpolation
- SSTI and malicious code injection prevention
- Sensitive key leak prevention
- HTML escaping for email context
- Fallback system templates
"""

import pytest
from unittest.mock import AsyncMock
from app.models.notification import NotificationChannel
from app.services.notification_template_service import NotificationTemplateService


def test_render_string_success():
    tpl = "Hello {{ name }}, your order #{{ order_number }} is ready!"
    variables = {"name": "Alice", "order_number": "CRT-2026-1234"}
    result = NotificationTemplateService.render_string(tpl, variables)
    assert result == "Hello Alice, your order #CRT-2026-1234 is ready!"


def test_render_string_missing_variable():
    tpl = "Order {{ order_number }} for {{ name }}."
    variables = {"order_number": "CRT-999"}
    result = NotificationTemplateService.render_string(tpl, variables)
    assert result == "Order CRT-999 for ."


def test_render_string_html_escaping():
    tpl = "Hello {{ user_input }}"
    variables = {"user_input": "<script>alert('xss')</script>"}
    result = NotificationTemplateService.render_string(tpl, variables, escape_html=True)
    assert "<script>" not in result
    assert "&lt;script&gt;alert(&#x27;xss&#x27;)&lt;/script&gt;" in result


def test_render_disallows_code_injection_keys():
    with pytest.raises(ValueError, match="disallowed character sequence"):
        NotificationTemplateService.render_string(
            "Test {{ __import__ }}", {"__import__": "evil"}
        )

    with pytest.raises(ValueError, match="disallowed character sequence"):
        NotificationTemplateService.render_string(
            "Test {{ evil }}", {"evil_eval_key": "bad"}
        )


def test_render_disallows_sensitive_keys():
    with pytest.raises(ValueError, match="sensitive key"):
        NotificationTemplateService.render_string(
            "Test {{ password }}", {"password": "secret_password"}
        )

    with pytest.raises(ValueError, match="sensitive key"):
        NotificationTemplateService.render_string(
            "Test {{ token }}", {"token": "jwt_token"}
        )


@pytest.mark.asyncio
async def test_get_rendered_template_system_fallback(monkeypatch):
    mock_db = AsyncMock()
    # No template in DB -> fallback to DEFAULT_SYSTEM_TEMPLATES
    from app.repositories.notification_template import NotificationTemplateRepository
    monkeypatch.setattr(NotificationTemplateRepository, "get_template_by_code", AsyncMock(return_value=None))

    res = await NotificationTemplateService.get_rendered_template(
        db=mock_db,
        template_code="ORDER_CREATED",
        channel=NotificationChannel.IN_APP,
        variables={"order_number": "CRT-8888", "total_amount": "599.00"},
    )

    assert "CRT-8888" in res["title"]
    assert "599.00" in res["body"]
