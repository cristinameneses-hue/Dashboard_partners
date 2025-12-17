"""
Script to check what partner names exist in the database
"""
import asyncio
from datetime import datetime
from motor.motor_asyncio import AsyncIOMotorClient

async def check_partners():
    client = AsyncIOMotorClient("mongodb://iimReports:Reports2019@localhost:27017/LudaFarma-PRO?readPreference=primary&directConnection=true&ssl=false")
    db = client["LudaFarma-PRO"]
    
    # Get unique partner names
    pipeline = [
        {
            "$match": {
                "thirdUser.user": {"$exists": True},
                "origin": {"$exists": False},
            }
        },
        {
            "$group": {
                "_id": {"$toLower": "$thirdUser.user"}
            }
        },
        {
            "$sort": {"_id": 1}
        }
    ]
    
    print("=== All unique partner names in database ===")
    async for doc in db.bookings.aggregate(pipeline):
        print(f"  - {doc['_id']}")
    
    # Check specific partners
    target_partners = ["amazon", "chiesi", "ferrer"]
    print(f"\n=== Checking specific partners: {target_partners} ===")
    
    for partner in target_partners:
        # Count bookings for this partner (case insensitive, exact match)
        count = await db.bookings.count_documents({
            "thirdUser.user": {"$regex": f"^{partner}$", "$options": "i"},
            "origin": {"$exists": False}
        })
        print(f"  {partner}: {count} bookings")
        
        # Get a sample document
        sample = await db.bookings.find_one({
            "thirdUser.user": {"$regex": f"^{partner}$", "$options": "i"},
            "origin": {"$exists": False}
        })
        if sample:
            print(f"    Sample thirdUser.user value: '{sample.get('thirdUser', {}).get('user', 'N/A')}'")
    
    # Also check with case-sensitive patterns to see if there's a mismatch
    print("\n=== Checking partner name variations ===")
    variations = ["Amazon", "AMAZON", "Chiesi", "CHIESI", "Ferrer", "FERRER"]
    for v in variations:
        count = await db.bookings.count_documents({
            "thirdUser.user": v,
            "origin": {"$exists": False}
        })
        if count > 0:
            print(f"  '{v}': {count} bookings")

if __name__ == "__main__":
    asyncio.run(check_partners())

