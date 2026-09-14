import os
from typing import List, Optional, Union
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
    DATABASE_PRIMARY_URL: str = os.getenv(
        "DATABASE_PRIMARY_URL",
        DATABASE_URL,
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

    # Security & Tokens (Module 1 Authentication)
    SECRET_KEY: str = os.getenv(
        "SECRET_KEY",
        "cartify_insecure_dev_secret_key_change_in_production_2026",
    )
    JWT_SECRET_KEY: str = os.getenv(
        "JWT_SECRET_KEY",
        "cartify_insecure_dev_secret_key_change_in_production_2026",
    )
    ALGORITHM: str = "HS256"
    JWT_ALGORITHM: str = os.getenv("JWT_ALGORITHM", "HS256")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "30"))
    REFRESH_TOKEN_EXPIRE_DAYS: int = int(os.getenv("REFRESH_TOKEN_EXPIRE_DAYS", "30"))
    PASSWORD_RESET_EXPIRE_MINUTES: int = int(os.getenv("PASSWORD_RESET_EXPIRE_MINUTES", "15"))

    # Request Timeouts & Limits
    REQUEST_TIMEOUT_SECONDS: float = float(os.getenv("REQUEST_TIMEOUT_SECONDS", "10.0"))
    RATE_LIMIT_PER_MINUTE: int = int(os.getenv("RATE_LIMIT_PER_MINUTE", "120"))
    RATE_LIMIT_LOGIN: int = int(os.getenv("RATE_LIMIT_LOGIN", "10"))
    RATE_LIMIT_REGISTER: int = int(os.getenv("RATE_LIMIT_REGISTER", "5"))
    RATE_LIMIT_FORGOT_PASSWORD: int = int(os.getenv("RATE_LIMIT_FORGOT_PASSWORD", "3"))
    RATE_LIMIT_RESET_PASSWORD: int = int(os.getenv("RATE_LIMIT_RESET_PASSWORD", "5"))
    COOKIE_SECURE: bool = os.getenv("COOKIE_SECURE", "false").lower() == "true"

    # Module 9 Checkout & Delivery Settings
    FREE_DELIVERY_THRESHOLD: float = float(os.getenv("FREE_DELIVERY_THRESHOLD", "499.0"))
    STANDARD_DELIVERY_FEE: float = float(os.getenv("STANDARD_DELIVERY_FEE", "40.0"))
    CHECKOUT_SESSION_EXPIRE_MINUTES: int = int(os.getenv("CHECKOUT_SESSION_EXPIRE_MINUTES", "30"))

    # Module 12 Payments & High-Security Payment Infrastructure
    PAYMENT_PROVIDER_DEFAULT: str = os.getenv("PAYMENT_PROVIDER_DEFAULT", "mock")
    RAZORPAY_KEY_ID: Optional[str] = os.getenv("RAZORPAY_KEY_ID", None)
    RAZORPAY_KEY_SECRET: Optional[str] = os.getenv("RAZORPAY_KEY_SECRET", None)
    RAZORPAY_WEBHOOK_SECRET: Optional[str] = os.getenv("RAZORPAY_WEBHOOK_SECRET", None)
    PAYMENT_WEBHOOK_MAX_BYTES: int = int(os.getenv("PAYMENT_WEBHOOK_MAX_BYTES", "65536"))
    PAYMENT_EXPIRY_MINUTES: int = int(os.getenv("PAYMENT_EXPIRY_MINUTES", "15"))

    # Module 13 Notifications & Notification Infrastructure
    NOTIFICATION_EMAIL_PROVIDER: str = os.getenv("NOTIFICATION_EMAIL_PROVIDER", "mock")
    NOTIFICATION_EMAIL_API_KEY: Optional[str] = os.getenv("NOTIFICATION_EMAIL_API_KEY", None)
    NOTIFICATION_SMS_PROVIDER: str = os.getenv("NOTIFICATION_SMS_PROVIDER", "mock")
    NOTIFICATION_SMS_API_KEY: Optional[str] = os.getenv("NOTIFICATION_SMS_API_KEY", None)
    NOTIFICATION_PUSH_PROVIDER: str = os.getenv("NOTIFICATION_PUSH_PROVIDER", "mock")
    NOTIFICATION_PUSH_API_KEY: Optional[str] = os.getenv("NOTIFICATION_PUSH_API_KEY", None)
    NOTIFICATION_WEBHOOK_SECRET: Optional[str] = os.getenv("NOTIFICATION_WEBHOOK_SECRET", "mock_notif_webhook_secret_key")
    NOTIFICATION_MAX_RETRIES: int = int(os.getenv("NOTIFICATION_MAX_RETRIES", "3"))
    NOTIFICATION_RETRY_BASE_DELAY: int = int(os.getenv("NOTIFICATION_RETRY_BASE_DELAY", "5"))
    NOTIFICATION_DEFAULT_EXPIRY_DAYS: int = int(os.getenv("NOTIFICATION_DEFAULT_EXPIRY_DAYS", "90"))
    NOTIFICATION_PAGE_SIZE_DEFAULT: int = int(os.getenv("NOTIFICATION_PAGE_SIZE_DEFAULT", "20"))
    NOTIFICATION_PAGE_SIZE_MAX: int = int(os.getenv("NOTIFICATION_PAGE_SIZE_MAX", "50"))

    # Module 14 Reviews & Ratings (High-Security Architecture)
    REVIEW_PAGE_SIZE_DEFAULT: int = int(os.getenv("REVIEW_PAGE_SIZE_DEFAULT", "20"))
    REVIEW_PAGE_SIZE_MAX: int = int(os.getenv("REVIEW_PAGE_SIZE_MAX", "50"))
    REVIEW_MODERATION_AUTO_PUBLISH: bool = os.getenv("REVIEW_MODERATION_AUTO_PUBLISH", "true").lower() == "true"
    RATE_LIMIT_REVIEW_CREATE: int = int(os.getenv("RATE_LIMIT_REVIEW_CREATE", "10"))
    RATE_LIMIT_REVIEW_VOTE: int = int(os.getenv("RATE_LIMIT_REVIEW_VOTE", "30"))
    RATE_LIMIT_REVIEW_REPORT: int = int(os.getenv("RATE_LIMIT_REVIEW_REPORT", "5"))

settings = Settings()

