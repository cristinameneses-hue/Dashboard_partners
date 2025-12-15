# 📚 DICCIONARIO SEMÁNTICO FINAL - LUDA MIND

**Versión:** 4.3.0  
**Fecha:** 20 Noviembre 2024  
**Estado:** ✅ VALIDADO Y CORREGIDO

---

## ✅ ESTRUCTURA VALIDADA CON MONGODB REAL

### 🏥 FARMACIAS (pharmacies)

```python
{
    "_id": ObjectId,                    # ID único (ObjectId)
    "description": "FARMACIA ISABEL",   # Nombre comercial
    "active": 1,                        # 1=activa, 0=inactiva
    "contact": {
        "city": "Madrid",               # Ciudad
        "postalCode": "28010",          # Código postal
        "address": "Calle X, 123",      # Dirección completa
        "province": "Madrid",
        "phone1": "...",
        "email": "..."
    }
}
```

**Búsqueda:**
- ID sin sentido → `_id` (ObjectId)
- Nombre legible → `description` (regex case-insensitive)
- No encuentra → pedir ID

**Para relacionar:** pharmacies._id (ObjectId) = bookings.target (string convertido)

---

### 💊 PRODUCTOS (items)

```python
{
    "_id": ObjectId,                           # NO usar para búsquedas usuario
    "description": "NATALBEN SUPRA 30 CAPS",  # Nombre del producto
    "code": "154653",                          # Código nacional (6 dígitos, STRING)
    "ean13": "8470001546531",                  # EAN (13 dígitos, STRING)
    "active": 1,                               # 1=activo, 0=inactivo
    "itemType": 3,                             # 3=Parafarmacia, otro=Medicamento
    "pharmacyDescription": "..."               # Descripción alternativa
}
```

**Claves Primarias:** `code` y `ean13` (NO `_id`)

**Identificación:**
1. Texto libre ("ozempic") → `description` regex /ozempic/i
2. 6 dígitos ("154653") → `code` (STRING)
3. 13 dígitos ("8470001546531") → `ean13` (STRING)

**Múltiples resultados:** Mostrar lista con description + code, pedir elección

**⚠️ PRECIOS:** NO están en items, están en stockItems

---

### 📦 STOCK (stockItems)

```python
{
    "_id": "pharmacy_id-item_id",             # String compuesto
    "pharmacyId": "5c41b4ea...",              # ID farmacia (STRING)
    "itemId": "5ab0d643...",                  # ID item (STRING)
    "code": "154653",                         # Código nacional
    "quantity": 2,                            # Cantidad en stock
    "pvp": 20.00,                             # Precio Venta Público
    "pva": 14.48,                             # Precio Venta Almacén
    "updatedDate": ISODate
}
```

**Precios:**
- Default: **moda** (valor más frecuente) de `pvp`
- Si especifica: min, max, avg
- PVP = público (cliente), PVA = almacén (farmacia)

**Relación:**
- items._id (ObjectId) → str() → stockItems.itemId (string)
- pharmacies._id (ObjectId) → str() → stockItems.pharmacyId (string)

---

### 🤝 PARTNERS (bookings con thirdUser)

```python
{
    "_id": ObjectId,
    "bookingId": "abc123",
    "createdDate": ISODate("2025-11-20"),
    "target": "pharmacy_id",                  # Farmacia destino
    
    "thirdUser": {                            # Info del partner
        "user": "glovo",                      # = thirdUsers.idUser
        "price": 48.70,                       # GMV (si existe)
        "booking": "ref...",
        "provider": {...}
    },
    
    "items": [                                # Productos del pedido
        {
            "description": "NATALBEN SUPRA...",
            "code": "154653",
            "ean13": "8470001546531",
            "pvp": 20.10,
            "quantity": 1
        }
    ]
}
```

**GMV Calculation:**
```python
if thirdUser.price exists:
    gmv = thirdUser.price
else:
    gmv = sum(item.pvp * item.quantity for item in items)
```

**12 Partners Activos:**
- **Delivery:** glovo, glovo-otc, uber, justeat, carrefour, amazon
- **Labs:** danone, procter, enna, nordic, chiesi, ferrer

---

### 🔄 SHORTAGES (transferencias internas)

```python
{
    "_id": ObjectId,
    "bookingId": "xyz789",
    "createdDate": ISODate,
    "origin": "pharmacy_id_origen",           # Farmacia origen
    "target": "pharmacy_id_destino",          # Farmacia destino
    
    # NO tiene thirdUser (es interno)
    
    "items": [                                # Productos transferidos
        {
            "pvp": 20.10,
            "quantity": 1
        }
    ]
}
```

**Detectar Shortage:** `origin` exists

**GMV Shortage:** `sum(items[].pvp * items[].quantity)`

**Separar en reportes:**
- GMV Ecommerce (con thirdUser)
- GMV Shortage (con origin)

---

## 🧮 REGLAS DE CÁLCULO

### GMV Total
```
GMV Total Esta Semana:
┌─────────────────────────┐
│ GMV Ecommerce: €103,905 │ (partners)
│ GMV Shortage:  €77,649  │ (transferencias)
│ ────────────────────────│
│ TOTAL:         €181,554 │
└─────────────────────────┘
```

### Precio de Producto
```
1. Buscar en items (por code/ean13/description)
2. Obtener items._id → convertir a string
3. Buscar en stockItems where itemId = str(items._id)
4. Obtener lista de pvp (uno por farmacia)
5. Calcular:
   - Default: moda (más común)
   - "más barato": min
   - "más caro": max
   - "promedio": avg
```

---

## 🔍 BÚSQUEDAS

### Farmacias
```python
# Por nombre
{"description": {"$regex": "isabel", "$options": "i"}}

# Por ciudad
{"contact.city": "Madrid", "active": 1}

# Por código postal
{"contact.postalCode": "28010"}

# Por ID
{"_id": ObjectId("5a30f602...")}
```

### Productos
```python
# Por descripción (fuzzy)
{"description": {"$regex": "ozempic", "$options": "i"}}

# Por código nacional (6 dígitos)
{"code": "154653"}  # STRING

# Por EAN (13 dígitos)
{"ean13": "8470001546531"}  # STRING

# Solo parafarmacia
{"itemType": 3, "active": 1}
```

### Partners
```python
# Pedidos de Glovo
{"thirdUser.user": "glovo"}

# Con regex (case-insensitive)
{"thirdUser.user": {"$regex": "glovo", "$options": "i"}}

# Pedidos de farmacia por partner
{"target": "pharmacy_id", "thirdUser.user": "uber"}
```

### Shortages
```python
# Todos los shortages
{"origin": {"$exists": True}}

# Shortages esta semana
{
    "origin": {"$exists": True},
    "createdDate": {"$gte": ISODate("2025-11-13")}
}
```

---

## 📊 ESTADÍSTICAS VALIDADAS

### Esta Semana (últimos 7 días):

**Ecommerce:**
- Glovo: 3,412 pedidos | €73,036
- Uber: 1,020 pedidos | €25,322
- Glovo-OTC: 414 pedidos
- JustEat: 86 pedidos | €2,083
- Carrefour: 70 pedidos | €2,787
- Otros: 43 pedidos

**Shortage:**
- 2,074 transferencias | €77,649

**Total Sistema:**
- 7,119 bookings | €181,554

---

## ✅ VALIDACIONES

- ✅ Estructura auditada contra MongoDB real
- ✅ Partners verificados en thirdUsers.idUser
- ✅ Campos corregidos con nombres reales
- ✅ Lógica de negocio confirmada
- ✅ GMV calculation robusta
- ✅ Shortages identificados
- ✅ Múltiples métodos de búsqueda
- ✅ Precios en stockItems verificados
- ✅ Relaciones entre colecciones validadas

---

## 🚀 PRÓXIMO PASO

Implementar en `app_luda_mind.py`:
1. ✅ Campos corregidos
2. ✅ GMV dual (price o items)
3. ✅ Separación shortage/ecommerce
4. ✅ Búsqueda multi-criterio productos
5. ✅ Precios desde stockItems
6. ✅ Solo 12 partners activos

---

**Diccionario semántico 100% validado con lógica de negocio real. 💚**

---

*Luda Mind v4.3.0 - Final Validated Semantic Dictionary*
