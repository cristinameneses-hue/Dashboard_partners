#!/usr/bin/env python3
"""
Verificar que la query de provincia funciona correctamente
usando el mismo código que usa la aplicación Flask
"""

import os
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from pymongo import MongoClient
from domain.services.smart_query_processor import SmartQueryProcessor
from dotenv import load_dotenv

load_dotenv()

# Conectar a MongoDB (mismo que Flask)
client = MongoClient(os.getenv('MONGO_LUDAFARMA_URL'))
db = client['ludafarma']

# Crear processor (usa el mismo repositorio que Flask)
processor = SmartQueryProcessor(db, os.getenv('OPENAI_API_KEY'))

print("\n" + "="*80)
print("  ✅ VERIFICACIÓN - QUERY DE PROVINCIA ARREGLADA")
print("="*80 + "\n")

# Test 1: Query simple (debería funcionar)
print("Test 1: Query simple de Glovo")
print("─"*80)
query1 = "cuantas farmacias tenemos en glovo?"
result1 = processor.process(query1, mode="conversational")
print(f"Query: {query1}")
print(f"Respuesta:\n{result1.get('answer', 'N/A')}\n")

# Test 2: Query con provincia (el que estaba fallando)
print("\nTest 2: Query con provincia de Castellón")
print("─"*80)
query2 = "cuantas farmacias tenemos en glovo en la provincia de castellon?"
result2 = processor.process(query2, mode="conversational")
print(f"Query: {query2}")
print(f"Respuesta:\n{result2.get('answer', 'N/A')}\n")
print(f"Debug - Result keys: {result2.keys()}")
if 'data' in result2:
    print(f"Debug - Data: {result2['data']}")

# Test 3: Otra provincia para comparar
print("\nTest 3: Query con provincia de Madrid")
print("─"*80)
query3 = "cuantas farmacias tenemos en glovo en la provincia de madrid?"
result3 = processor.process(query3, mode="conversational")
print(f"Query: {query3}")
print(f"Respuesta:\n{result3.get('answer', 'N/A')}\n")

print("="*80 + "\n")
