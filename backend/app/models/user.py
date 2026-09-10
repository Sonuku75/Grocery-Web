from sqlalchemy import Boolean, Column, String, Index
from app.models.base import Base, TimestampMixin, generate_uuid

class User(Base, TimestampMixin):
    __tablename__ = "users"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    email = Column(String(255), unique=True, index=True, nullable=False)
    mobile = Column(String(32), unique=True, index=True, nullable=False)
    full_name = Column(String(255), nullable=False)
    hashed_password = Column(String(255), nullable=False)
    avatar_url = Column(String(1024), nullable=True)
    role = Column(String(32), default="customer", nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)

    __table_args__ = (
        Index("idx_users_email_active", "email", "is_active"),
    )
