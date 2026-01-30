"""
UkieService - Ecommerce service for Ireland (Ukie) database.

Inherits from EcommerceService but uses Ireland-specific partner configuration.
"""

from typing import List, Optional
from motor.motor_asyncio import AsyncIOMotorDatabase

from app.services.ecommerce_service import EcommerceService
from app.repositories.booking_repository import BookingRepository
from app.repositories.pharmacy_repository import PharmacyRepository
from app.core.config import get_settings


class UkieBookingRepository(BookingRepository):
    """
    Booking repository that uses Ireland partner configuration.
    Overrides the partners list to use partners_ireland from settings.
    """

    def __init__(self, database: AsyncIOMotorDatabase):
        super().__init__(database)
        # Override partners list with Ireland-specific partners
        self._settings = IrelandSettingsWrapper(self._settings)


class IrelandSettingsWrapper:
    """
    Wrapper that overrides the partners list with Ireland-specific partners.
    All other settings are passed through from the original settings.
    """

    def __init__(self, original_settings):
        self._original = original_settings

    @property
    def partners(self) -> List[str]:
        """Return Ireland-specific partners instead of Spain partners."""
        return self._original.partners_ireland

    @property
    def partners_without_tags(self) -> List[str]:
        """All Ireland partners are without tags (no pharmacy tag system in Ireland)."""
        return self._original.partners_ireland

    @property
    def cancelled_state_id(self) -> str:
        """Pass through cancelled state ID."""
        return self._original.cancelled_state_id

    @property
    def partner_tags(self) -> dict:
        """No tags in Ireland."""
        return {}

    def __getattr__(self, name):
        """Pass through all other attributes to the original settings."""
        return getattr(self._original, name)


class UkieService(EcommerceService):
    """
    Ecommerce service for Ireland (Ukie) database.
    Uses Ireland-specific partner configuration.
    """

    def __init__(self, database: AsyncIOMotorDatabase):
        # Don't call super().__init__() - we need to use our custom repository
        self._booking_repo = UkieBookingRepository(database)
        self._pharmacy_repo = PharmacyRepository(database)
        self._settings = get_settings()

    async def get_available_partners(self) -> List[str]:
        """Return the list of available partners for Ireland."""
        return self._settings.partners_ireland
