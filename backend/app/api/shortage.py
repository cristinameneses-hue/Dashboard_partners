from typing import Optional
from datetime import date
from fastapi import APIRouter, Depends, Query
from motor.motor_asyncio import AsyncIOMotorDatabase

from app.core.database import get_database
from app.services.shortage_service import ShortageService
from app.schemas.metrics import (
    PeriodType,
    PeriodFilter,
    ShortageResponse,
)

router = APIRouter()


def get_shortage_service(
    db: AsyncIOMotorDatabase = Depends(get_database)
) -> ShortageService:
    """Dependency injection for ShortageService."""
    return ShortageService(db)


@router.get("", response_model=ShortageResponse)
async def get_shortage_metrics(
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
    service: ShortageService = Depends(get_shortage_service)
):
    """
    Get shortage (internal transfer) metrics.
    
    Global metrics (no partner filter) including:
    - Gross/Cancelled/Net Bookings
    - Gross/Cancelled/Net GMV
    - Average Ticket
    - Avg Orders/GMV per Pharmacy (based on receiving pharmacies)
    - % Cancelled Bookings/GMV
    - Active Pharmacies (total with active=1)
    - Sending Pharmacies (unique origins)
    - Receiving Pharmacies (unique targets)
    """
    period = PeriodFilter(
        period_type=period_type,
        start_date=start_date,
        end_date=end_date
    )
    
    return await service.get_metrics(period)


