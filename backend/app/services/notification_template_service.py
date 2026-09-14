"""
Notification Template Service (Module 13)

Provides secure template compilation, validation, and rendering:
- Safe mustache interpolation (e.g. {{variable}})
- SSTI (Server-Side Template Injection) and code injection prevention
- Sanitization of variable names and strict allowlisting
- HTML-escaping for web/email contexts
- Fallback default system templates for automated lifecycle events
"""

import html
import re
from typing import Any, Dict, Optional
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.notification import NotificationChannel
from app.repositories.notification_template import NotificationTemplateRepository

# Strict regex matching {{ variable }} or {{variable}}
TEMPLATE_VARIABLE_REGEX = re.compile(r"\{\{\s*([a-zA-Z0-9_]+)\s*\}\}")

# Disallowed substrings and sensitive keys to prevent SSTI, code injection, and leaks
DISALLOWED_SUBSTRINGS = ["__", "eval", "exec", "import", "globals", "locals", "class", "mro", "subclasses"]
DISALLOWED_KEYS = {"password", "token", "secret", "api_key", "credentials", "jwt", "auth", "hash"}

# Built-in fallback system templates: key -> { "title": ..., "body": ... }
DEFAULT_SYSTEM_TEMPLATES: Dict[str, Dict[str, str]] = {
    "ORDER_CREATED": {
        "title": "Order Placed: {{order_number}}",
        "body": "Thank you for your order! Your order #{{order_number}} of ₹{{total_amount}} has been placed successfully.",
    },
    "ORDER_CONFIRMED": {
        "title": "Order Confirmed: {{order_number}}",
        "body": "Your order #{{order_number}} has been confirmed and is being prepared.",
    },
    "ORDER_SHIPPED": {
        "title": "Order Shipped: {{order_number}}",
        "body": "Good news! Your order #{{order_number}} has been dispatched and is on its way.",
    },
    "ORDER_DELIVERED": {
        "title": "Order Delivered: {{order_number}}",
        "body": "Your order #{{order_number}} has been delivered. Enjoy your groceries!",
    },
    "ORDER_CANCELLED": {
        "title": "Order Cancelled: {{order_number}}",
        "body": "Your order #{{order_number}} has been cancelled. Any refund due will be credited per policy.",
    },
    "PAYMENT_SUCCESS": {
        "title": "Payment Successful",
        "body": "Payment of ₹{{amount}} for order #{{order_number}} was successful.",
    },
    "PAYMENT_FAILED": {
        "title": "Payment Failed",
        "body": "Payment for order #{{order_number}} failed. Please update your payment method.",
    },
    "REFUND_SUCCESS": {
        "title": "Refund Processed",
        "body": "A refund of ₹{{amount}} for order #{{order_number}} has been processed successfully.",
    },
    "SECURITY_ALERTS": {
        "title": "Security Alert: Account Activity",
        "body": "New security activity detected on your Cartify account: {{activity_description}}.",
    },
    "PASSWORD_RESET": {
        "title": "Password Reset Request",
        "body": "A password reset was requested for your Cartify account. Use code {{reset_code}} to reset your password.",
    },
    "INVENTORY_BACK_IN_STOCK": {
        "title": "Item Back in Stock: {{product_name}}",
        "body": "{{product_name}} is back in stock! Order now before stock runs out.",
    },
    "PROMOTIONAL": {
        "title": "Special Offer from Cartify!",
        "body": "{{promo_text}} Use code {{coupon_code}} at checkout.",
    },
}


class NotificationTemplateService:
    """Service handling template rendering, validation, and retrieval."""

    @classmethod
    def validate_variable_key(cls, key: str) -> None:
        """Validate that a variable key is safe and not malicious."""
        key_lower = key.lower()
        if any(bad in key_lower for bad in DISALLOWED_SUBSTRINGS):
            raise ValueError(f"Template variable contains disallowed character sequence: '{key}'")
        if key_lower in DISALLOWED_KEYS:
            raise ValueError(f"Template variable references sensitive key: '{key}'")

    @classmethod
    def render_string(
        cls,
        template_str: str,
        variables: Dict[str, Any],
        escape_html: bool = False,
    ) -> str:
        """
        Safely interpolate {{variable}} in template_str using provided variables.
        
        Args:
            template_str: The raw template text containing {{var}} tokens.
            variables: Mapping of variable names to primitive values.
            escape_html: If True, values are HTML-escaped before insertion.
        """
        if not template_str:
            return ""

        # Validate all provided keys first
        for k in variables.keys():
            cls.validate_variable_key(k)

        def replacer(match: re.Match) -> str:
            var_name = match.group(1).strip()
            cls.validate_variable_key(var_name)
            if var_name not in variables:
                # Retain token if variable is not supplied or treat as empty
                return ""
            val = variables[var_name]
            val_str = "" if val is None else str(val)
            if escape_html:
                return html.escape(val_str)
            return val_str

        return TEMPLATE_VARIABLE_REGEX.sub(replacer, template_str)

    @classmethod
    async def get_rendered_template(
        cls,
        db: AsyncSession,
        template_code: str,
        channel: NotificationChannel,
        variables: Dict[str, Any],
    ) -> Dict[str, str]:
        """
        Fetch template from repository or fallback to system default, then render title and body.
        
        Returns:
            Dict with "title", "body", and optionally "html_content".
        """
        db_template = await NotificationTemplateRepository.get_template_by_code(
            db, template_code, channel.value
        )

        escape_html = channel == NotificationChannel.EMAIL

        if db_template:
            raw_title = db_template.subject or db_template.title_template or ""
            raw_body = getattr(db_template, "body_template", None) or getattr(db_template, "body", "")
            raw_html = getattr(db_template, "html_content", None)

            title = cls.render_string(raw_title, variables, escape_html=False)
            body = cls.render_string(raw_body, variables, escape_html=escape_html)
            html_content = (
                cls.render_string(raw_html, variables, escape_html=False)
                if raw_html
                else None
            )
            return {
                "title": title,
                "body": body,
                "html_content": html_content,
            }

        # Fallback to system defaults
        default = DEFAULT_SYSTEM_TEMPLATES.get(
            template_code,
            {
                "title": f"Update: {template_code}",
                "body": "You have a new notification regarding your Cartify account.",
            },
        )

        rendered_title = cls.render_string(default.get("title", ""), variables, escape_html=False)
        rendered_body = cls.render_string(default.get("body", ""), variables, escape_html=escape_html)

        return {
            "title": rendered_title,
            "body": rendered_body,
            "html_content": None,
        }
