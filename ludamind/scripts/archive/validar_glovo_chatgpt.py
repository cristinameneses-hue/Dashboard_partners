"""
Validación de KPIs de Glovo con ChatGPT/OpenAI

Compara los resultados obtenidos via MCP directo con las respuestas
que da ChatGPT al hacer preguntas en lenguaje natural.
"""

import json
import os
from dotenv import load_dotenv
from openai import OpenAI

# Cargar variables de entorno
load_dotenv()

# Cargar resultados MCP
with open('resultados_glovo_octubre_2025.json', 'r', encoding='utf-8') as f:
    resultados_mcp = json.load(f)

# Configurar OpenAI
client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))

# System prompt optimizado para consultas de negocio
SYSTEM_PROMPT = """
Eres un analista de datos experto en LudaFarma, una farmacia digital.

CONTEXTO DE NEGOCIO:
- Base de datos: MongoDB (ludafarma) con colección "bookings"
- Partners: Glovo, Uber, Danone, Hartmann, Carrefour, etc.
- Identificación: campo thirdUser.user contiene el nombre del partner
- GMV: Se calcula con thirdUser.price (si existe) o sum(items[].pvp * items[].quantity)
- Cancelados: bookings con state = "5a54c525b2948c860f00000d"
- Farmacias: campo "target" identifica la farmacia destino

DICCIONARIO SEMANTICO:
```json
{
  "bookings": {
    "_id": "ObjectId",
    "createdDate": "ISODate",
    "target": "pharmacy_id (string)",
    "state": "state_id (string)",
    "thirdUser": {
      "user": "partner_name (glovo, uber, etc)",
      "price": "gmv (number or null)"
    },
    "items": [
      {
        "pvp": "precio (number)",
        "quantity": "cantidad (number)"
      }
    ]
  }
}
```

INSTRUCCIONES:
1. Responde basándote en la estructura de datos de MongoDB
2. Para octubre 2025: filtrar por createdDate entre 2025-10-01 y 2025-11-01
3. Para Glovo: filtrar por thirdUser.user = "glovo"
4. Usa agregación MongoDB con $facet para calcular múltiples métricas
5. Proporciona números EXACTOS basados en la agregación
6. Si te dan resultados previos, compáralos y valida

FORMATO DE RESPUESTA:
Responde en español con:
- Los KPIs solicitados con valores numéricos
- Breve explicación de cómo se calculó
- Si es válido, compara con resultados previos
"""

def consultar_chatgpt(pregunta, contexto_adicional=""):
    """Consulta a ChatGPT/OpenAI con contexto de negocio."""

    messages = [
        {"role": "system", "content": SYSTEM_PROMPT}
    ]

    if contexto_adicional:
        messages.append({
            "role": "user",
            "content": f"CONTEXTO ADICIONAL:\n{contexto_adicional}\n\nPREGUNTA:\n{pregunta}"
        })
    else:
        messages.append({"role": "user", "content": pregunta})

    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=messages,
            temperature=0.1,
            max_tokens=1500
        )

        return response.choices[0].message.content

    except Exception as e:
        return f"ERROR: {str(e)}"


def main():
    print("=" * 80)
    print("VALIDACION DE KPIS DE GLOVO (OCTUBRE 2025) CON CHATGPT")
    print("=" * 80)
    print()

    # Mostrar resultados MCP
    print("RESULTADOS OBTENIDOS VIA MCP:")
    print("-" * 80)
    print(json.dumps(resultados_mcp['kpis'], indent=2, ensure_ascii=False))
    print()
    print(json.dumps(resultados_mcp['estadisticas_adicionales'], indent=2, ensure_ascii=False))
    print()
    print()

    # Preguntas de validación
    preguntas = [
        {
            "titulo": "GMV Total y Cancelado",
            "pregunta": """
Para el partner Glovo en octubre de 2025:
1. ¿Cuál es el GMV total?
2. ¿Cuál es el GMV cancelado?
3. ¿Cuál es el GMV activo (total - cancelado)?

Proporciona los valores exactos que deberían obtenerse con una agregación MongoDB.
"""
        },
        {
            "titulo": "Numero de Bookings",
            "pregunta": """
Para el partner Glovo en octubre de 2025:
1. ¿Cuántos bookings totales hubo?
2. ¿Cuántos bookings fueron cancelados?
3. ¿Cuántos bookings quedaron activos?

Explica cómo se identifican los cancelados (usando el campo state).
"""
        },
        {
            "titulo": "Farmacias Atendidas",
            "pregunta": """
Para el partner Glovo en octubre de 2025:
¿Cuántas farmacias únicas recibieron pedidos?

Explica cómo se cuentan las farmacias únicas (usando el campo target).
"""
        },
        {
            "titulo": "Validacion Completa",
            "pregunta": f"""
He ejecutado una consulta MongoDB con los siguientes resultados para Glovo en octubre 2025:

RESULTADOS MCP:
{json.dumps(resultados_mcp['kpis'], indent=2, ensure_ascii=False)}

¿Son estos resultados consistentes con la estructura de datos de MongoDB?
¿Hay alguna métrica que parezca incorrecta o sospechosa?
¿El pipeline de agregación usado es correcto?

Pipeline usado:
{json.dumps(resultados_mcp['pipeline_mongodb'], indent=2, ensure_ascii=False)}
"""
        }
    ]

    # Ejecutar validaciones
    for i, item in enumerate(preguntas, 1):
        print(f"[{i}/{len(preguntas)}] {item['titulo']}")
        print("=" * 80)
        print()

        respuesta = consultar_chatgpt(item['pregunta'])

        print("RESPUESTA CHATGPT:")
        print("-" * 80)
        print(respuesta)
        print()
        print()

        # Guardar respuesta
        item['respuesta_chatgpt'] = respuesta

    # Guardar todas las validaciones
    output = {
        "resultados_mcp": resultados_mcp,
        "validaciones_chatgpt": preguntas,
        "fecha_validacion": "2025-12-02"
    }

    with open('validacion_glovo_chatgpt.json', 'w', encoding='utf-8') as f:
        json.dump(output, f, indent=2, ensure_ascii=False)

    print("=" * 80)
    print("VALIDACION COMPLETADA")
    print("=" * 80)
    print()
    print("Archivo guardado: validacion_glovo_chatgpt.json")
    print()

    # Resumen
    print("RESUMEN:")
    print(f"  - Resultados MCP: {resultados_mcp['kpis']['num_bookings']} bookings")
    print(f"  - GMV MCP: EUR {resultados_mcp['kpis']['gmv_total_euros']:,.2f}")
    print(f"  - Validaciones ChatGPT: {len(preguntas)} consultas ejecutadas")
    print()


if __name__ == "__main__":
    main()
