from typing import Dict, Any
from motor.motor_asyncio import AsyncIOMotorDatabase

from app.repositories.booking_repository import BookingRepository
from app.repositories.pharmacy_repository import PharmacyRepository
from app.schemas.metrics import (
    PeriodFilter,
    ShortageMetrics,
    ShortageResponse,
)
from app.schemas.periods import get_period_dates


class ShortageService:
    """
    Service for Shortage metrics calculation.
    Handles all internal transfer (shortage) metrics - global, no partner filter.
    """
    
    def __init__(self, database: AsyncIOMotorDatabase):
        self._booking_repo = BookingRepository(database)
        self._pharmacy_repo = PharmacyRepository(database)
    
    def _calculate_derived_metrics(
        self,
        raw: Dict[str, Any],
        active_pharmacies: int
    ) -> ShortageMetrics:
        """Calculate derived metrics from raw data."""
        
        gross_bookings = raw.get("gross_bookings", 0)
        cancelled_bookings = raw.get("cancelled_bookings", 0)
        net_bookings = raw.get("net_bookings", 0)
        gross_gmv = raw.get("gross_gmv", 0.0)
        cancelled_gmv = raw.get("cancelled_gmv", 0.0)
        net_gmv = raw.get("net_gmv", 0.0)
        sending_pharmacies = raw.get("sending_pharmacies", 0)
        receiving_pharmacies = raw.get("receiving_pharmacies", 0)
        
        # Calculate percentages and averages
        pct_cancelled_bookings = (
            (cancelled_bookings / gross_bookings * 100) 
            if gross_bookings > 0 else 0.0
        )
        
        pct_cancelled_gmv = (
            (cancelled_gmv / gross_gmv * 100) 
            if gross_gmv > 0 else 0.0
        )
        
        average_ticket = (
            net_gmv / net_bookings 
            if net_bookings > 0 else 0.0
        )
        
        # Avg per pharmacy based on receiving pharmacies (target) as per user request
        avg_orders_per_pharmacy = (
            net_bookings / receiving_pharmacies 
            if receiving_pharmacies > 0 else 0.0
        )
        
        avg_gmv_per_pharmacy = (
            net_gmv / receiving_pharmacies 
            if receiving_pharmacies > 0 else 0.0
        )
        
        return ShortageMetrics(
            gross_bookings=gross_bookings,
            cancelled_bookings=cancelled_bookings,
            net_bookings=net_bookings,
            gross_gmv=round(gross_gmv, 2),
            cancelled_gmv=round(cancelled_gmv, 2),
            net_gmv=round(net_gmv, 2),
            average_ticket=round(average_ticket, 2),
            avg_orders_per_pharmacy=round(avg_orders_per_pharmacy, 2),
            avg_gmv_per_pharmacy=round(avg_gmv_per_pharmacy, 2),
            pct_cancelled_bookings=round(pct_cancelled_bookings, 2),
            pct_cancelled_gmv=round(pct_cancelled_gmv, 2),
            active_pharmacies=active_pharmacies,
            sending_pharmacies=sending_pharmacies,
            receiving_pharmacies=receiving_pharmacies
        )
    
    async def get_metrics(self, period: PeriodFilter) -> ShortageResponse:
        """Get shortage metrics for the given period."""
        
        start_date, end_date = get_period_dates(period)
        
        # Get raw shortage metrics
        raw_metrics = await self._booking_repo.get_shortage_metrics(
            start_date, end_date
        )
        
        # Get active pharmacies count
        active_pharmacies = await self._pharmacy_repo.count_active_pharmacies()
        
        # Calculate derived metrics
        metrics = self._calculate_derived_metrics(raw_metrics, active_pharmacies)
        
        return ShortageResponse(
            period=period,
            period_start=start_date,
            period_end=end_date,
            metrics=metrics
        )


