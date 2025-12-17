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
        
        totals = await self._calculate_totals(
            totals_raw,
            partners=None,  # No filter for global totals
            start_date=start_date,
            end_date=end_date
        )
        
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
    
    async def _calculate_totals(
        self, 
        raw: Dict[str, Any],
        partners: Optional[List[str]] = None,
        start_date: Optional[Any] = None,
        end_date: Optional[Any] = None
    ) -> BaseMetrics:
        """Calculate total metrics across all partners or filtered by partners."""
        
        gross_bookings = raw.get("gross_bookings", 0)
        cancelled_bookings = raw.get("cancelled_bookings", 0)
        net_bookings = raw.get("net_bookings", 0)
        gross_gmv = raw.get("gross_gmv", 0.0)
        cancelled_gmv = raw.get("cancelled_gmv", 0.0)
        net_gmv = raw.get("net_gmv", 0.0)
        pharmacies_with_orders = raw.get("pharmacies_with_orders", 0)
        
        # Get total pharmacies (filtered by partners if provided)
        total_pharmacies = await self._booking_repo.get_total_pharmacies(
            partners=partners,
            start_date=start_date,
            end_date=end_date
        )
        
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
            pct_cancelled_gmv=round(pct_cancelled_gmv, 2),
            total_pharmacies=total_pharmacies,
            pharmacies_with_orders=pharmacies_with_orders
        )

    async def get_time_series(
        self,
        period: PeriodFilter,
        group_by: str = "month",
        partners: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """Get time series metrics grouped by period."""
        
        start_date, end_date = get_period_dates(period)
        
        # Get total pharmacies (filtered by partners if provided)
        total_pharmacies = await self._booking_repo.get_total_pharmacies(
            partners=partners,
            start_date=None,  # Don't filter by date for total pharmacies base
            end_date=None
        )
        
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
            
            pharmacies_with_orders = item.get("pharmacies_with_orders", 0)
            pct_active = (pharmacies_with_orders / total_pharmacies * 100) if total_pharmacies > 0 else 0
            
            result.append(TimeSeriesPoint(
                period=label,
                gross_bookings=item.get("gross_bookings", 0),
                cancelled_bookings=item.get("cancelled_bookings", 0),
                net_bookings=item.get("net_bookings", 0),
                gross_gmv=round(item.get("gross_gmv", 0), 2),
                cancelled_gmv=round(item.get("cancelled_gmv", 0), 2),
                net_gmv=round(item.get("net_gmv", 0), 2),
                pharmacies_with_orders=pharmacies_with_orders,
                total_pharmacies=total_pharmacies,
                pct_pharmacies_active=round(pct_active, 1),
                average_ticket=round(item.get("average_ticket", 0), 2),
                avg_orders_per_pharmacy=round(item.get("avg_orders_per_pharmacy", 0), 2),
                avg_gmv_per_pharmacy=round(item.get("avg_gmv_per_pharmacy", 0), 2)
            ))
        
        return {
            "data": result,
            "total_pharmacies": total_pharmacies
        }

    async def get_partner_time_series(
        self,
        period: PeriodFilter,
        group_by: str = "month"
    ) -> Dict[str, Any]:
        """Get time series metrics grouped by period and partner for stacked charts."""
        
        start_date, end_date = get_period_dates(period)
        
        raw_data = await self._booking_repo.get_ecommerce_partner_time_series(
            start_date, end_date, group_by
        )
        
        # Organize data by period with partner as keys
        orders_by_period: Dict[str, Dict[str, Any]] = {}
        gmv_by_period: Dict[str, Dict[str, Any]] = {}
        
        for item in raw_data:
            period_info = item.get("period", {})
            partner = item.get("partner", "unknown")
            
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
            
            # Initialize period if not exists
            if label not in orders_by_period:
                orders_by_period[label] = {"period": label}
                gmv_by_period[label] = {"period": label}
            
            # Add partner data
            orders_by_period[label][partner] = item.get("net_bookings", 0)
            gmv_by_period[label][partner] = round(item.get("net_gmv", 0), 2)
        
        # Convert to sorted lists
        months_list = ['Ene', 'Feb', 'Mar', 'Abr', 'May', 'Jun', 
                       'Jul', 'Ago', 'Sep', 'Oct', 'Nov', 'Dic']
        
        def sort_key(label: str) -> tuple:
            # Sort by year first, then by period number
            parts = label.split()
            if len(parts) >= 2:
                year = int(parts[-1]) if len(parts[-1]) == 4 else int(f"20{parts[-1]}")
                first_part = parts[0]
                
                # Check if it's a month name first (before checking S/Q prefix)
                if first_part in months_list:
                    return (year, months_list.index(first_part) + 1)
                elif first_part.startswith("S") and first_part[1:].isdigit():  # Week (S1, S52, etc.)
                    return (year, int(first_part[1:]))
                elif first_part.startswith("Q") and first_part[1:].isdigit():  # Quarter
                    return (year, int(first_part[1:]))
            elif len(parts) == 1 and parts[0].isdigit():  # Year only
                return (int(parts[0]), 0)
            return (0, 0)
        
        sorted_periods = sorted(orders_by_period.keys(), key=sort_key)
        
        orders_data = [orders_by_period[p] for p in sorted_periods]
        gmv_data = [gmv_by_period[p] for p in sorted_periods]
        
        # Get all unique partners
        all_partners = set()
        for item in raw_data:
            all_partners.add(item.get("partner", "unknown"))
        
        return {
            "group_by": group_by,
            "partners": list(all_partners),
            "orders": orders_data,
            "gmv": gmv_data
        }


