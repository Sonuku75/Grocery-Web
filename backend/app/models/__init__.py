"""
Cartify Models Registry (Module 0 Foundation)

Base classes and mixins are exported here.
Business domain models (Users in Module 1, Categories/Products in Module 2, Cart/Orders in Module 3+)
will be registered here module-by-module.
"""

from app.db.base import Base, BaseRecord, TimestampMixin, generate_uuid

__all__ = ["Base", "BaseRecord", "TimestampMixin", "generate_uuid"]
