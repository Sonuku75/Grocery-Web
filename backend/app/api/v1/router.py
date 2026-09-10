"""
Cartify API v1 Router Registry (Module 0 Foundation)

Mounts all versioned /api/v1 routes.
Future domain routers (Auth in Module 1, Products in Module 2, Cart/Orders in Module 3+)
will be registered here cleanly.
"""

from fastapi import APIRouter
from app.api.v1.endpoints import health

api_router = APIRouter()

# Health and readiness probes
api_router.include_router(health.router, tags=["Health"])
