#!/usr/bin/env python3
"""
Check actual province values in MongoDB pharmacies collection
"""

import os
from pymongo import MongoClient
from dotenv import load_dotenv

load_dotenv()

# Conectar a MongoDB
client = MongoClient(os.getenv('MONGO_LUDAFARMA_URL'))
db = client['ludafarma']

# Aggregation pipeline para ver valores únicos de provincia en farmacias Glovo
pipeline = [
    {"$match": {"tags": "GLOVO"}},
    {"$group": {"_id": "$contact.province", "count": {"$sum": 1}}},
    {"$sort": {"count": -1}},
    {"$limit": 20}
]

print("\n" + "="*80)
print("  🗺️ PROVINCIAS EN FARMACIAS GLOVO")
print("="*80 + "\n")

result = list(db.pharmacies.aggregate(pipeline))

if result:
    print(f"Total de provincias diferentes: {len(result)}\n")
    for item in result:
        province = item.get("_id") or "(sin provincia)"
        count = item.get("count", 0)
        print(f"  • {province:30} → {count:4} farmacias")
else:
    print("❌ No se encontraron resultados")

print("\n" + "="*80)

# Ahora buscar específicamente "Castellón" en varias formas
print("\n  🔍 BÚSQUEDA DE CASTELLÓN:")
print("="*80 + "\n")

test_values = ["Castellón", "Castellon", "CASTELLÓN", "CASTELLON", "castellón", "castellon"]

for test_val in test_values:
    count = db.pharmacies.count_documents({"tags": "GLOVO", "contact.province": test_val})
    print(f"  • '{test_val}' → {count} farmacias")

# Buscar con regex case-insensitive
print("\n  🔍 BÚSQUEDA CON REGEX (case-insensitive):")
print("─"*80 + "\n")

count_regex = db.pharmacies.count_documents({
    "tags": "GLOVO",
    "contact.province": {"$regex": "castellon", "$options": "i"}
})
print(f"  • Regex /castellon/i → {count_regex} farmacias")

print("\n" + "="*80 + "\n")
