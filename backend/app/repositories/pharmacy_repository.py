from typing import Dict, Any, List, Optional
from motor.motor_asyncio import AsyncIOMotorDatabase

from app.core.config import get_settings


class PharmacyRepository:
    """
    Repository for accessing pharmacies collection.
    Handles pharmacy counts and tag-based queries.
    """
    
    def __init__(self, database: AsyncIOMotorDatabase):
        self._db = database
        self._collection = database["pharmacies"]
        self._settings = get_settings()
    
    async def count_active_pharmacies(self) -> int:
        """Count pharmacies with active=1."""
        return await self._collection.count_documents({"active": 1})
    
    async def count_pharmacies_with_partner_tag(self, partner: str) -> int:
        """
        Count pharmacies that have at least one tag for the given partner.
        Returns 0 if partner has no tags (uber, justeat).
        """
        if partner.lower() in self._settings.partners_without_tags:
            return 0
        
        tags = self._settings.partner_tags.get(partner.lower(), [])
        
        if not tags:
            return 0
        
        # Count pharmacies that have at least one of the partner's tags
        return await self._collection.count_documents({
            "tags": {"$in": tags}
        })
    
    async def get_all_partner_pharmacy_counts(self) -> Dict[str, int]:
        """
        Get pharmacy counts for all partners with tags.
        Returns dict: {partner: count}
        """
        counts = {}
        
        for partner, tags in self._settings.partner_tags.items():
            if tags:
                count = await self._collection.count_documents({
                    "tags": {"$in": tags}
                })
                counts[partner] = count
        
        return counts
    
    async def get_pharmacy_distribution_by_province(self) -> List[Dict[str, Any]]:
        """Get pharmacy count distribution by province."""
        pipeline = [
            {"$match": {"active": 1}},
            {
                "$group": {
                    "_id": "$contact.province",
                    "count": {"$sum": 1}
                }
            },
            {"$sort": {"count": -1}},
            {"$limit": 20}
        ]
        
        cursor = self._collection.aggregate(pipeline)
        results = await cursor.to_list(length=20)
        
        return [
            {"province": r["_id"] or "Sin provincia", "count": r["count"]}
            for r in results
        ]
    
    async def get_pharmacy_distribution_by_city(self) -> List[Dict[str, Any]]:
        """Get pharmacy count distribution by city."""
        pipeline = [
            {"$match": {"active": 1}},
            {
                "$group": {
                    "_id": "$contact.city",
                    "count": {"$sum": 1}
                }
            },
            {"$sort": {"count": -1}},
            {"$limit": 20}
        ]
        
        cursor = self._collection.aggregate(pipeline)
        results = await cursor.to_list(length=20)
        
        return [
            {"city": r["_id"] or "Sin ciudad", "count": r["count"]}
            for r in results
        ]
    
    async def get_partner_tag_distribution(self) -> List[Dict[str, Any]]:
        """
        Get distribution of pharmacies by partner tags.
        Shows how many pharmacies are active in each partner.
        """
        results = []
        
        for partner, tags in self._settings.partner_tags.items():
            if tags:
                count = await self._collection.count_documents({
                    "tags": {"$in": tags},
                    "active": 1
                })
                results.append({
                    "partner": partner,
                    "pharmacies": count,
                    "tags": tags
                })
        
        # Sort by pharmacy count descending
        results.sort(key=lambda x: x["pharmacies"], reverse=True)
        
        return results


