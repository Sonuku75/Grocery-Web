"""
Integration tests for Cartify Address Endpoints (Module 2)
"""

from datetime import datetime, timezone
from unittest.mock import AsyncMock, patch
import pytest
from fastapi.testclient import TestClient

from app.api.deps import get_current_active_user
from app.core.database import get_db_reader, get_db_writer
from app.core.errors import NotFoundError
from app.main import app
from app.models.user import User
from app.schemas.address import AddressListResponse, AddressResponse

@pytest.fixture
def test_user():
    return User(
        id="usr-test-addr-1",
        name="Sonu Kumar",
        email="sonu@cartify.com",
        phone="9110036860",
        role="customer",
        is_active=True,
        is_verified=True,
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
    )

@pytest.fixture
def mock_session():
    return AsyncMock()

@pytest.fixture
def client(mock_session):
    app.dependency_overrides[get_db_writer] = lambda: mock_session
    app.dependency_overrides[get_db_reader] = lambda: mock_session
    with TestClient(app, base_url="http://testserver") as test_client:
        yield test_client
    app.dependency_overrides.clear()

def test_create_address_unauthenticated(client):
    res = client.post(
        "/api/v1/addresses",
        json={
            "recipient_name": "Sonu Kumar",
            "phone": "9110036860",
            "address_line_1": "123 Main Road",
            "city": "Jaipur",
            "state": "Rajasthan",
            "postal_code": "302017",
        },
    )
    assert res.status_code == 401

def test_create_address_authenticated(client, test_user):
    app.dependency_overrides[get_current_active_user] = lambda: test_user
    fake_resp = AddressResponse(
        id="addr-new-1",
        user_id=test_user.id,
        label="Home",
        recipient_name="Sonu Kumar",
        phone="9110036860",
        address_line_1="123 Main Road",
        address_line_2=None,
        landmark=None,
        city="Jaipur",
        state="Rajasthan",
        country="India",
        postal_code="302017",
        latitude=26.9124,
        longitude=75.7873,
        is_default=True,
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
    )

    with patch("app.services.address.AddressService.create_address", new_callable=AsyncMock) as mock_create:
        mock_create.return_value = fake_resp

        res = client.post(
            "/api/v1/addresses",
            headers={"Authorization": "Bearer valid_token"},
            json={
                "label": "Home",
                "recipient_name": "Sonu Kumar",
                "phone": "9110036860",
                "address_line_1": "123 Main Road",
                "city": "Jaipur",
                "state": "Rajasthan",
                "postal_code": "302017",
                "latitude": 26.9124,
                "longitude": 75.7873,
                "is_default": True,
            },
        )

        assert res.status_code == 201
        data = res.json()
        assert data["success"] is True
        assert data["data"]["id"] == "addr-new-1"
        assert data["data"]["user_id"] == test_user.id
        assert data["data"]["is_default"] is True

def test_list_addresses(client, test_user):
    app.dependency_overrides[get_current_active_user] = lambda: test_user
    fake_resp = AddressResponse(
        id="addr-1",
        user_id=test_user.id,
        label="Home",
        recipient_name="Sonu Kumar",
        phone="9110036860",
        address_line_1="123 Main Road",
        city="Jaipur",
        state="Rajasthan",
        country="India",
        postal_code="302017",
        is_default=True,
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
    )

    with patch("app.services.address.AddressService.list_addresses", new_callable=AsyncMock) as mock_list:
        mock_list.return_value = AddressListResponse(items=[fake_resp], total=1)

        res = client.get(
            "/api/v1/addresses",
            headers={"Authorization": "Bearer valid_token"},
        )
        assert res.status_code == 200
        data = res.json()
        assert data["success"] is True
        assert data["data"]["total"] == 1
        assert len(data["data"]["items"]) == 1

def test_get_address_owner_vs_non_owner(client, test_user):
    app.dependency_overrides[get_current_active_user] = lambda: test_user
    fake_resp = AddressResponse(
        id="addr-1",
        user_id=test_user.id,
        label="Home",
        recipient_name="Sonu Kumar",
        phone="9110036860",
        address_line_1="123 Main Road",
        city="Jaipur",
        state="Rajasthan",
        country="India",
        postal_code="302017",
        is_default=True,
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
    )

    with patch("app.services.address.AddressService.get_address", new_callable=AsyncMock) as mock_get:
        mock_get.return_value = fake_resp
        res = client.get(
            "/api/v1/addresses/addr-1",
            headers={"Authorization": "Bearer valid_token"},
        )
        assert res.status_code == 200
        assert res.json()["data"]["id"] == "addr-1"

        # When address belongs to another user or doesn't exist -> 404
        mock_get.side_effect = NotFoundError("Address", "other-user-addr")
        res_404 = client.get(
            "/api/v1/addresses/other-user-addr",
            headers={"Authorization": "Bearer valid_token"},
        )
        assert res_404.status_code == 404

def test_update_address(client, test_user):
    app.dependency_overrides[get_current_active_user] = lambda: test_user
    fake_resp = AddressResponse(
        id="addr-1",
        user_id=test_user.id,
        label="Office",
        recipient_name="Sonu Kumar",
        phone="9110036860",
        address_line_1="Tower B",
        city="Jaipur",
        state="Rajasthan",
        country="India",
        postal_code="302017",
        is_default=True,
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
    )

    with patch("app.services.address.AddressService.update_address", new_callable=AsyncMock) as mock_update:
        mock_update.return_value = fake_resp

        res = client.patch(
            "/api/v1/addresses/addr-1",
            headers={"Authorization": "Bearer valid_token"},
            json={"label": "Office", "address_line_1": "Tower B"},
        )
        assert res.status_code == 200
        assert res.json()["data"]["label"] == "Office"

def test_delete_address(client, test_user):
    app.dependency_overrides[get_current_active_user] = lambda: test_user

    with patch("app.services.address.AddressService.delete_address", new_callable=AsyncMock) as mock_del:
        res = client.delete(
            "/api/v1/addresses/addr-1",
            headers={"Authorization": "Bearer valid_token"},
        )
        assert res.status_code == 200
        assert res.json()["success"] is True
        mock_del.assert_called_once_with(db=client.app.dependency_overrides[get_db_writer](), address_id="addr-1", user_id=test_user.id)

def test_set_default_address(client, test_user):
    app.dependency_overrides[get_current_active_user] = lambda: test_user
    fake_resp = AddressResponse(
        id="addr-2",
        user_id=test_user.id,
        label="Work",
        recipient_name="Sonu Kumar",
        phone="9110036860",
        address_line_1="Work address",
        city="Jaipur",
        state="Rajasthan",
        country="India",
        postal_code="302017",
        is_default=True,
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
    )

    with patch("app.services.address.AddressService.set_default_address", new_callable=AsyncMock) as mock_set:
        mock_set.return_value = fake_resp

        res = client.patch(
            "/api/v1/addresses/addr-2/default",
            headers={"Authorization": "Bearer valid_token"},
        )
        assert res.status_code == 200
        assert res.json()["data"]["is_default"] is True
