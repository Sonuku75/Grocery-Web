import pytest
from fastapi.testclient import TestClient

def test_404_error_envelope(client: TestClient):
    response = client.get("/api/v1/non-existent-endpoint-xyz")
    assert response.status_code == 404
    data = response.json()
    assert data["success"] is False
    assert "error" in data
    assert data["error"]["code"] == "NOT_FOUND"
    assert "message" in data["error"]
    assert "request_id" in data

def test_request_id_and_timing_headers(client: TestClient):
    custom_id = "test-custom-request-id-999"
    response = client.get("/api/v1/health", headers={"X-Request-ID": custom_id})
    assert response.headers.get("X-Request-ID") == custom_id
    assert "X-Response-Time-Ms" in response.headers

def test_cors_preflight(client: TestClient):
    response = client.options(
        "/api/v1/health",
        headers={
            "Origin": "http://localhost:3000",
            "Access-Control-Request-Method": "GET",
        },
    )
    assert response.status_code == 200
    assert response.headers.get("access-control-allow-origin") == "http://localhost:3000"
