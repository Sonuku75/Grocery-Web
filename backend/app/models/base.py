from datetime import datetime, timezone
import uuid
from sqlalchemy import Column, DateTime, String
from sqlalchemy.orm import declarative_base, declared_attr

Base = declarative_base()

def generate_uuid() -> str:
    return str(uuid.uuid4())

class TimestampMixin:
    @declared_attr
    def created_at(cls):
        return Column(
            DateTime(timezone=True),
            default=lambda: datetime.now(timezone.utc),
            nullable=False,
        )

    @declared_attr
    def updated_at(cls):
        return Column(
            DateTime(timezone=True),
            default=lambda: datetime.now(timezone.utc),
            onupdate=lambda: datetime.now(timezone.utc),
            nullable=False,
        )
