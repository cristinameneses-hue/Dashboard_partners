from datetime import datetime, date
from typing import Optional, List
from pydantic import BaseModel, Field
from enum import Enum


class PeriodType(str, Enum):
    """Available period types for filtering."""
    THIS_YEAR = "this_year"
    LAST_YEAR = "last_year"
    THIS_MONTH = "this_month"
    LAST_MONTH = "last_month"
    THIS_WEEK = "this_week"
    LAST_WEEK = "last_week"
    Q1 = "q1"
    Q2 = "q2"
    Q3 = "q3"
    Q4 = "q4"
    CUSTOM = "custom"


class PeriodFilter(BaseModel):
    """Period filter for metrics queries."""
    period_type: PeriodType = PeriodType.THIS_MONTH
    start_date: Optional[date] = None  # Required for CUSTOM
    end_date: Optional[date] = None    # Required for CUSTOM


class BaseMetrics(BaseModel):
    """Base metrics shared between Ecommerce and Shortage."""
    gross_bookings: int = 0
    cancelled_bookings: int = 0
    net_bookings: int = 0
    gross_gmv: float = 0.0
    cancelled_gmv: float = 0.0
    net_gmv: float = 0.0
    average_ticket: float = 0.0
    avg_orders_per_pharmacy: float = 0.0
    avg_gmv_per_pharmacy: float = 0.0
    pct_cancelled_bookings: float = 0.0
    pct_cancelled_gmv: float = 0.0
    total_pharmacies: int = 0
    pharmacies_with_orders: int = 0


class EcommerceMetrics(BaseMetrics):
    """Metrics for a specific partner (Ecommerce)."""
    partner: str
    pct_active_pharmacies: Optional[float] = None  # None for uber/justeat
    total_pharmacies_with_tag: Optional[int] = None
    pharmacies_with_orders: int = 0


class ShortageMetrics(BaseMetrics):
    """Metrics for Shortage (global, no partner filter)."""
    active_pharmacies: int = 0      # pharmacies with active=1
    sending_pharmacies: int = 0     # distinct origins
    receiving_pharmacies: int = 0   # distinct targets


class EcommerceResponse(BaseModel):
    """Response for Ecommerce metrics."""
    period: PeriodFilter
    period_start: datetime
    period_end: datetime
    partners: List[EcommerceMetrics]
    totals: BaseMetrics


class ShortageResponse(BaseModel):
    """Response for Shortage metrics."""
    period: PeriodFilter
    period_start: datetime
    period_end: datetime
    metrics: ShortageMetrics


class TimeSeriesPoint(BaseModel):
    """Time series data point for charts."""
    period: str  # Label like "Ene 25", "S12 2025", "Q1 2025", "2025"
    gross_bookings: int = 0
    cancelled_bookings: int = 0
    net_bookings: int = 0
    gross_gmv: float = 0.0
    cancelled_gmv: float = 0.0
    net_gmv: float = 0.0
    pharmacies_with_orders: int = 0
    total_pharmacies: int = 0
    pct_pharmacies_active: float = 0.0
    average_ticket: float = 0.0
    avg_orders_per_pharmacy: float = 0.0
    avg_gmv_per_pharmacy: float = 0.0


class TimeSeriesResponse(BaseModel):
    """Response for time series data."""
    group_by: str  # week, month, quarter, year
    data: List[TimeSeriesPoint]
    total_pharmacies: int = 0


class ShortageTimeSeriesPoint(BaseModel):
    """Time series data point for shortage charts."""
    period: str  # Label like "Ene 25", "S12 2025", "Q1 2025", "2025"
    # Pharmacy metrics
    total_pharmacies: int = 0  # Total pharmacies in shortage system
    active_pharmacies: int = 0  # Union of sending + receiving (participated in period)
    sending_pharmacies: int = 0  # Pharmacies that sent at least 1 order
    receiving_pharmacies: int = 0  # Pharmacies that received at least 1 order
    pct_active: float = 0.0  # % active pharmacies (over total)
    pct_sending: float = 0.0  # % sending pharmacies (over total)
    pct_receiving: float = 0.0  # % receiving pharmacies (over total)
    # Order metrics
    gross_bookings: int = 0
    cancelled_bookings: int = 0
    net_bookings: int = 0
    pct_cancelled: float = 0.0
    delta_bookings: int = 0  # Delta vs previous period
    pct_growth_bookings: float = 0.0  # % growth vs previous period
    # GMV metrics
    gross_gmv: float = 0.0
    cancelled_gmv: float = 0.0
    net_gmv: float = 0.0
    pct_cancelled_gmv: float = 0.0
    delta_gmv: float = 0.0  # Delta vs previous period
    pct_growth_gmv: float = 0.0  # % growth vs previous period
    # Cumulative metrics
    cumulative_ops: int = 0
    cumulative_gmv: float = 0.0


class ShortageTimeSeriesResponse(BaseModel):
    """Response for shortage time series data."""
    group_by: str  # week, month, quarter, year
    data: List[ShortageTimeSeriesPoint]
    total_pharmacies: int = 0  # Total pharmacies in shortage system


class PartnerSummary(BaseModel):
    """Summary of a single partner for the dashboard."""
    partner: str
    net_bookings: int
    net_gmv: float
    average_ticket: float
    pct_cancelled_bookings: float
    pct_active_pharmacies: Optional[float] = None


class DashboardSummary(BaseModel):
    """Dashboard summary with KPIs."""
    period: PeriodFilter
    period_start: datetime
    period_end: datetime
    
    # Totals
    total_net_bookings: int
    total_net_gmv: float
    total_average_ticket: float
    total_pct_cancelled: float
    
    # Per partner summary
    partners: List[PartnerSummary]


