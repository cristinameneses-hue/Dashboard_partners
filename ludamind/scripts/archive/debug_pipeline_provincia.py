#!/usr/bin/env python3
"""
Debug - Ver qué pipeline genera GPT para queries de provincia
"""

import os
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from domain.services.query_interpreter import QueryInterpreter
from dotenv import load_dotenv

load_dotenv()

interpreter = QueryInterpreter()

queries = [
    "cuantas farmacias tenemos en glovo?",
    "cuantas farmacias tenemos en glovo en castellon?",
    "cuantas farmacias tenemos en glovo en la provincia de castellon?",
]

print("\n" + "="*80)
print("  🔍 DEBUG - PIPELINES GENERADOS POR GPT")
print("="*80)

for query in queries:
    print(f"\n{'─'*80}")
    print(f"📝 Query: {query}")
    print(f"{'─'*80}")

    result = interpreter.interpret_query(query, mode="conversational")

    print(f"\n✅ Collection: {result.get('collection', 'N/A')}")
    print(f"✅ Time Range: {result.get('time_range', 'N/A')}")
    print(f"✅ Confidence: {result.get('confidence', 0):.2f}")

    pipeline = result.get('pipeline', [])

    if pipeline and len(pipeline) > 0:
        print(f"\n📊 PIPELINE ({len(pipeline)} stages):")
        import json
        for idx, stage in enumerate(pipeline, 1):
            print(f"\n  Stage {idx}:")
            print(f"  {json.dumps(stage, indent=4, default=str)}")
    else:
        print(f"\n❌ NO SE GENERÓ PIPELINE")

    explanation = result.get('explanation', '')
    if explanation:
        print(f"\n💬 Explanation:")
        print(f"  {explanation[:200]}...")

print("\n" + "="*80 + "\n")
