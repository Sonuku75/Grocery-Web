"""
Unit tests for Notification Provider Adapters (Module 13)

Validates:
- MockEmailProvider: success, permanent fail, transient fail
- MockSMSProvider: phone normalization, delivery results
- MockPushNotificationProvider: token validation, simulated push delivery
"""

import pytest
from app.providers.notifications.mock_email import MockEmailProvider
from app.providers.notifications.mock_sms import MockSMSProvider
from app.providers.notifications.mock_push import MockPushNotificationProvider


@pytest.mark.asyncio
async def test_mock_email_provider_success():
    provider = MockEmailProvider()
    res = await provider.send_email(
        to_email="test@cartify.com",
        subject="Welcome",
        body_html="<p>Welcome to Cartify</p>",
        body_text="Welcome to Cartify",
    )
    assert res.success is True
    assert res.provider_message_id is not None
    assert res.is_transient is False


@pytest.mark.asyncio
async def test_mock_email_provider_simulated_failures():
    provider = MockEmailProvider()

    # Permanent failure injection
    res_perm = await provider.send_email(
        to_email="FORCE_PERMANENT_FAIL@cartify.com",
        subject="Test",
        body_html="body",
        body_text="body",
    )
    assert res_perm.success is False
    assert res_perm.is_transient is False

    # Transient failure injection
    res_trans = await provider.send_email(
        to_email="FORCE_TRANSIENT_FAIL@cartify.com",
        subject="Test",
        body_html="body",
        body_text="body",
    )
    assert res_trans.success is False
    assert res_trans.is_transient is True


@pytest.mark.asyncio
async def test_mock_sms_provider():
    provider = MockSMSProvider()

    # Valid Indian mobile
    res_ok = await provider.send_sms(
        phone_number="+919876543210",
        message="Your Cartify OTP is 123456",
    )
    assert res_ok.success is True
    assert res_ok.provider_message_id is not None

    # Invalid phone format
    res_err = await provider.send_sms(
        phone_number="123",
        message="Test message",
    )
    assert res_err.success is False
    assert res_err.failure_code == "INVALID_PHONE_NUMBER"


@pytest.mark.asyncio
async def test_mock_push_provider():
    provider = MockPushNotificationProvider()

    # Valid token
    res_ok = await provider.send_push(
        device_token="fcm_valid_token_1234567890",
        platform="ANDROID",
        title="Order Dispatched",
        body="Your groceries are on the way!",
    )
    assert res_ok.success is True
    assert res_ok.provider_message_id is not None

    # Invalid / short token
    res_short = await provider.send_push(
        device_token="bad",
        platform="IOS",
        title="Title",
        body="Body",
    )
    assert res_short.success is False
    assert res_short.failure_code == "INVALID_DEVICE_TOKEN"
