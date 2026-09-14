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
    admin_coupons,
    admin_inventory,
    admin_notifications,
    admin_orders,
    admin_payments,
    admin_products,
    auth,
    cart,
    categories,
    checkout,
    coupons,
    devices,
    health,
    inventory,
    notification_preferences,
    notification_webhooks,
    notifications,
    orders,
    payments,
    products,
    reviews,
    admin_reviews,
    search,
    users,
    wishlist,
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

# Module 5: Search & Product Discovery
api_router.include_router(search.router)

# Module 6: Wishlist & Favorites
api_router.include_router(wishlist.router)

# Module 7: Cart & Cart Management
api_router.include_router(cart.router)

# Module 8: Coupons & Offers Management
api_router.include_router(coupons.router)
api_router.include_router(admin_coupons.router)

# Module 9: Checkout Management
api_router.include_router(checkout.router)

# Module 10: Orders & Order Management
api_router.include_router(orders.router)
api_router.include_router(admin_orders.router)

# Module 11: Inventory Management
api_router.include_router(inventory.router)
api_router.include_router(admin_inventory.router)

# Module 12: Payments & High-Security Payment Infrastructure
api_router.include_router(payments.router)
api_router.include_router(admin_payments.router)

# Module 13: Notifications & Notification Infrastructure
api_router.include_router(notifications.router)
api_router.include_router(notification_preferences.router)
api_router.include_router(devices.router)
api_router.include_router(notification_webhooks.router)
api_router.include_router(admin_notifications.router)

# Module 14: Reviews & Ratings (High-Security Architecture)
api_router.include_router(reviews.router)
api_router.include_router(admin_reviews.router)


