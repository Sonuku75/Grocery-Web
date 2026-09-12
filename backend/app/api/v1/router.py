"""
Cartify API v1 Router Registry (Module 4)

Mounts all versioned /api/v1 routes:
- /api/v1/health (Module 0)
- /api/v1/auth (Module 1)
- /api/v1/users (Module 1)
- /api/v1/addresses (Module 2)
- /api/v1/categories (Module 3)
- /api/v1/admin/categories (Module 3)
- /api/v1/products (Module 4)
- /api/v1/admin/products (Module 4)
"""

from fastapi import APIRouter
from app.api.v1.endpoints import (
    addresses,
    admin_categories,
    admin_products,
    auth,
    categories,
    health,
    products,
    users,
)

api_router = APIRouter()

# Health and readiness probes
api_router.include_router(health.router, tags=["Health"])

# Module 1: Authentication & User Management
api_router.include_router(auth.router)
api_router.include_router(users.router)

# Module 2: Location & Address Management
api_router.include_router(addresses.router)

# Module 3: Categories & Subcategories Management
api_router.include_router(categories.router)
api_router.include_router(admin_categories.router)

# Module 4: Products & Product Variants
api_router.include_router(products.router)
api_router.include_router(admin_products.router)
