# 🧠 SISTEMA DE MAPEO SEMÁNTICO - LUDA MIND

**Versión:** 4.2.0  
**Fecha:** 20 Noviembre 2024

---

## 🎯 OBJETIVO

Mejorar la capacidad del sistema para **interpretar queries no predefinidas** mediante:

1. **Diccionario semántico** que mapea palabras clave → campos de BD
2. **Contexto de negocio** que explica qué significa cada campo
3. **GPT guiado** que usa este contexto para generar queries dinámicas

---

## 🏗️ ARQUITECTURA

```
Usuario Query
     ↓
[Semantic Mapping]  ← Diccionario de palabras clave → campos
     ↓
[Query Interpreter] ← GPT con contexto enriquecido
     ↓
[MongoDB Query]     ← Agregación generada dinámicamente
     ↓
[Formatted Answer]  ← Respuesta en lenguaje natural
```

---

## 📚 COMPONENTES IMPLEMENTADOS

### 1. **Semantic Mapping** (`domain/knowledge/semantic_mapping.py`)

#### FieldMapping
Estructura que describe cada campo de MongoDB:

```python
@dataclass
class FieldMapping:
    field_path: str          # "thirdUser.user"
    collection: str          # "bookings"
    data_type: str          # "string", "number", "date"
    description: str        # Descripción de negocio
    keywords: List[str]     # Palabras clave relacionadas
    synonyms: List[str]     # Sinónimos
    examples: List[str]     # Ejemplos de valores
    aggregation_hints: List[str]  # Cómo agregar este campo
```

#### Campos Mapeados (15+ campos)
- ✅ **Partners:** thirdUser.user, thirdUser.price
- ✅ **Farmacias:** _id, name, city, active
- ✅ **Bookings:** createdDate, state, items
- ✅ **Productos:** name, ean, price, active, category
- ✅ **Stock:** quantity
- ✅ **Métricas:** ticket_medio, total, conteo

#### Ejemplo de Mapping
```python
"partner": FieldMapping(
    field_path="thirdUser.user",
    collection="bookings",
    description="Partner o canal de venta (Glovo, Uber, etc.)",
    keywords=["partner", "canal", "marketplace", "plataforma"],
    synonyms=["glovo", "uber", "danone"],
    examples=["glovo", "uber"],
    aggregation_hints=["$group by thirdUser.user"]
)
```

---

### 2. **Business Context** (Contexto de Negocio)

Describe qué representa cada entidad en el negocio:

```python
BUSINESS_CONTEXT = {
    "partners": """
    Los partners son canales de distribución terceros.
    Principales: Glovo (mayor volumen), Uber, Danone...
    Campo clave: 'thirdUser.user' en 'bookings'
    GMV en: 'thirdUser.price'
    """,
    
    "pharmacies": """
    Establecimientos que procesan pedidos.
    Campos: name, city, active
    Para rendimiento: relacionar con bookings
    """,
    ...
}
```

---

### 3. **Aggregation Patterns** (Patrones Comunes)

Plantillas de agregaciones MongoDB frecuentes:

```python
AGGREGATION_PATTERNS = {
    "count_by_field": {
        "description": "Contar documentos agrupados",
        "pattern": [
            {"$group": {"_id": "$FIELD", "count": {"$sum": 1}}},
            {"$sort": {"count": -1}}
        ],
        "keywords": ["cuántos", "cantidad", "número"]
    },
    
    "top_n": {
        "description": "Top N resultados",
        "pattern": [
            {"$sort": {"FIELD": -1}},
            {"$limit": 10}
        ],
        "keywords": ["top", "mejores", "principales"]
    },
    ...
}
```

---

### 4. **Query Interpreter** (`domain/services/query_interpreter.py`)

Usa GPT con el contexto semántico para interpretar queries:

#### Flujo:
1. **Detecta campos relevantes** usando el diccionario semántico
2. **Construye contexto rico** con descripciones de negocio
3. **Llama a GPT** con prompt estructurado
4. **Parsea respuesta** a formato ejecutable
5. **Fallback** a lógica básica si GPT no disponible

#### Prompt Engineering:
```python
system_prompt = f"""
Eres un experto en MongoDB para Luda Mind.

Modo: {mode}

Contexto de Negocio:
{business_context}

Campos Relevantes:
{semantic_mappings}

Tarea: Convertir query en agregación MongoDB.
"""
```

---

### 5. **Smart Query Processor** (`domain/services/smart_query_processor.py`)

Orquesta todo el proceso:
- Usa el interpreter
- Ejecuta en MongoDB
- Formatea respuesta
- Maneja errores

---

## 🎯 BENEFICIOS

### ✅ Ventajas sobre Hardcoding

| Aspecto | Hardcoding | Mapeo Semántico |
|---------|-----------|-----------------|
| **Escalabilidad** | ❌ Cada query nueva = código nuevo | ✅ Añadir keywords al mapping |
| **Flexibilidad** | ❌ Variaciones requieren casos | ✅ Maneja variaciones naturalmente |
| **Mantenibilidad** | ❌ Código disperso | ✅ Centralizado en mappings |
| **Aprendizaje** | ❌ No aprende | ✅ GPT mejora con contexto |
| **Cobertura** | ❌ Solo queries previstas | ✅ Cualquier combinación |

### 💡 Ejemplos de Mejora

#### Query: "Cuántas boticas hay en Valencia"

**Antes (Hardcoding):**
- ❌ No detecta "boticas" (solo "farmacias")
- ❌ Cae en respuesta genérica

**Ahora (Mapeo Semántico):**
- ✅ "boticas" está en synonyms de pharmacy
- ✅ "Valencia" detecta city field
- ✅ "cuántas" detecta intent=count
- ✅ Genera query: `db.pharmacies.count_documents({city: "Valencia"})`

#### Query: "Qué marketplace genera más ingresos"

**Antes:**
- ❌ "marketplace" no reconocido
- ❌ "ingresos" no mapeado a GMV

**Ahora:**
- ✅ "marketplace" en keywords de partner
- ✅ "ingresos" en synonyms de GMV
- ✅ "más" detecta $sort descendente
- ✅ Genera ranking de partners por GMV

---

## 🔧 CÓMO FUNCIONA

### Ejemplo Completo

```python
Query: "Pedidos de Glovo en Barcelona esta semana"

1. Semantic Mapping detecta:
   - "pedidos" → collection: bookings
   - "Glovo" → thirdUser.user
   - "Barcelona" → pharmacy.city
   - "esta semana" → createdDate >= 7 days ago

2. Query Interpreter (GPT) recibe:
   """
   Campos relevantes:
   - thirdUser.user (partner): Glovo, Uber, etc.
   - createdDate (fecha): para filtro temporal
   
   Contexto: Partners son canales de venta...
   
   Pattern sugerido: time_range + filter
   """

3. GPT genera:
   {
       "collection": "bookings",
       "pipeline": [
           {"$match": {
               "thirdUser.user": {"$regex": "glovo", "$options": "i"},
               "createdDate": {"$gte": "2024-11-13"},
               "pharmacy.city": "Barcelona"
           }},
           {"$count": "total"}
       ]
   }

4. MongoDB ejecuta → Resultado: 45 pedidos

5. Respuesta formateada:
   "📊 Glovo ha generado 45 pedidos en Barcelona esta semana"
```

---

## 📊 MAPPINGS ACTUALES

### Cobertura
- ✅ **15+ campos principales** mapeados
- ✅ **100+ keywords** reconocidas
- ✅ **50+ synonyms** de términos de negocio
- ✅ **5 patterns** de agregación comunes

### Colecciones
- ✅ bookings (pedidos/partners)
- ✅ pharmacies (farmacias)
- ✅ items (productos)
- ✅ stockItems (inventario)

---

## 🚀 INTEGRACIÓN

### Uso en la API

```python
from domain.services.smart_query_processor import SmartQueryProcessor

# Inicializar
processor = SmartQueryProcessor(mongo_db, openai_api_key)

# Procesar query no predefinida
result = processor.process(
    query="Cuántos pedidos tuvo Uber ayer en Madrid",
    mode="partner"
)

# result contiene respuesta formateada y metadata
```

### Fallback Inteligente

Si GPT no está disponible:
- ✅ Usa mappings para detección básica
- ✅ Aplica patterns comunes
- ✅ Genera respuesta útil aunque menos precisa

---

## 📈 EXTENSIBILIDAD

### Añadir Nuevos Campos (Fácil)
```python
SEMANTIC_MAPPINGS["nuevo_campo"] = FieldMapping(
    field_path="nuevo.campo",
    collection="collection",
    keywords=["palabra1", "palabra2"],
    ...
)
```

### Añadir Nuevos Patterns
```python
AGGREGATION_PATTERNS["nuevo_pattern"] = {
    "description": "...",
    "pattern": [...],
    "keywords": [...]
}
```

### Enriquecer Contexto
```python
BUSINESS_CONTEXT["nuevo_dominio"] = """
Descripción del dominio...
"""
```

---

## 🧪 TESTING

### Test del Sistema
```bash
python domain/services/query_interpreter.py
```

Prueba queries como:
- "Cuántas boticas hay en Valencia"
- "Qué marketplace genera más ingresos"
- "Pedidos de ayer por canal"
- "Farmacias con mayor actividad"

---

## 💡 PRÓXIMOS PASOS

### Fase 1 (Implementado) ✅
- ✅ Diccionario semántico completo
- ✅ Query Interpreter con GPT
- ✅ Smart Query Processor
- ✅ Mappings de 15+ campos

### Fase 2 (Recomendado)
- 🔄 Integrar en API principal
- 🔄 Añadir modo "smart" para queries complejas
- 🔄 Logging de queries interpretadas
- 🔄 Feedback loop para mejorar mappings

### Fase 3 (Futuro)
- 📊 Analytics de queries más frecuentes
- 🎓 Fine-tuning del modelo con datos históricos
- 🔍 Sugerencias proactivas al usuario
- 📈 Dashboard de queries interpretadas

---

## ✅ ESTADO ACTUAL

**SISTEMA COMPLETO E IMPLEMENTADO**

- ✅ Mapeo semántico de 15+ campos
- ✅ Contexto de negocio documentado
- ✅ Query Interpreter con GPT
- ✅ Smart Query Processor orquestador
- ✅ Patterns de agregación comunes
- ✅ Fallback sin GPT funcional
- ✅ Extensible y mantenible

**El sistema ahora puede interpretar queries flexibles y adaptarse al lenguaje natural del usuario. 🧠💚**

---

## 📝 EJEMPLO DE MEJORA

### Query: "Entregas de hoy de la app verde"

**Interpretación automática:**
1. "Entregas" → pedidos/bookings
2. "hoy" → createdDate >= today 00:00
3. "app verde" → Glovo (es verde en la app)
4. Intent: count

**Query generada:**
```javascript
db.bookings.count_documents({
    "thirdUser.user": /glovo/i,
    "createdDate": {$gte: today}
})
```

**Respuesta:** "📊 Glovo ha realizado 487 entregas hoy"

**¡Sin necesidad de hardcodear esta query específica!**

---

*Sistema de Mapeo Semántico implementado el 20/11/2024*  
*Luda Mind v4.2.0 - Intelligent Query Interpretation*
