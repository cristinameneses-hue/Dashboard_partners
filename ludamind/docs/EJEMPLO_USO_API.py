"""
Ejemplo de cómo usar ChatGPT API con el System Prompt de routing
para garantizar que siempre gestione bien las peticiones.
"""

import openai
import os
from typing import Dict, Any

# ═══════════════════════════════════════════════════════════════════════════════
# SYSTEM PROMPT - Incluir en CADA llamada API
# ═══════════════════════════════════════════════════════════════════════════════

LUDAFARMA_SYSTEM_PROMPT = """Eres un experto en routing de queries de bases de datos para LudaFarma.

CONTEXTO DEL SISTEMA:
- MySQL (db: "trends"): Analytics generales de productos, ventas históricas, trends, Z_Y scores
- MongoDB (db: "ludafarma"): Operaciones por canal de venta, bookings, usuarios, farmacias

REGLA DE ORO:
¿Menciona CANAL (Glovo, Uber, Danone, Carrefour, shortage, derivación)?
├─ SÍ  → MongoDB (collections: users + bookings)
└─ NO  → MySQL (table: trends_consolidado)

CANALES CONOCIDOS:
- Glovo, Uber Eats (delivery)
- Danone, Hartmann, Carrefour, Procter, AliExpress (B2B/marketplaces)
- Shortage/Derivaciones (NO es partner, es servicio: bookings.origin EXISTS)

CONCEPTOS CLAVE:
1. Partners son CANALES de venta (no compradores)
2. Shortage = derivación entre farmacias (campo: origin EXISTS)
3. GMV = SUM(items[i].pvp * items[i].quantity)
4. Partner booking: bookings.creator = partner_id (de users._id)
5. Shortage booking: bookings.origin EXISTS

PROCESO PARA CANALES (MongoDB):
1. Si es partner: users.findOne({idUser: "glovo"}) → obtener _id
2. Buscar bookings: {creator: ese_id_como_string, createdDate: filtro}
3. Si es shortage: {origin: {$exists: true}, createdDate: filtro}
4. Calcular GMV de items: SUM(pvp * quantity)
5. Excluir cancelados: state != "5a54c525b2948c860f00000d"

PROCESO PARA PRODUCTOS SIN CANAL (MySQL):
1. SELECT * FROM trends_consolidado WHERE nombre_producto LIKE '%X%'
2. Analytics general: Ventas_promedio, Z_Y, id_grupo, etc.

EJEMPLOS:
- "GMV de Glovo" → MongoDB (canal)
- "Ventas de Ibuprofeno" → MySQL (sin canal)
- "Ibuprofeno en Glovo" → MongoDB (canal + producto)
- "GMV de derivaciones" → MongoDB WHERE origin EXISTS
- "Top productos en Uber" → MongoDB (canal específico)

RESPONDE SIEMPRE:
1. Database elegida (MySQL o MongoDB)
2. Razón (menciona o no menciona canal)
3. Proceso/Query específico"""


# ═══════════════════════════════════════════════════════════════════════════════
# Función para llamar a ChatGPT con el system prompt
# ═══════════════════════════════════════════════════════════════════════════════

def query_chatgpt_with_routing(user_query: str) -> Dict[str, Any]:
    """
    Llama a ChatGPT API con el system prompt de routing.

    El system prompt se incluye en CADA llamada para garantizar
    que el modelo siempre tenga el contexto de routing.
    """

    # Configurar API key
    openai.api_key = os.getenv("OPENAI_API_KEY")

    # Llamada a la API con system prompt
    response = openai.ChatCompletion.create(
        model="gpt-4",  # o "gpt-3.5-turbo" si quieres más económico
        temperature=0.1,  # Baja temperatura para respuestas consistentes
        messages=[
            {
                "role": "system",
                "content": LUDAFARMA_SYSTEM_PROMPT  # ← CLAVE: System prompt en cada llamada
            },
            {
                "role": "user",
                "content": user_query
            }
        ]
    )

    return {
        "query": user_query,
        "response": response.choices[0].message.content,
        "model": response.model,
        "tokens": response.usage.total_tokens
    }


# ═══════════════════════════════════════════════════════════════════════════════
# Ejemplos de uso
# ═══════════════════════════════════════════════════════════════════════════════

if __name__ == "__main__":

    # Ejemplo 1: Query de canal (debe usar MongoDB)
    result1 = query_chatgpt_with_routing("GMV que se ha movido en Glovo la última semana")
    print("="*80)
    print("QUERY 1: GMV de Glovo")
    print("="*80)
    print(result1["response"])
    print(f"\nTokens usados: {result1['tokens']}")

    print("\n\n")

    # Ejemplo 2: Query de producto sin canal (debe usar MySQL)
    result2 = query_chatgpt_with_routing("Ventas totales de Ibuprofeno")
    print("="*80)
    print("QUERY 2: Ventas de Ibuprofeno")
    print("="*80)
    print(result2["response"])
    print(f"\nTokens usados: {result2['tokens']}")

    print("\n\n")

    # Ejemplo 3: Producto EN canal (debe usar MongoDB)
    result3 = query_chatgpt_with_routing("Cuántas unidades de Paracetamol se vendieron en Glovo")
    print("="*80)
    print("QUERY 3: Paracetamol en Glovo")
    print("="*80)
    print(result3["response"])
    print(f"\nTokens usados: {result3['tokens']}")

    print("\n\n")

    # Ejemplo 4: Shortage (debe usar MongoDB con origin EXISTS)
    result4 = query_chatgpt_with_routing("GMV de derivaciones del último mes")
    print("="*80)
    print("QUERY 4: GMV de derivaciones")
    print("="*80)
    print(result4["response"])
    print(f"\nTokens usados: {result4['tokens']}")


# ═══════════════════════════════════════════════════════════════════════════════
# VENTAJAS de este enfoque:
# ═══════════════════════════════════════════════════════════════════════════════
#
# ✅ PERSISTENTE: El contexto se incluye en cada llamada
# ✅ CONSISTENTE: Siempre tiene las mismas reglas
# ✅ FLEXIBLE: Puedes actualizar el system prompt sin reentrenar
# ✅ ECONÓMICO: No necesitas fine-tuning (más barato)
# ✅ RÁPIDO: Funciona inmediatamente
#
# DESVENTAJAS:
# ⚠️ Consume tokens del system prompt en cada llamada (~600 tokens)
# ⚠️ Ligeramente más lento que un modelo fine-tuneado
#
# ═══════════════════════════════════════════════════════════════════════════════


# ═══════════════════════════════════════════════════════════════════════════════
# OPTIMIZACIÓN: Versión compacta del system prompt (si quieres ahorrar tokens)
# ═══════════════════════════════════════════════════════════════════════════════

LUDAFARMA_SYSTEM_PROMPT_COMPACT = """Routing LudaFarma:
MongoDB si menciona: Glovo, Uber, Danone, Carrefour, shortage, derivación
MySQL si NO menciona canal (analytics general)

Partners (MongoDB): users.findOne({idUser}), luego bookings.creator
Shortage (MongoDB): bookings.origin EXISTS
GMV: SUM(items[].pvp * quantity)

Ejemplos:
"GMV Glovo" → MongoDB
"Ventas Ibuprofeno" → MySQL
"Ibuprofeno en Glovo" → MongoDB"""

# Esta versión usa ~100 tokens vs ~600 tokens de la versión completa
