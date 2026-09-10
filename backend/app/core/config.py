import os
from typing import List, Union
from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore",
    )

    # Project Information
    PROJECT_NAME: str = "Cartify API"
    VERSION: str = "1.0.0"
    API_V1_STR: str = "/api/v1"
    ENVIRONMENT: str = os.getenv("ENVIRONMENT", "development")
    DEBUG: bool = os.getenv("DEBUG", "false").lower() == "true"

    # Cross-Origin Resource Sharing (CORS)
    CORS_ORIGINS: Union[List[str], str] = [
        "http://localhost:3000",
        "http://127.0.0.1:3000",
    ]

    @field_validator("CORS_ORIGINS", mode="before")
    @classmethod
    def assemble_cors_origins(cls, v: Union[str, List[str]]) -> List[str]:
        if isinstance(v, str) and not v.startswith("["):
            return [i.strip() for i in v.split(",") if i.strip()]
        elif isinstance(v, list):
            return v
        return ["http://localhost:3000"]

    # PostgreSQL Database Configuration
    DATABASE_URL: str = os.getenv(
        "DATABASE_URL",
        "postgresql+asyncpg://cartify:cartify_secure_pass@localhost:5432/cartify_db",
    )
    DATABASE_REPLICA_URL: str = os.getenv(
        "DATABASE_REPLICA_URL",
        DATABASE_URL,
    )

    # Database Connection Pool Settings
    DB_POOL_SIZE: int = int(os.getenv("DB_POOL_SIZE", "20"))
    DB_MAX_OVERFLOW: int = int(os.getenv("DB_MAX_OVERFLOW", "10"))
    DB_POOL_TIMEOUT: int = int(os.getenv("DB_POOL_TIMEOUT", "10"))
    DB_POOL_RECYCLE: int = int(os.getenv("DB_POOL_RECYCLE", "1800"))
    DB_ECHO: bool = os.getenv("DB_ECHO", "false").lower() == "true"
    DB_TIMEOUT_SECONDS: float = float(os.getenv("DB_TIMEOUT_SECONDS", "5.0"))

    # Redis Configuration
    REDIS_URL: str = os.getenv("REDIS_URL", "redis://localhost:6379/0")
    REDIS_POOL_MAX_CONNECTIONS: int = int(os.getenv("REDIS_POOL_MAX_CONNECTIONS", "100"))
    REDIS_SOCKET_TIMEOUT: float = float(os.getenv("REDIS_SOCKET_TIMEOUT", "2.0"))
    REDIS_CONNECT_TIMEOUT: float = float(os.getenv("REDIS_CONNECT_TIMEOUT", "2.0"))
    REDIS_TIMEOUT_SECONDS: float = float(os.getenv("REDIS_TIMEOUT_SECONDS", "2.0"))

    # Cache TTLs (in seconds)
    CACHE_DEFAULT_TTL: int = 300
    CACHE_CATEGORIES_TTL: int = 3600
    CACHE_PRODUCTS_TTL: int = 300

    # Security & Tokens (Foundation for Module 1)
    SECRET_KEY: str = os.getenv(
        "SECRET_KEY",
        "cartify_insecure_dev_secret_key_change_in_production_2026",
    )
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24  # 24 hours
    REFRESH_TOKEN_EXPIRE_DAYS: int = 30

    # Request Timeouts & Limits
    REQUEST_TIMEOUT_SECONDS: float = float(os.getenv("REQUEST_TIMEOUT_SECONDS", "10.0"))
    RATE_LIMIT_PER_MINUTE: int = int(os.getenv("RATE_LIMIT_PER_MINUTE", "120"))

settings = Settings()
