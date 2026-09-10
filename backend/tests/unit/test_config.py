import pytest
from app.core.config import Settings

def test_settings_defaults():
    settings = Settings()
    assert settings.PROJECT_NAME == "Cartify API"
    assert settings.API_V1_STR == "/api/v1"
    assert settings.VERSION == "1.0.0"
    assert settings.DB_POOL_SIZE >= 5
    assert settings.REDIS_POOL_MAX_CONNECTIONS >= 10

def test_cors_origins_validator():
    settings = Settings(CORS_ORIGINS="http://localhost:3000, http://test.cartify.com")
    assert "http://localhost:3000" in settings.CORS_ORIGINS
    assert "http://test.cartify.com" in settings.CORS_ORIGINS
