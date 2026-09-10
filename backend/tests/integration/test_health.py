import pytest
from fastapi.testclient import TestClient

def test_root_discovery(client: TestClient):
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "Cartify API"
    assert "health" in data
    assert "documentation" in data

def test_health_liveness(client: TestClient):
    response = client.get("/api/v1/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert data["service"] == "Cartify API"
    assert "version" in data
    assert "timestamp" in data

def test_health_readiness_probe(client: TestClient):
    # Without active DB/Redis in test environment, it returns 200 or 503 with structured JSON schema
    response = client.get("/api/v1/ready")
    assert response.status_code in (200, 503)
    data = response.json()
    assert "status" in data
    assert "services" in data
    assert "postgres_primary" in data["services"]
    assert "redis" in data["services"]
