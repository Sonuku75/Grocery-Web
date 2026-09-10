from sqlalchemy import Boolean, Column, ForeignKey, Index, String
from app.models.base import Base, TimestampMixin, generate_uuid

class Address(Base, TimestampMixin):
    __tablename__ = "addresses"

    id = Column(String(64), primary_key=True, default=generate_uuid)
    user_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    full_name = Column(String(255), nullable=False)
    mobile = Column(String(32), nullable=False)
    house_flat = Column(String(255), nullable=False)
    street = Column(String(255), nullable=False)
    area = Column(String(255), nullable=False)
    city = Column(String(128), nullable=False)
    state = Column(String(128), nullable=False)
    pincode = Column(String(32), nullable=False)
    landmark = Column(String(255), nullable=True)
    address_type = Column(String(32), default="home", nullable=False)
    is_default = Column(Boolean, default=False, nullable=False)

    __table_args__ = (
        Index("idx_addresses_user_default", "user_id", "is_default"),
    )
