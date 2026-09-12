"""
Cartify Models Registry (Module 4)

Exports all database models for declarative mapping and Alembic migrations.
"""

from app.db.base import Base, BaseRecord, TimestampMixin, generate_uuid
from app.models.user import User
from app.models.refresh_token import RefreshToken
from app.models.password_reset_token import PasswordResetToken
from app.models.address import Address
from app.models.category import Category
from app.models.product import Product
from app.models.product_variant import ProductVariant
from app.models.product_image import ProductImage

__all__ = [
    "Base",
    "BaseRecord",
    "TimestampMixin",
    "generate_uuid",
    "User",
    "RefreshToken",
    "PasswordResetToken",
    "Address",
    "Category",
    "Product",
    "ProductVariant",
    "ProductImage",
]
