from typing import Optional
from datetime import date
from fastapi import APIRouter, Depends, Query
from motor.motor_asyncio import AsyncIOMotorDatabase

from app.core.database import get_database
from app.core.config import get_settings
from app.services.ecommerce_service import EcommerceService
from app.schemas.metrics import (
    PeriodType,
    PeriodFilter,
    EcommerceResponse,
    EcommerceMetrics,
)

router = APIRouter()


def get_ecommerce_service(
    db: AsyncIOMotorDatabase = Depends(get_database)
) -> EcommerceService:
    """Dependency injection for EcommerceService."""
    return EcommerceService(db)


@router.get("", response_model=EcommerceResponse)
async def get_ecommerce_metrics(
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
    service: EcommerceService = Depends(get_ecommerce_service)
):
    """
    Get ecommerce metrics for all partners.
    
    Returns metrics including:
    - Gross/Cancelled/Net Bookings
    - Gross/Cancelled/Net GMV
    - Average Ticket
    - Avg Orders/GMV per Pharmacy
    - % Cancelled Bookings/GMV
    - % Active Pharmacies (for partners with tags)
    """
    period = PeriodFilter(
        period_type=period_type,
        start_date=start_date,
        end_date=end_date
    )
    
    return await service.get_metrics(period)


@router.get("/partners", response_model=list)
async def get_available_partners():
    """Get list of available partners."""
    settings = get_settings()
    return [
        {
            "id": partner,
            "name": partner.title().replace("-", " "),
            "has_tags": partner not in settings.partners_without_tags
        }
        for partner in settings.partners
    ]


@router.get("/partner/{partner}", response_model=EcommerceMetrics)
async def get_partner_metrics(
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
    service: EcommerceService = Depends(get_ecommerce_service)
):
    """
    Get ecommerce metrics for a specific partner.
    """
    period = PeriodFilter(
        period_type=period_type,
        start_date=start_date,
        end_date=end_date
    )
    
    return await service.get_partner_metrics(partner, period)


