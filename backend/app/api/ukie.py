"""
Ukie (Ireland) API Router

Endpoints for Ireland ecommerce metrics using the same service layer
as Spain but connected to the Ireland database.
"""

from typing import Optional
from datetime import date
from fastapi import APIRouter, Depends, Query, HTTPException
from motor.motor_asyncio import AsyncIOMotorDatabase

from app.core.database import get_database_ireland
from app.services.ukie_service import UkieService
from app.schemas.metrics import (
    PeriodType,
    PeriodFilter,
    EcommerceResponse,
    EcommerceMetrics,
    TimeSeriesResponse,
)

router = APIRouter()


def get_ukie_service(
    db: AsyncIOMotorDatabase = Depends(get_database_ireland)
) -> UkieService:
    """Dependency injection for UkieService using Ireland database."""
    return UkieService(db)


@router.get("", response_model=EcommerceResponse)
async def get_ukie_metrics(
    period_type: PeriodType = Query(
        PeriodType.THIS_MONTH,
        description="Period type for filtering"
    ),
    start_date: Optional[date] = Query(
        None,
        description="Start date for custom period (YYYY-MM-DD)"
    ),
    end_date: Optional[date] = Query(
        None,
        description="End date for custom period (YYYY-MM-DD)"
    ),
    service: UkieService = Depends(get_ukie_service)
):
    """
    Get ecommerce metrics for all partners in Ireland (Ukie).

    Returns metrics including:
    - Gross/Cancelled/Net Bookings
    - Gross/Cancelled/Net GMV
    - Average Ticket
    - Avg Orders/GMV per Pharmacy
    - % Cancelled Bookings/GMV
    """
    period = PeriodFilter(
        period_type=period_type,
        start_date=start_date,
        end_date=end_date
    )

    return await service.get_metrics(period)


@router.get("/partners", response_model=list)
async def get_ukie_partners(
    service: UkieService = Depends(get_ukie_service)
):
    """Get list of available partners in Ireland."""
    return await service.get_available_partners()


@router.get("/partner/{partner}", response_model=EcommerceMetrics)
async def get_ukie_partner_metrics(
    partner: str,
    period_type: PeriodType = Query(
        PeriodType.THIS_MONTH,
        description="Period type for filtering"
    ),
    start_date: Optional[date] = Query(
        None,
        description="Start date for custom period"
    ),
    end_date: Optional[date] = Query(
        None,
        description="End date for custom period"
    ),
    service: UkieService = Depends(get_ukie_service)
):
    """
    Get ecommerce metrics for a specific partner in Ireland.
    """
    period = PeriodFilter(
        period_type=period_type,
        start_date=start_date,
        end_date=end_date
    )

    return await service.get_partner_metrics(partner, period)


@router.get("/timeseries", response_model=TimeSeriesResponse)
async def get_ukie_time_series(
    period_type: PeriodType = Query(
        PeriodType.THIS_YEAR,
        description="Period type for filtering"
    ),
    start_date: Optional[date] = Query(
        None,
        description="Start date for custom period"
    ),
    end_date: Optional[date] = Query(
        None,
        description="End date for custom period"
    ),
    group_by: str = Query(
        "month",
        description="Group by: week, month, quarter, year"
    ),
    partners: Optional[str] = Query(
        None,
        description="Comma-separated list of partners to filter"
    ),
    service: UkieService = Depends(get_ukie_service)
):
    """
    Get time series metrics for Ireland charts.

    Returns metrics grouped by time period (week, month, quarter, year).
    Optionally filter by specific partners.
    """
    period = PeriodFilter(
        period_type=period_type,
        start_date=start_date,
        end_date=end_date
    )

    # Parse partners list
    partners_list = None
    if partners:
        partners_list = [p.strip() for p in partners.split(",")]

    result = await service.get_time_series(period, group_by, partners_list)

    return TimeSeriesResponse(
        group_by=group_by,
        data=result["data"],
        total_pharmacies=result["total_pharmacies"]
    )


@router.get("/partner-timeseries")
async def get_ukie_partner_time_series(
    period_type: PeriodType = Query(
        PeriodType.THIS_YEAR,
        description="Period type for filtering"
    ),
    start_date: Optional[date] = Query(
        None,
        description="Start date for custom period"
    ),
    end_date: Optional[date] = Query(
        None,
        description="End date for custom period"
    ),
    group_by: str = Query(
        "month",
        description="Group by: week, month, quarter, year"
    ),
    service: UkieService = Depends(get_ukie_service)
):
    """
    Get time series metrics grouped by partner for Ireland stacked charts.

    Returns orders and GMV data organized by period with partner breakdown.
    """
    period = PeriodFilter(
        period_type=period_type,
        start_date=start_date,
        end_date=end_date
    )

    return await service.get_partner_time_series(period, group_by)
