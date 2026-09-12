"""
Cartify Models Base Re-export
Ensures app.models.base points directly to app.db.base for single declarative metadata.
"""

from app.db.base import Base, BaseRecord, TimestampMixin, generate_uuid

__all__ = ["Base", "BaseRecord", "TimestampMixin", "generate_uuid"]

