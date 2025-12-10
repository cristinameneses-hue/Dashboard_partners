from typing import List, Dict, Any, Optional
from motor.motor_asyncio import AsyncIOMotorDatabase

from app.repositories.booking_repository import BookingRepository
from app.repositories.pharmacy_repository import PharmacyRepository
from app.schemas.metrics import (
    PeriodFilter,
    EcommerceMetrics,
    EcommerceResponse,
    BaseMetrics,
    TimeSeriesPoint,
)
from app.schemas.periods import get_period_dates
from app.core.config import get_settings


class EcommerceService:
    """
    Service for Ecommerce metrics calculation.
    Handles all partner-based booking metrics.
    """
    
    def __init__(self, database: AsyncIOMotorDatabase):
        self._booking_repo = BookingRepository(database)
        self._pharmacy_repo = PharmacyRepository(database)
        self._settings = get_settings()
    
    def _calculate_derived_metrics(
        self,
        metrics: Dict[str, Any],
        pharmacies_with_tag: int = 0
    ) -> EcommerceMetrics:
        """Calculate derived metrics from raw data."""
        
        gross_bookings = metrics.get("gross_bookings", 0)
        cancelled_bookings = metrics.get("cancelled_bookings", 0)
        net_bookings = metrics.get("net_bookings", 0)
        gross_gmv = metrics.get("gross_gmv", 0.0)
        cancelled_gmv = metrics.get("cancelled_gmv", 0.0)
        net_gmv = metrics.get("net_gmv", 0.0)
        pharmacies_with_orders = metrics.get("pharmacies_with_orders", 0)
        partner = metrics.get("partner", "")
        
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
        
        avg_orders_per_pharmacy = (
            net_bookings / pharmacies_with_orders 
            if pharmacies_with_orders > 0 else 0.0
        )
        
        avg_gmv_per_pharmacy = (
            net_gmv / pharmacies_with_orders 
            if pharmacies_with_orders > 0 else 0.0
        )
        
        # % Active Pharmacies (only for partners with tags)
        pct_active_pharmacies = None
        if pharmacies_with_tag > 0:
            pct_active_pharmacies = (
                pharmacies_with_orders / pharmacies_with_tag * 100
            )
        
        return EcommerceMetrics(
            partner=partner,
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
            pct_active_pharmacies=(
                round(pct_active_pharmacies, 2) 
                if pct_active_pharmacies is not None else None
            ),
            total_pharmacies_with_tag=pharmacies_with_tag if pharmacies_with_tag > 0 else None,
            pharmacies_with_orders=pharmacies_with_orders
        )
    
    async def get_metrics(self, period: PeriodFilter) -> EcommerceResponse:
        """Get ecommerce metrics for all partners in the given period."""
        
        start_date, end_date = get_period_dates(period)
        
        # Get raw metrics from repository
        raw_metrics = await self._booking_repo.get_all_ecommerce_metrics(
            start_date, end_date
        )
        
        # Get pharmacy counts for all partners
        pharmacy_counts = await self._pharmacy_repo.get_all_partner_pharmacy_counts()
        
        # Calculate metrics for each partner
        partners_metrics: List[EcommerceMetrics] = []
        
        for raw in raw_metrics:
            partner = raw.get("partner", "").lower()
            pharmacies_with_tag = pharmacy_counts.get(partner, 0)
            
            metrics = self._calculate_derived_metrics(raw, pharmacies_with_tag)
            metrics.partner = partner
            partners_metrics.append(metrics)
        
        # Get totals
        totals_raw = await self._booking_repo.get_ecommerce_totals(
            start_date, end_date
        )
        
        totals = self._calculate_totals(totals_raw)
        
        return EcommerceResponse(
            period=period,
            period_start=start_date,
            period_end=end_date,
            partners=partners_metrics,
            totals=totals
        )
    
    async def get_partner_metrics(
        self, 
        partner: str, 
        period: PeriodFilter
    ) -> EcommerceMetrics:
        """Get ecommerce metrics for a specific partner."""
        
        start_date, end_date = get_period_dates(period)
        
        # Get raw metrics
        raw_metrics = await self._booking_repo.get_ecommerce_metrics_by_partner(
            partner, start_date, end_date
        )
        
        # Get pharmacy count for this partner
        pharmacies_with_tag = await self._pharmacy_repo.count_pharmacies_with_partner_tag(
            partner
        )
        
        raw_metrics["partner"] = partner.lower()
        
        return self._calculate_derived_metrics(raw_metrics, pharmacies_with_tag)
    
    def _calculate_totals(self, raw: Dict[str, Any]) -> BaseMetrics:
        """Calculate total metrics across all partners."""
        
        gross_bookings = raw.get("gross_bookings", 0)
        cancelled_bookings = raw.get("cancelled_bookings", 0)
        net_bookings = raw.get("net_bookings", 0)
        gross_gmv = raw.get("gross_gmv", 0.0)
        cancelled_gmv = raw.get("cancelled_gmv", 0.0)
        net_gmv = raw.get("net_gmv", 0.0)
        pharmacies_with_orders = raw.get("pharmacies_with_orders", 0)
        
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
        
        avg_orders_per_pharmacy = (
            net_bookings / pharmacies_with_orders 
            if pharmacies_with_orders > 0 else 0.0
        )
        
        avg_gmv_per_pharmacy = (
            net_gmv / pharmacies_with_orders 
            if pharmacies_with_orders > 0 else 0.0
        )
        
        return BaseMetrics(
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
            pct_cancelled_gmv=round(pct_cancelled_gmv, 2)
        )

    async def get_time_series(
        self,
        period: PeriodFilter,
        group_by: str = "month",
        partners: Optional[List[str]] = None
    ) -> List[TimeSeriesPoint]:
        """Get time series metrics grouped by period."""
        
        start_date, end_date = get_period_dates(period)
        
        raw_data = await self._booking_repo.get_ecommerce_time_series(
            start_date, end_date, group_by, partners
        )
        
        result = []
        for item in raw_data:
            period_info = item.get("period", {})
            
            # Format period label
            if group_by == "week":
                label = f"S{period_info.get('week', 0)} {period_info.get('year', '')}"
            elif group_by == "quarter":
                label = f"Q{int(period_info.get('quarter', 0))} {period_info.get('year', '')}"
            elif group_by == "year":
                label = str(period_info.get('year', ''))
            else:  # month
                months = ['Ene', 'Feb', 'Mar', 'Abr', 'May', 'Jun', 
                         'Jul', 'Ago', 'Sep', 'Oct', 'Nov', 'Dic']
                month_idx = period_info.get('month', 1) - 1
                label = f"{months[month_idx]} {str(period_info.get('year', ''))[-2:]}"
            
            result.append(TimeSeriesPoint(
                period=label,
                gross_bookings=item.get("gross_bookings", 0),
                cancelled_bookings=item.get("cancelled_bookings", 0),
                net_bookings=item.get("net_bookings", 0),
                gross_gmv=round(item.get("gross_gmv", 0), 2),
                cancelled_gmv=round(item.get("cancelled_gmv", 0), 2),
                net_gmv=round(item.get("net_gmv", 0), 2),
                pharmacies_with_orders=item.get("pharmacies_with_orders", 0),
                average_ticket=round(item.get("average_ticket", 0), 2),
                avg_orders_per_pharmacy=round(item.get("avg_orders_per_pharmacy", 0), 2),
                avg_gmv_per_pharmacy=round(item.get("avg_gmv_per_pharmacy", 0), 2)
            ))
        
        return result


