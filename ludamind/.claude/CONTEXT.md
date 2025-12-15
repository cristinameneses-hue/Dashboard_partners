# Luda Mind - Contexto de Queries para IA

> **Archivo maestro de contexto semántico para generación de queries MongoDB/MySQL**
> Basado en: `domain/knowledge/semantic_mapping.py`
> Última actualización: 2025-12-11

---

## 1. Partners / Canales de Venta

### Campo Principal
```
bookings.thirdUser.user → Identificador del partner (string)
```

### Partners Activos (12 verificados)

| Partner | Tipo | Notas |
|---------|------|-------|
| `glovo` | Delivery | Mayor volumen |
| `glovo-otc` | Delivery | Glovo OTC |
| `uber` | Delivery | Segundo mayor |
| `justeat` | Delivery | JustEat |
| `amazon` | Marketplace | Amazon |
| `carrefour` | Retail | Carrefour |
| `danone` | Lab corporativo | Danone |
| `procter` | Lab corporativo | Procter & Gamble |
| `enna` | Lab corporativo | Enna |
| `nordic` | Lab corporativo | Nordic |
| `chiesi` | Lab corporativo | Chiesi |
| `ferrer` | Lab corporativo | Ferrer |

### GMV (Gross Merchandise Value)

**Cálculo de GMV:**
```javascript
// SIEMPRE calcular desde items
GMV = sum(items[].pvp * items[].quantity)

// Pipeline MongoDB:
{
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
```

**Campo alternativo (legacy):**
```
bookings.thirdUser.price → Precio/GMV del pedido (si existe)
```

---

## 2. Farmacias

### Campos Principales

| Campo | Colección | Descripción |
|-------|-----------|-------------|
| `_id` | pharmacies | ObjectId único |
| `description` | pharmacies | **Nombre comercial** (NO usar `name`) |
| `contact.city` | pharmacies | Ciudad |
| `contact.province` | pharmacies | Provincia |
| `contact.postalCode` | pharmacies | Código postal |
| `active` | pharmacies | 1=activa, 0=inactiva |
| `tags` | pharmacies | Array de partners activos |

### Identificación de Farmacias

```javascript
// Por ID (ObjectId)
db.pharmacies.findOne({_id: ObjectId("5a30f602c495ec99da3b2d77")})

// Por nombre (regex case-insensitive)
db.pharmacies.find({description: {$regex: "FARMACIA ISABEL", $options: "i"}})
```

### Farmacias Activas en Partners

**Partners CON tags (usar pharmacies.tags):**
```javascript
// Glovo (sin sufijo)
{tags: "GLOVO"}

// Otros partners (con sufijos _2H, _48H)
{tags: {$in: ["AMAZON_2H", "AMAZON_48H"]}}
{tags: {$in: ["CARREFOUR_2H", "CARREFOUR_48H"]}}
{tags: {$in: ["DANONE_2H", "DANONE_48H"]}}
{tags: {$in: ["PROCTER_2H", "PROCTER_48H"]}}
// etc.
```

**Partners SIN tags (Uber, Justeat):**
```javascript
// Buscar farmacias con pedidos del partner
db.bookings.aggregate([
  {$match: {"thirdUser.user": "uber", createdDate: {$gte: fecha}}},
  {$group: {_id: "$target"}}
])
```

---

## 3. Pedidos (Bookings)

### Campos Principales

| Campo | Descripción |
|-------|-------------|
| `_id` | ObjectId del pedido |
| `createdDate` | **Fecha del pedido** (NO usar createdAt) |
| `target` | ID farmacia destino (string) |
| `origin` | ID farmacia origen (si existe = shortage) |
| `state` | ID del estado |
| `items[]` | Array de productos |
| `thirdUser.user` | Partner (si es ecommerce) |
| `thirdUser.price` | GMV legacy del partner |

### Tipos de Bookings

1. **Pedidos de Partners (ecommerce):**
   - Tienen `thirdUser.user`
   - GMV = sum(items[].pvp * items[].quantity)

2. **Shortages (transferencias internas):**
   - Tienen `origin` (farmacia origen)
   - NO tienen `thirdUser`
   - Son movimientos entre farmacias

### Estados de Pedidos

```javascript
// Estado cancelado
"5a54c525b2948c860f00000d"

// Excluir cancelados
{state: {$ne: "5a54c525b2948c860f00000d"}}
```

### Relación Booking → Farmacia

```javascript
// El campo target es STRING, necesita conversión
{"$lookup": {
  "from": "pharmacies",
  "let": {"target_id": {"$toObjectId": "$target"}},
  "pipeline": [
    {"$match": {"$expr": {"$eq": ["$_id", "$$target_id"]}}},
    {"$project": {"description": 1, "contact.province": 1}}
  ],
  "as": "pharmacy_info"
}}
```

---

## 4. Productos

### Campos Principales

| Campo | Colección | Descripción |
|-------|-----------|-------------|
| `_id` | items | ObjectId |
| `description` | items | Nombre del producto |
| `code` | items | Código nacional (6 dígitos, STRING) |
| `ean13` | items | Código EAN (13 dígitos, STRING) |
| `active` | items | 1=activo, 0=inactivo |
| `itemType` | items | 3=Parafarmacia, otro=Medicamento |

### Búsqueda de Productos

```javascript
// Por nombre (regex)
{description: {$regex: "ozempic", $options: "i"}}

// Por código nacional (6 dígitos)
{code: "154653"}

// Por EAN (13 dígitos)
{ean13: "8470001546531"}
```

---

## 5. Stock / Inventario

### Campos Principales (stockItems)

| Campo | Descripción |
|-------|-------------|
| `pharmacyId` | ID farmacia (STRING) |
| `itemId` | ID producto (STRING) |
| `quantity` | Cantidad en stock |
| `pvp` | Precio Venta Público |
| `pva` | Precio Venta Almacén |

---

## 6. Patrones de Agregación Comunes

### Top Farmacias por Partner

```javascript
[
  {"$match": {"thirdUser.user": "glovo"}},
  {"$lookup": {
    "from": "pharmacies",
    "let": {"target_id": {"$toObjectId": "$target"}},
    "pipeline": [
      {"$match": {"$expr": {"$eq": ["$_id", "$$target_id"]}}},
      {"$project": {"description": 1, "contact.province": 1, "contact.city": 1}}
    ],
    "as": "pharmacy_info"
  }},
  {"$unwind": {"path": "$pharmacy_info", "preserveNullAndEmptyArrays": false}},
  {"$match": {"pharmacy_info.contact.province": "Barcelona"}}, // Opcional
  {"$group": {
    "_id": "$target",
    "pharmacy_name": {"$first": "$pharmacy_info.description"},
    "num_pedidos": {"$sum": 1},
    "gmv_total": {
      "$sum": {
        "$reduce": {
          "input": "$items",
          "initialValue": 0,
          "in": {"$add": ["$$value", {"$multiply": [
            {"$toDouble": {"$ifNull": ["$$this.pvp", 0]}},
            {"$toInt": {"$ifNull": ["$$this.quantity", 0]}}
          ]}]}
        }
      }
    }
  }},
  {"$sort": {"gmv_total": -1}},
  {"$limit": 20}
]
```

### Conteo por Campo

```javascript
[
  {"$group": {"_id": "$CAMPO", "count": {"$sum": 1}}},
  {"$sort": {"count": -1}}
]
```

### Filtro Temporal

```javascript
// Hoy
{createdDate: {$gte: new Date().setHours(0,0,0,0)}}

// Esta semana (últimos 7 días)
{createdDate: {$gte: new Date(Date.now() - 7*24*60*60*1000)}}

// Este mes (últimos 30 días)
{createdDate: {$gte: new Date(Date.now() - 30*24*60*60*1000)}}
```

---

## 7. Provincias de España (Mapeo)

```javascript
const provincias_map = {
  'barcelona': 'Barcelona',
  'madrid': 'Madrid',
  'valencia': 'Valencia',
  'sevilla': 'Sevilla',
  'málaga': 'Málaga',
  'malaga': 'Málaga',
  'alicante': 'Alicante',
  'murcia': 'Murcia',
  'zaragoza': 'Zaragoza',
  'bilbao': 'Vizcaya',
  'vizcaya': 'Vizcaya',
  'granada': 'Granada',
  'córdoba': 'Córdoba',
  'cordoba': 'Córdoba',
  'valladolid': 'Valladolid',
  'mallorca': 'Illes Balears',
  'las palmas': 'Las Palmas',
  'tenerife': 'Santa Cruz de Tenerife',
  'asturias': 'Asturias',
  'cantabria': 'Cantabria',
  'navarra': 'Navarra',
  'la rioja': 'La Rioja',
  'castellón': 'Castellón',
  'toledo': 'Toledo',
  'cádiz': 'Cádiz',
  'huelva': 'Huelva',
  'almería': 'Almería',
  'jaén': 'Jaén'
};
```

---

## 8. Routing MySQL vs MongoDB

### Usar MySQL cuando:
- ventas, sales, sold, vendidos
- trends, tendencias, demanda
- cazador, hunter, oportunidades
- Z_Y, z-score, riesgo, risk group
- analytics, predicción, histórico
- bookings_agrupado

### Usar MongoDB cuando:
- farmacia, pharmacy
- usuario, user
- booking, reserva, pedido actual
- catálogo, producto actual
- stock actual, inventario
- partner, glovo, uber, danone, etc.
- GMV por partner

### Default: MongoDB

---

## 9. Reglas Importantes

1. **Nombre de farmacia:** Usar `description`, NO `name`
2. **Fecha de pedido:** Usar `createdDate`, NO `createdAt`
3. **ID farmacia en booking:** Campo `target` (string → ObjectId)
4. **Partner:** Campo `thirdUser.user` (NO `creator`)
5. **GMV:** Calcular desde `items[].pvp * items[].quantity`
6. **Provincias:** Case-sensitive en MongoDB

---

## 10. Archivo Fuente

El contexto técnico completo está en:
```
domain/knowledge/semantic_mapping.py
```

Este archivo contiene:
- `SEMANTIC_MAPPINGS`: Diccionario de campos con keywords y ejemplos
- `BUSINESS_CONTEXT`: Contexto de negocio por área
- `AGGREGATION_PATTERNS`: Patrones de agregación comunes
- `build_context_for_llm()`: Función que construye contexto para GPT
