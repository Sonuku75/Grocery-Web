"""
Cartify Address Model (Module 2)

Persists customer delivery addresses with coordinates, default selection, and ownership constraints.
"""

from sqlalchemy import Boolean, Column, Float, ForeignKey, Index, String
from sqlalchemy.orm import relationship
from app.db.base import Base, TimestampMixin, generate_uuid

class Address(Base, TimestampMixin):
    __tablename__ = "addresses"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    user_id = Column(
        String(36),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    label = Column(String(50), default="Home", nullable=False)
    recipient_name = Column(String(100), nullable=False)
    phone = Column(String(20), nullable=False)
    address_line_1 = Column(String(255), nullable=False)
    address_line_2 = Column(String(255), nullable=True)
    landmark = Column(String(255), nullable=True)
    city = Column(String(100), nullable=False)
    state = Column(String(100), nullable=False)
    country = Column(String(100), default="India", nullable=False)
    postal_code = Column(String(20), nullable=False, index=True)
    latitude = Column(Float, nullable=True)
    longitude = Column(Float, nullable=True)
    is_default = Column(Boolean, default=False, nullable=False)

    # Relationships
    user = relationship("User", back_populates="addresses")

    __table_args__ = (
        Index("idx_addresses_user_default", "user_id", "is_default"),
        Index("idx_addresses_postal_code", "postal_code"),
    )

    # Compatibility properties for legacy / frontend property aliases
    @property
    def full_name(self) -> str:
        return self.recipient_name

    @full_name.setter
    def full_name(self, value: str) -> None:
        self.recipient_name = value

    @property
    def mobile(self) -> str:
        return self.phone

    @mobile.setter
    def mobile(self, value: str) -> None:
        self.phone = value

    @property
    def house_flat(self) -> str:
        return self.address_line_1

    @house_flat.setter
    def house_flat(self, value: str) -> None:
        self.address_line_1 = value

    @property
    def street(self) -> str:
        return self.address_line_2 or ""

    @street.setter
    def street(self, value: str) -> None:
        self.address_line_2 = value

    @property
    def area(self) -> str:
        return self.address_line_2 or ""

    @area.setter
    def area(self, value: str) -> None:
        self.address_line_2 = value

    @property
    def pincode(self) -> str:
        return self.postal_code

    @pincode.setter
    def pincode(self, value: str) -> None:
        self.postal_code = value

    @property
    def address_type(self) -> str:
        return self.label

    @address_type.setter
    def address_type(self, value: str) -> None:
        self.label = value
