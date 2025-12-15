# 📋 PLAN: Queries Predefinidas - Nueva Implementación

**Fecha**: 2025-01-04
**Objetivo**: Sustituir queries antiguas por nuevas queries optimizadas con comparación GPT vs Hardcoded

---

## 🎯 Queries a Implementar

### ✅ YA IMPLEMENTADA (CONSERVAR)
- **KPIs completos de partner** (línea 897-1087 en app_luda_mind.py)
  - GMV total, GMV cancelado, bookings, bookings cancelados, farmacias con pedidos
  - Soporta períodos: hoy, semana, mes, mes pasado, meses específicos

---

## ❌ QUERIES A ELIMINAR (FLOJAS)
- Top farmacias por partner (línea 802-894) - Será reemplazada por versión mejorada

---

## 🆕 QUERIES NUEVAS A IMPLEMENTAR

### 🏥 MODO FARMACIA (6 queries)

#### 1. **Ventas en todos los partners de una farmacia**
- **Input**: `{farmacia_id}`
- **Output**: Tabla con GMV y pedidos por cada partner
- **Complejidad**: Media
- **Pipeline esperado**:
  ```json
  [
    {"$match": {"target": "{farmacia_id}"}},
    {"$group": {
      "_id": "$thirdUser.user",
      "total_gmv": {"$sum": "..."},
      "total_pedidos": {"$sum": 1}
    }},
    {"$sort": {"total_gmv": -1}}
  ]
  ```

#### 2. **Porcentaje de cancelaciones de una farmacia**
- **Input**: `{farmacia_id}`, `{periodo?}`
- **Output**: % cancelaciones, total bookings, bookings cancelados
- **Complejidad**: Media
- **Requiere**: ID de estado "cancelado" (5a54c525b2948c860f00000d)

#### 3. **Métricas de shortage de una farmacia**
- **Input**: `{farmacia_id}`, `{periodo?}`
- **Output**: Número de shortages, GMV de shortage, productos más solicitados
- **Complejidad**: Media
- **Filtro**: `{origin: {$exists: true}}`

#### 4. **Número de farmacias por provincia**
- **Input**: Ninguno (o filtro `{activas_solo?}`)
- **Output**: Tabla provincia → count
- **Complejidad**: Baja
- **Pipeline esperado**:
  ```json
  [
    {"$match": {"active": 1}},
    {"$group": {"_id": "$contact.province", "count": {"$sum": 1}}},
    {"$sort": {"count": -1}}
  ]
  ```

#### 5. **Porcentaje de farmacias activas**
- **Input**: Ninguno (o filtro `{por_provincia?}`)
- **Output**: % activas, total farmacias, farmacias activas
- **Complejidad**: Baja
- **Pipeline esperado**:
  ```json
  [
    {"$facet": {
      "activas": [{"$match": {"active": 1}}, {"$count": "count"}],
      "totales": [{"$count": "count"}]
    }}
  ]
  ```

#### 6. **Top farmacias con más ventas**
- **Input**: `{limite?}`, `{periodo?}`
- **Output**: Ranking de farmacias por GMV total
- **Complejidad**: Media
- **Pipeline esperado**: Similar a "top farmacias por partner" pero sin filtro de partner

---

### 📦 MODO PRODUCTOS (7 queries)

#### 1. **Sell in y sell out de un producto**
- **Input**: `{producto_code}`
- **Output**: Sell in (compras farmacias), Sell out (ventas a clientes)
- **Complejidad**: Alta
- **NOTA**: Requiere definir qué es sell in vs sell out en el contexto
  - ¿Sell in = movimientos en stockItems?
  - ¿Sell out = bookings.items[]?

#### 2. **Margen de un producto**
- **Input**: `{producto_code}`
- **Output**: Margen promedio (PVP - PVA), % margen
- **Complejidad**: Media
- **Requiere**: stockItems con pvp y pva

#### 3. **Presencia de un producto**
- **Input**: `{producto_code}`
- **Output**: Número de farmacias con stock > 0
- **Complejidad**: Baja
- **Pipeline esperado**:
  ```json
  [
    {"$match": {"code": "{producto_code}", "quantity": {"$gt": 0}}},
    {"$count": "total_farmacias"}
  ]
  ```

#### 4. **Obtener ean13 más repetido en base a un CN y viceversa**
- **Input**: `{cn}` o `{ean13}`
- **Output**: Relaciones CN ↔ EAN13 con frecuencias
- **Complejidad**: Media
- **NOTA**: Algunos productos tienen múltiples EAN13 para un mismo CN

#### 5. **Métricas de venta de un producto en nuestros partners**
- **Input**: `{producto_code}`, `{periodo?}`
- **Output**: Tabla partner → unidades vendidas, GMV, pedidos
- **Complejidad**: Media
- **Pipeline esperado**:
  ```json
  [
    {"$match": {"createdDate": {"$gte": "..."}}},
    {"$unwind": "$items"},
    {"$match": {"items.code": "{producto_code}"}},
    {"$group": {
      "_id": "$thirdUser.user",
      "unidades": {"$sum": "$items.quantity"},
      "gmv": {"$sum": {"$multiply": ["$items.pvp", "$items.quantity"]}},
      "pedidos": {"$sum": 1}
    }}
  ]
  ```

#### 6. **Top productos más vendidos en la BBDD**
- **Input**: `{limite?}`, `{periodo?}`
- **Output**: Ranking de productos por unidades vendidas
- **Complejidad**: Media
- **Pipeline esperado**: Similar a query 5 pero sin filtro de producto

#### 7. **Top catálogos más extensos de la BBDD**
- **Input**: `{limite?}`
- **Output**: Ranking de farmacias por número de productos en catálogo
- **Complejidad**: Media
- **Requiere**: stockItems agrupados por farmacia

---

### 🤝 MODO PARTNERS (3 queries)

#### 1. **Comparativa de gmv, pedidos, ticket medio y media de cancelaciones por partner**
- **Input**: `{periodo?}`
- **Output**: Tabla comparativa con TODOS los partners
- **Complejidad**: Alta
- **Columnas**: Partner | GMV | Pedidos | Ticket Medio | % Cancelaciones
- **Pipeline esperado**: `$facet` con múltiples métricas

#### 2. **Top farmacias con más cancelaciones por partner**
- **Input**: `{partner}`, `{limite?}`, `{periodo?}`
- **Output**: Ranking de farmacias con más bookings cancelados
- **Complejidad**: Media
- **Filtro**: `{state: "5a54c525b2948c860f00000d"}`

#### 3. **Ventas por partners según provincia**
- **Input**: `{provincia?}`, `{periodo?}`
- **Output**: Matriz provincia × partner con GMV
- **Complejidad**: Alta
- **Requiere**: Lookup a pharmacies para obtener provincia desde bookings

---

## 📝 PROCESO DE IMPLEMENTACIÓN

### Para cada query:

1. **Crear esquema hardcodeado**
   - Definir pipeline MongoDB optimizado
   - Definir variables de entrada
   - Definir formato de respuesta

2. **Probar con GPT**
   - Generar query con GPT usando el diccionario actual
   - Comparar pipeline GPT vs hardcoded
   - Calcular similitud (estructura, operadores, campos)

3. **Documentar diferencias**
   - ¿GPT usó campos incorrectos?
   - ¿GPT generó pipeline ineficiente?
   - ¿GPT entendió correctamente la intención?

4. **Mejorar diccionario si es necesario**
   - Añadir keywords faltantes
   - Añadir synonyms
   - Añadir aggregation_hints más específicos
   - Mejorar BUSINESS_CONTEXT

5. **Implementar en app_luda_mind.py**
   - Añadir detección de pattern
   - Implementar pipeline hardcodeado
   - Añadir validación de seguridad
   - Formatear respuesta

---

## 🎯 ORDEN DE IMPLEMENTACIÓN (PRIORIDAD)

### **FASE 1 - Queries Simples (Warmup)** ✅
1. Número de farmacias por provincia
2. Porcentaje de farmacias activas
3. Presencia de un producto

### **FASE 2 - Queries de Negocio Core**
4. Top farmacias con más ventas (general)
5. Top productos más vendidos
6. Métricas de venta de un producto en partners

### **FASE 3 - Queries de Partner**
7. Comparativa de partners (tabla completa)
8. Top farmacias con más cancelaciones por partner
9. Ventas por partners según provincia

### **FASE 4 - Queries Complejas de Farmacia**
10. Ventas en todos los partners de una farmacia
11. Porcentaje de cancelaciones de una farmacia
12. Métricas de shortage de una farmacia

### **FASE 5 - Queries Avanzadas de Producto**
13. Margen de un producto
14. Top catálogos más extensos
15. Obtener ean13 más repetido (CN ↔ EAN13)
16. Sell in y sell out (requiere definición de negocio)

---

## 📊 MÉTRICAS DE ÉXITO

| Métrica | Objetivo |
|---------|----------|
| Similitud GPT vs Hardcoded | > 80% |
| Tiempo de respuesta hardcoded | < 500ms |
| Tiempo de respuesta GPT | < 3s |
| Cobertura de diccionario | > 90% keywords |
| Tests E2E pasando | 100% |

---

## 🔧 TEMPLATES DE CÓDIGO

### Template de Query Predefinida en app_luda_mind.py:

```python
# =====================================================================
# QUERY PREDEFINIDA: [Nombre de la query]
# =====================================================================
if [condición_de_detección]:
    # Variables de entrada
    variable_1 = extraer_variable_1(query_lower)
    variable_2 = extraer_variable_2(query_lower)

    # Determinar período si aplica
    match_filter = {}
    period_text = "histórico"

    if 'semana' in query_lower:
        fecha_inicio = datetime.now() - timedelta(days=7)
        match_filter["createdDate"] = {"$gte": fecha_inicio}
        period_text = "últimos 7 días"

    # Pipeline optimizado
    pipeline = [
        {"$match": match_filter},
        # ... resto del pipeline
    ]

    # Validar seguridad
    is_safe, error_msg = validate_mongodb_pipeline(pipeline, "collection_name")
    if not is_safe:
        return {
            'answer': f"❌ Consulta bloqueada: {error_msg}",
            'database': 'mongodb',
            'confidence': 0.0
        }

    # Ejecutar
    results = list(mongo_db.collection_name.aggregate(pipeline))

    # Formatear respuesta
    if results:
        answer = f"📊 **[Título de Respuesta]** (Luda Mind)\n\n"
        answer += f"📅 **Período:** {period_text}\n\n"
        # ... formatear datos
        answer += "\n*Fuente: Luda Mind - MongoDB (query predefinida)*"

        return {
            'answer': answer,
            'database': 'mongodb',
            'confidence': 0.95
        }
```

### Template de Comparación GPT vs Hardcoded:

```python
"""
Script de comparación: [nombre_query].py

Compara el pipeline hardcodeado vs el generado por GPT
"""

# Query de prueba
query = "[pregunta en lenguaje natural]"

# 1. Pipeline hardcodeado
pipeline_hardcoded = [
    # ... pipeline optimizado
]

# 2. Pipeline GPT
from domain.services.query_interpreter import QueryInterpreter
interpreter = QueryInterpreter(openai_api_key=os.getenv('OPENAI_API_KEY'))
result_gpt = interpreter.interpret_query(query, mode="conversational")
pipeline_gpt = result_gpt.get('pipeline', [])

# 3. Comparar
print("HARDCODED:")
print(json.dumps(pipeline_hardcoded, indent=2))
print("\nGPT:")
print(json.dumps(pipeline_gpt, indent=2))

# 4. Analizar diferencias
# - ¿Misma colección?
# - ¿Mismos operadores?
# - ¿Mismos campos?
# - ¿Mismo orden de stages?
```

---

**Siguiente paso**: Empezar con FASE 1 - Query 1: "Número de farmacias por provincia"

