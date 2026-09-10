from typing import Dict
from pydantic import BaseModel, Field

class HealthResponse(BaseModel):
    status: str = Field("healthy", description="Application process health state")
    service: str = Field(..., description="Application name")
    version: str = Field(..., description="API version")
    timestamp: str = Field(..., description="ISO 8601 UTC timestamp")

class ServiceStatus(BaseModel):
    postgres_primary: str
    postgres_replica: str
    redis: str

class ReadinessResponse(BaseModel):
    status: str = Field(..., description="'ready' or 'unhealthy'")
    services: ServiceStatus
