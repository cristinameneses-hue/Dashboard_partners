from typing import Dict, Any, List, Optional
from datetime import datetime
from motor.motor_asyncio import AsyncIOMotorDatabase

from app.core.config import get_settings


class BookingRepository:
    """
    Repository for accessing bookings collection.
    Handles both Ecommerce (thirdUser) and Shortage (origin) queries.
    """
    
    def __init__(self, database: AsyncIOMotorDatabase):
        self._db = database
        self._collection = database["bookings"]
        self._settings = get_settings()
    
    def _round_to_2_decimals(self, value: Any) -> Dict[str, Any]:
        """
        Round a value to 2 decimal places.
        Compatible with MongoDB < 4.2 (uses $trunc instead of $round).
        """
        return {
            "$divide": [
                {"$trunc": {"$add": [{"$multiply": [value, 100]}, 0.5]}},
                100
            ]
        }
    
    def _gmv_calculation(self) -> Dict[str, Any]:
        """
        GMV calculation pipeline stage.
        GMV = SUM(items[].pvp * items[].quantity)
        """
        return {
            "$reduce": {
                "input": "$items",
                "initialValue": 0,
                "in": {
                    "$add": [
                        "$$value",
                        {
                            "$multiply": [
                                {"$toDouble": {"$ifNull": ["$$this.pvp", 0]}},
                                {"$toInt": {"$ifNull": ["$$this.quantity", 0]}}
                            ]
                        }
                    ]
                }
            }
        }
    
    async def get_ecommerce_metrics_by_partner(
        self,
        partner: str,
        start_date: datetime,
        end_date: datetime
    ) -> Dict[str, Any]:
        """
        Get ecommerce metrics for a specific partner.
        Ecommerce = bookings with thirdUser.user and WITHOUT origin.
        """
        cancelled_state = self._settings.cancelled_state_id
        
        pipeline = [
            # Match ecommerce bookings for this partner in date range
            {
                "$match": {
                    "thirdUser.user": {"$regex": f"^{partner}$", "$options": "i"},
                    "origin": {"$exists": False},
                    "createdDate": {"$gte": start_date, "$lte": end_date}
                }
            },
            # Add computed fields
            {
                "$addFields": {
                    "gmv": self._gmv_calculation(),
                    "is_cancelled": {"$eq": ["$state", cancelled_state]}
                }
            },
            # Group to calculate metrics
            {
                "$group": {
                    "_id": None,
                    "gross_bookings": {"$sum": 1},
                    "cancelled_bookings": {
                        "$sum": {"$cond": ["$is_cancelled", 1, 0]}
                    },
                    "gross_gmv": {"$sum": "$gmv"},
                    "cancelled_gmv": {
                        "$sum": {"$cond": ["$is_cancelled", "$gmv", 0]}
                    },
                    "unique_pharmacies": {"$addToSet": "$target"}
                }
            },
            # Project final metrics
            {
                "$project": {
                    "_id": 0,
                    "gross_bookings": 1,
                    "cancelled_bookings": 1,
                    "net_bookings": {"$subtract": ["$gross_bookings", "$cancelled_bookings"]},
                    "gross_gmv": self._round_to_2_decimals("$gross_gmv"),
                    "cancelled_gmv": self._round_to_2_decimals("$cancelled_gmv"),
                    "net_gmv": self._round_to_2_decimals({"$subtract": ["$gross_gmv", "$cancelled_gmv"]}),
                    "pharmacies_with_orders": {"$size": "$unique_pharmacies"}
                }
            }
        ]
        
        cursor = self._collection.aggregate(pipeline)
        results = await cursor.to_list(length=1)
        
        if results:
            return results[0]
        
        return {
            "gross_bookings": 0,
            "cancelled_bookings": 0,
            "net_bookings": 0,
            "gross_gmv": 0.0,
            "cancelled_gmv": 0.0,
            "net_gmv": 0.0,
            "pharmacies_with_orders": 0
        }
    
    async def get_all_ecommerce_metrics(
        self,
        start_date: datetime,
        end_date: datetime
    ) -> List[Dict[str, Any]]:
        """
        Get ecommerce metrics for allowed partners only.
        Uses partner list from config settings.
        """
        cancelled_state = self._settings.cancelled_state_id
        
        # Build partner regex conditions for allowed partners only
        partner_conditions = [
            {"thirdUser.user": {"$regex": f"^{p}$", "$options": "i"}}
            for p in self._settings.partners
        ]
        
        pipeline = [
            # Match only allowed partners in date range
            {
                "$match": {
                    "origin": {"$exists": False},
                    "createdDate": {"$gte": start_date, "$lte": end_date},
                    "$or": partner_conditions
                }
            },
            # Add computed fields
            {
                "$addFields": {
                    "gmv": self._gmv_calculation(),
                    "is_cancelled": {"$eq": ["$state", cancelled_state]},
                    "partner_lower": {"$toLower": "$thirdUser.user"}
                }
            },
            # Group by partner
            {
                "$group": {
                    "_id": "$partner_lower",
                    "gross_bookings": {"$sum": 1},
                    "cancelled_bookings": {
                        "$sum": {"$cond": ["$is_cancelled", 1, 0]}
                    },
                    "gross_gmv": {"$sum": "$gmv"},
                    "cancelled_gmv": {
                        "$sum": {"$cond": ["$is_cancelled", "$gmv", 0]}
                    },
                    "unique_pharmacies": {"$addToSet": "$target"}
                }
            },
            # Project final metrics
            {
                "$project": {
                    "partner": "$_id",
                    "gross_bookings": 1,
                    "cancelled_bookings": 1,
                    "net_bookings": {"$subtract": ["$gross_bookings", "$cancelled_bookings"]},
                    "gross_gmv": self._round_to_2_decimals("$gross_gmv"),
                    "cancelled_gmv": self._round_to_2_decimals("$cancelled_gmv"),
                    "net_gmv": self._round_to_2_decimals({"$subtract": ["$gross_gmv", "$cancelled_gmv"]}),
                    "pharmacies_with_orders": {"$size": "$unique_pharmacies"}
                }
            },
            {"$sort": {"net_gmv": -1}}
        ]
        
        cursor = self._collection.aggregate(pipeline)
        return await cursor.to_list(length=100)
    
    async def get_shortage_metrics(
        self,
        start_date: datetime,
        end_date: datetime
    ) -> Dict[str, Any]:
        """
        Get shortage metrics (global, no partner filter).
        Shortage = bookings WITH origin field.
        """
        cancelled_state = self._settings.cancelled_state_id
        
        pipeline = [
            # Match shortage bookings in date range
            {
                "$match": {
                    "origin": {"$exists": True},
                    "createdDate": {"$gte": start_date, "$lte": end_date}
                }
            },
            # Add computed fields
            {
                "$addFields": {
                    "gmv": self._gmv_calculation(),
                    "is_cancelled": {"$eq": ["$state", cancelled_state]}
                }
            },
            # Group to calculate metrics
            {
                "$group": {
                    "_id": None,
                    "gross_bookings": {"$sum": 1},
                    "cancelled_bookings": {
                        "$sum": {"$cond": ["$is_cancelled", 1, 0]}
                    },
                    "gross_gmv": {"$sum": "$gmv"},
                    "cancelled_gmv": {
                        "$sum": {"$cond": ["$is_cancelled", "$gmv", 0]}
                    },
                    "unique_origins": {"$addToSet": "$origin"},
                    "unique_targets": {"$addToSet": "$target"}
                }
            },
            # Project final metrics
            {
                "$project": {
                    "_id": 0,
                    "gross_bookings": 1,
                    "cancelled_bookings": 1,
                    "net_bookings": {"$subtract": ["$gross_bookings", "$cancelled_bookings"]},
                    "gross_gmv": self._round_to_2_decimals("$gross_gmv"),
                    "cancelled_gmv": self._round_to_2_decimals("$cancelled_gmv"),
                    "net_gmv": self._round_to_2_decimals({"$subtract": ["$gross_gmv", "$cancelled_gmv"]}),
                    "sending_pharmacies": {"$size": "$unique_origins"},
                    "receiving_pharmacies": {"$size": "$unique_targets"}
                }
            }
        ]
        
        cursor = self._collection.aggregate(pipeline)
        results = await cursor.to_list(length=1)
        
        if results:
            return results[0]
        
        return {
            "gross_bookings": 0,
            "cancelled_bookings": 0,
            "net_bookings": 0,
            "gross_gmv": 0.0,
            "cancelled_gmv": 0.0,
            "net_gmv": 0.0,
            "sending_pharmacies": 0,
            "receiving_pharmacies": 0
        }
    
    async def get_ecommerce_time_series(
        self,
        start_date: datetime,
        end_date: datetime,
        group_by: str = "month",  # week, month, quarter, year
        partners: Optional[List[str]] = None
    ) -> List[Dict[str, Any]]:
        """
        Get ecommerce metrics grouped by time period.
        group_by: 'week', 'month', 'quarter', 'year'
        """
        cancelled_state = self._settings.cancelled_state_id
        
        # Define date grouping based on group_by parameter
        if group_by == "week":
            date_group = {
                "year": {"$year": "$createdDate"},
                "week": {"$isoWeek": "$createdDate"}
            }
            sort_fields = {"_id.year": 1, "_id.week": 1}
        elif group_by == "quarter":
            date_group = {
                "year": {"$year": "$createdDate"},
                "quarter": {
                    "$ceil": {"$divide": [{"$month": "$createdDate"}, 3]}
                }
            }
            sort_fields = {"_id.year": 1, "_id.quarter": 1}
        elif group_by == "year":
            date_group = {
                "year": {"$year": "$createdDate"}
            }
            sort_fields = {"_id.year": 1}
        else:  # month (default)
            date_group = {
                "year": {"$year": "$createdDate"},
                "month": {"$month": "$createdDate"}
            }
            sort_fields = {"_id.year": 1, "_id.month": 1}
        
        # Use provided partners or default to allowed partners from config
        allowed_partners = partners if partners else self._settings.partners
        
        # Build partner regex conditions - always filter by allowed partners
        partner_conditions = [
            {"thirdUser.user": {"$regex": f"^{p}$", "$options": "i"}} 
            for p in allowed_partners
        ]
        
        # Build match stage with partner filter
        match_stage: Dict[str, Any] = {
            "origin": {"$exists": False},
            "createdDate": {"$gte": start_date, "$lte": end_date},
            "$or": partner_conditions
        }
        
        pipeline = [
            {"$match": match_stage},
            {
                "$addFields": {
                    "gmv": self._gmv_calculation(),
                    "is_cancelled": {"$eq": ["$state", cancelled_state]}
                }
            },
            {
                "$group": {
                    "_id": date_group,
                    "gross_bookings": {"$sum": 1},
                    "cancelled_bookings": {
                        "$sum": {"$cond": ["$is_cancelled", 1, 0]}
                    },
                    "gross_gmv": {"$sum": "$gmv"},
                    "cancelled_gmv": {
                        "$sum": {"$cond": ["$is_cancelled", "$gmv", 0]}
                    },
                    "unique_pharmacies": {"$addToSet": "$target"}
                }
            },
            {"$sort": sort_fields},
            {
                "$project": {
                    "_id": 0,
                    "period": "$_id",
                    "gross_bookings": 1,
                    "cancelled_bookings": 1,
                    "net_bookings": {"$subtract": ["$gross_bookings", "$cancelled_bookings"]},
                    "gross_gmv": self._round_to_2_decimals("$gross_gmv"),
                    "cancelled_gmv": self._round_to_2_decimals("$cancelled_gmv"),
                    "net_gmv": self._round_to_2_decimals({"$subtract": ["$gross_gmv", "$cancelled_gmv"]}),
                    "pharmacies_with_orders": {"$size": "$unique_pharmacies"},
                    "average_ticket": {
                        "$cond": [
                            {"$gt": [{"$subtract": ["$gross_bookings", "$cancelled_bookings"]}, 0]},
                            self._round_to_2_decimals({
                                "$divide": [
                                    {"$subtract": ["$gross_gmv", "$cancelled_gmv"]},
                                    {"$subtract": ["$gross_bookings", "$cancelled_bookings"]}
                                ]
                            }),
                            0
                        ]
                    },
                    "avg_orders_per_pharmacy": {
                        "$cond": [
                            {"$gt": [{"$size": "$unique_pharmacies"}, 0]},
                            self._round_to_2_decimals({
                                "$divide": [
                                    {"$subtract": ["$gross_bookings", "$cancelled_bookings"]},
                                    {"$size": "$unique_pharmacies"}
                                ]
                            }),
                            0
                        ]
                    },
                    "avg_gmv_per_pharmacy": {
                        "$cond": [
                            {"$gt": [{"$size": "$unique_pharmacies"}, 0]},
                            self._round_to_2_decimals({
                                "$divide": [
                                    {"$subtract": ["$gross_gmv", "$cancelled_gmv"]},
                                    {"$size": "$unique_pharmacies"}
                                ]
                            }),
                            0
                        ]
                    }
                }
            }
        ]
        
        cursor = self._collection.aggregate(pipeline)
        return await cursor.to_list(length=100)

    async def get_ecommerce_totals(
        self,
        start_date: datetime,
        end_date: datetime,
        partners: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Get total ecommerce metrics. Filters by allowed partners from config by default.
        """
        cancelled_state = self._settings.cancelled_state_id
        
        # Use provided partners or default to allowed partners from config
        allowed_partners = partners if partners else self._settings.partners
        
        # Build partner regex conditions
        partner_conditions = [
            {"thirdUser.user": {"$regex": f"^{p}$", "$options": "i"}}
            for p in allowed_partners
        ]
        
        pipeline = [
            {
                "$match": {
                    "thirdUser.user": {"$exists": True},
                    "origin": {"$exists": False},
                    "createdDate": {"$gte": start_date, "$lte": end_date},
                    "$or": partner_conditions
                }
            },
            {
                "$addFields": {
                    "gmv": self._gmv_calculation(),
                    "is_cancelled": {"$eq": ["$state", cancelled_state]}
                }
            },
            {
                "$group": {
                    "_id": None,
                    "gross_bookings": {"$sum": 1},
                    "cancelled_bookings": {
                        "$sum": {"$cond": ["$is_cancelled", 1, 0]}
                    },
                    "gross_gmv": {"$sum": "$gmv"},
                    "cancelled_gmv": {
                        "$sum": {"$cond": ["$is_cancelled", "$gmv", 0]}
                    },
                    "unique_pharmacies": {"$addToSet": "$target"}
                }
            },
            {
                "$project": {
                    "_id": 0,
                    "gross_bookings": 1,
                    "cancelled_bookings": 1,
                    "net_bookings": {"$subtract": ["$gross_bookings", "$cancelled_bookings"]},
                    "gross_gmv": self._round_to_2_decimals("$gross_gmv"),
                    "cancelled_gmv": self._round_to_2_decimals("$cancelled_gmv"),
                    "net_gmv": self._round_to_2_decimals({"$subtract": ["$gross_gmv", "$cancelled_gmv"]}),
                    "pharmacies_with_orders": {"$size": "$unique_pharmacies"}
                }
            }
        ]
        
        cursor = self._collection.aggregate(pipeline)
        results = await cursor.to_list(length=1)
        
        if results:
            return results[0]
        
        return {
            "gross_bookings": 0,
            "cancelled_bookings": 0,
            "net_bookings": 0,
            "gross_gmv": 0.0,
            "cancelled_gmv": 0.0,
            "net_gmv": 0.0,
            "pharmacies_with_orders": 0
        }

    async def get_total_pharmacies(
        self, 
        partners: Optional[List[str]] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> int:
        """
        Get total unique pharmacies that have received ecommerce orders.
        Uses allowed partners from config by default.
        If dates are provided, only count pharmacies with orders in that period.
        """
        # Use provided partners or default to allowed partners from config
        allowed_partners = partners if partners else self._settings.partners
        
        # Build partner regex conditions
        partner_conditions = [
            {"thirdUser.user": {"$regex": f"^{p}$", "$options": "i"}}
            for p in allowed_partners
        ]
        
        match_stage: Dict[str, Any] = {
            "origin": {"$exists": False},
            "target": {"$exists": True},
            "$or": partner_conditions
        }
        
        # Add date filter if provided
        if start_date and end_date:
            match_stage["createdDate"] = {
                "$gte": start_date,
                "$lte": end_date
            }
        
        pipeline = [
            {"$match": match_stage},
            {"$group": {"_id": "$target"}},
            {"$count": "total"}
        ]
        
        cursor = self._collection.aggregate(pipeline)
        results = await cursor.to_list(length=1)
        
        if results:
            return results[0].get("total", 0)
        return 0

    async def get_ecommerce_partner_time_series(
        self,
        start_date: datetime,
        end_date: datetime,
        group_by: str = "month",
        partners: Optional[List[str]] = None
    ) -> List[Dict[str, Any]]:
        """
        Get ecommerce metrics grouped by time period and partner.
        Returns data for stacked charts showing partner contributions.
        Filters by allowed partners from config by default.
        """
        cancelled_state = self._settings.cancelled_state_id
        
        # Use provided partners or default to allowed partners from config
        allowed_partners = partners if partners else self._settings.partners
        
        # Build partner regex conditions
        partner_conditions = [
            {"thirdUser.user": {"$regex": f"^{p}$", "$options": "i"}}
            for p in allowed_partners
        ]
        
        # Define date grouping based on group_by parameter
        if group_by == "week":
            date_group = {
                "year": {"$year": "$createdDate"},
                "week": {"$isoWeek": "$createdDate"}
            }
            sort_fields = {"_id.year": 1, "_id.week": 1}
        elif group_by == "quarter":
            date_group = {
                "year": {"$year": "$createdDate"},
                "quarter": {
                    "$ceil": {"$divide": [{"$month": "$createdDate"}, 3]}
                }
            }
            sort_fields = {"_id.year": 1, "_id.quarter": 1}
        elif group_by == "year":
            date_group = {
                "year": {"$year": "$createdDate"}
            }
            sort_fields = {"_id.year": 1}
        else:  # month (default)
            date_group = {
                "year": {"$year": "$createdDate"},
                "month": {"$month": "$createdDate"}
            }
            sort_fields = {"_id.year": 1, "_id.month": 1}
        
        pipeline = [
            {
                "$match": {
                    "thirdUser.user": {"$exists": True},
                    "origin": {"$exists": False},
                    "createdDate": {"$gte": start_date, "$lte": end_date},
                    "$or": partner_conditions
                }
            },
            {
                "$addFields": {
                    "gmv": self._gmv_calculation(),
                    "is_cancelled": {"$eq": ["$state", cancelled_state]},
                    "partner_lower": {"$toLower": "$thirdUser.user"}
                }
            },
            {
                "$group": {
                    "_id": {
                        **date_group,
                        "partner": "$partner_lower"
                    },
                    "gross_bookings": {"$sum": 1},
                    "cancelled_bookings": {
                        "$sum": {"$cond": ["$is_cancelled", 1, 0]}
                    },
                    "gross_gmv": {"$sum": "$gmv"},
                    "cancelled_gmv": {
                        "$sum": {"$cond": ["$is_cancelled", "$gmv", 0]}
                    }
                }
            },
            {"$sort": sort_fields},
            {
                "$project": {
                    "_id": 0,
                    "period": {
                        k: v for k, v in {
                            "year": "$_id.year",
                            "month": "$_id.month" if group_by == "month" else None,
                            "week": "$_id.week" if group_by == "week" else None,
                            "quarter": "$_id.quarter" if group_by == "quarter" else None
                        }.items() if v is not None
                    },
                    "partner": "$_id.partner",
                    "gross_bookings": 1,
                    "net_bookings": {"$subtract": ["$gross_bookings", "$cancelled_bookings"]},
                    "gross_gmv": self._round_to_2_decimals("$gross_gmv"),
                    "net_gmv": self._round_to_2_decimals({"$subtract": ["$gross_gmv", "$cancelled_gmv"]})
                }
            }
        ]
        
        cursor = self._collection.aggregate(pipeline)
        return await cursor.to_list(length=500)


