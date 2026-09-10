"""
Cartify Database Declarative Base & Conventions (Module 0)

Primary Key & Identifier Strategy:
----------------------------------
We use UUIDv4 string representations (36 characters) as the primary key strategy:
1. Security: Prevents sequential ID enumeration attacks (e.g. scraping /orders/1, /orders/2).
2. Distributed Scalability: Permits distributed generation across microservices, database shards,
   and future mobile applications (Android/iOS offline sync) without cross-node coordination.
3. Decoupling: Decouples record creation from database sequence locks.

Timestamp Conventions:
----------------------
All models inherit TimestampMixin with timezone-aware UTC timestamps (DateTime(timezone=True)).
"""

import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, DateTime, String
from sqlalchemy.orm import declarative_base, declared_attr

Base = declarative_base()

def generate_uuid() -> str:
    """Generates standard UUIDv4 string."""
    return str(uuid.uuid4())

class TimestampMixin:
    """
    Standard mixin providing timezone-aware created_at and updated_at fields.
    """
    created_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
    updated_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

class BaseRecord(Base, TimestampMixin):
    """
    Abstract base model equipped with UUID primary key and timestamp tracking.
    """
    __abstract__ = True

    id = Column(String(36), primary_key=True, default=generate_uuid)
