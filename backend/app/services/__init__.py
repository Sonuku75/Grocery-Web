"""
Cartify Services Registry (Module 2)
"""

from app.services.auth import AuthService
from app.services.user import UserService
from app.services.address import AddressService

__all__ = ["AuthService", "UserService", "AddressService"]
