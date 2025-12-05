from typing import List, Dict, Any
from fastapi import APIRouter, Depends
from motor.motor_asyncio import AsyncIOMotorDatabase

from app.core.database import get_database
from app.repositories.pharmacy_repository import PharmacyRepository

router = APIRouter()


def get_pharmacy_repository(
    db: AsyncIOMotorDatabase = Depends(get_database)
) -> PharmacyRepository:
    """Dependency injection for PharmacyRepository."""
    return PharmacyRepository(db)


@router.get("/count/active")
async def get_active_pharmacies_count(
    repo: PharmacyRepository = Depends(get_pharmacy_repository)
):
    """Get count of active pharmacies."""
    count = await repo.count_active_pharmacies()
    return {"active_pharmacies": count}


@router.get("/distribution/province")
async def get_pharmacy_distribution_by_province(
    repo: PharmacyRepository = Depends(get_pharmacy_repository)
) -> List[Dict[str, Any]]:
    """Get pharmacy distribution by province."""
    return await repo.get_pharmacy_distribution_by_province()


@router.get("/distribution/city")
async def get_pharmacy_distribution_by_city(
    repo: PharmacyRepository = Depends(get_pharmacy_repository)
) -> List[Dict[str, Any]]:
    """Get pharmacy distribution by city."""
    return await repo.get_pharmacy_distribution_by_city()


@router.get("/distribution/partner")
async def get_partner_tag_distribution(
    repo: PharmacyRepository = Depends(get_pharmacy_repository)
) -> List[Dict[str, Any]]:
    """Get pharmacy distribution by partner tags."""
    return await repo.get_partner_tag_distribution()


