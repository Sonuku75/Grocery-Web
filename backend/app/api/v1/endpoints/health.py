"""
Cartify Health & Readiness Probes (Module 0 Foundation)

Probes:
- GET /api/v1/health: Liveness check (lightweight, no external service dependency)
- GET /api/v1/ready: Readiness check (probes PostgreSQL Primary, Replica, and Redis)
"""

from datetime import datetime, timezone
from fastapi import APIRouter, Response, status
from app.core.config import settings
from app.core.redis import ping_redis
from app.db.session import ping_databases
from app.schemas.health import HealthResponse, ReadinessResponse, ServiceStatus

router = APIRouter()

@router.get(
    "/health",
    response_model=HealthResponse,
    status_code=status.HTTP_200_OK,
    summary="Application Liveness Probe",
)
async def health_check() -> HealthResponse:
    """
    Liveness probe.
    Returns 200 OK immediately if the FastAPI worker process is active and responsive.
    Does not query downstream databases to avoid cascading restart loops.
    """
    return HealthResponse(
        status="healthy",
        service=settings.PROJECT_NAME,
        version=settings.VERSION,
        timestamp=datetime.now(timezone.utc).isoformat(),
    )

@router.get(
    "/ready",
    response_model=ReadinessResponse,
    summary="Application Readiness Probe",
)
async def readiness_check(response: Response) -> ReadinessResponse:
    """
    Readiness probe.
    Verifies operational readiness of upstream infrastructure:
    - PostgreSQL Primary
    - PostgreSQL Read Replica
    - Redis Cache & Lock cluster
    Returns 503 if primary database or redis is unavailable.
    """
    db_status = await ping_databases()
    redis_ok = await ping_redis()

    is_ready = db_status.get("primary", False) and redis_ok

    services = ServiceStatus(
        postgres_primary="up" if db_status.get("primary") else "down",
        postgres_replica="up" if db_status.get("replica") else "down",
        redis="up" if redis_ok else "down",
    )

    if not is_ready:
        response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE

    return ReadinessResponse(
        status="ready" if is_ready else "unhealthy",
        services=services,
    )
