"""
Cartify FastAPI Application Entrypoint (Module 0 Foundation)

Features:
- Structured lifespan connection pool management (PostgreSQL & Redis)
- Request ID tracing and latency measurement middleware
- Centralized exception handlers
- Configurable CORS policy
- Swagger UI (/docs) and OpenAPI specification (/openapi.json)
- API v1 versioned router (/api/v1/...)
"""

from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.responses import JSONResponse

from app.api.v1.router import api_router
from app.core.config import settings
from app.core.errors import setup_exception_handlers
from app.core.logging import logger
from app.core.redis import ping_redis, redis_client
from app.db.session import engine_primary, engine_replica, ping_databases
from app.middleware.request_id import RequestTracingMiddleware

@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application Lifespan: Manages startup checks and graceful shutdown of network pools.
    """
    logger.info(f"Starting {settings.PROJECT_NAME} v{settings.VERSION} [{settings.ENVIRONMENT}]")

    # Non-blocking connectivity checks
    redis_alive = await ping_redis()
    if redis_alive:
        logger.info("Redis cache and lock connection verified.")
    else:
        logger.warning("Redis is offline. Operating with degraded cache capabilities.")

    db_alive = await ping_databases()
    if db_alive.get("primary"):
        logger.info("PostgreSQL Primary connection verified.")
    else:
        logger.warning("PostgreSQL Primary is currently unreachable.")

    yield

    logger.info("Initiating graceful shutdown. Disposing connection pools...")
    try:
        await redis_client.close()
        await engine_primary.dispose()
        await engine_replica.dispose()
    except Exception as e:
        logger.warning(f"Error during shutdown pool disposal: {e}")
    logger.info("Cartify API shutdown completed successfully.")

app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    description="Cartify E-Commerce Scalable REST API",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
)

# 1. High-Performance Gzip compression for payloads > 1KB
app.add_middleware(GZipMiddleware, minimum_size=1000)

# 2. Request Tracing, Structured Logging, and Server-side Timeouts
app.add_middleware(RequestTracingMiddleware)

# 3. Cross-Origin Resource Sharing (CORS)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["X-Request-ID", "X-Response-Time-Ms"],
)

# 4. Centralized Exception Handlers
setup_exception_handlers(app)

# 5. Business Versioned Router (/api/v1)
app.include_router(api_router, prefix=settings.API_V1_STR)

# Root service discovery route
@app.get("/", summary="Root Discovery & Health Navigation")
async def root():
    return JSONResponse(
        content={
            "name": settings.PROJECT_NAME,
            "version": settings.VERSION,
            "environment": settings.ENVIRONMENT,
            "documentation": "/docs",
            "openapi": "/openapi.json",
            "health": f"{settings.API_V1_STR}/health",
            "readiness": f"{settings.API_V1_STR}/ready",
        }
    )
