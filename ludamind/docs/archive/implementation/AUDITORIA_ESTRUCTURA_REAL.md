# 🔍 AUDITORÍA: Estructura REAL de MongoDB vs Diccionario Semántico

**Fecha:** 20 Noviembre 2024

---

## ⚠️ PROBLEMAS DETECTADOS EN EL DICCIONARIO SEMÁNTICO

### ❌ ERRORES CRÍTICOS ENCONTRADOS

#### 1. **PHARMACIES** - Campos Incorrectos

| Campo en Mapping | Estado | Campo Real Correcto |
|-----------------|--------|---------------------|
| `name` | ❌ NO EXISTE | `description` ✅ |
| `city` | ❌ NO EXISTE | `contact.city` ✅ |
| `address` | ❌ NO EXISTE | `contact.address` ✅ |
| `active` | ✅ CORRECTO | `active` ✅ |

**Estructura Real:**
```javascript
{
    _id: ObjectId,
    description: "FARMACIA ISABEL CELADA",  // ← Nombre de la farmacia
    active: 0 o 1,
    contact: {
        city: "Madrid",          // ← Ciudad
        address: "Calle...",     // ← Dirección
        street: "...",
        postalCode: "...",
        phone1: "...",
        email: "..."
    },
    ...
}
```

---

#### 2. **ITEMS** - Campos Incorrectos

| Campo en Mapping | Estado | Campo Real Correcto |
|-----------------|--------|---------------------|
| `name` | ❌ NO EXISTE | `description` o `pharmacyDescription` ✅ |
| `ean` | ❌ NO EXISTE | `ean13` ✅ |
| `price` | ❌ NO EXISTE | `pvp` (precio venta) o `pva` (precio compra) ✅ |
| `active` | ✅ CORRECTO | `active` ✅ |
| `category` | ❌ NO EXISTE | `categories` (array) o `family` ✅ |

**Estructura Real:**
```javascript
{
    _id: ObjectId,
    description: "INTERAPOTHEK PAÑUELOS BOLSILLO 6 UI",  // ← Nombre
    pharmacyDescription: "...",  // ← Descripción de farmacia
    ean13: "8427950600043",      // ← EAN
    active: 0 o 1,
    family: "P",                 // ← Familia/tipo
    categories: ["..."],         // ← Categorías (array)
    itemType: 3,
    parapharmacyGroup: "Z",
    // NO tiene campos: pvp, pva (solo en stockItems)
}
```

**⚠️ NOTA IMPORTANTE:** Los precios (pvp/pva) están en `stockItems`, NO en `items`!

---

#### 3. **BOOKINGS** - Verificar thirdUser

**El documento de muestra NO mostró `thirdUser`** en la estructura, pero las queries anteriores confirmaron que **SÍ existe** en 730,553 documentos.

**Posible explicación:** El documento de muestra (de 2018) no tenía thirdUser, pero los documentos más recientes sí.

**Verificación necesaria:** ✅ Confirmado que thirdUser.user existe en 730k docs

---

## ✅ ESTRUCTURA REAL CORRECTA

### 📦 BOOKINGS

```javascript
{
    _id: ObjectId,
    bookingId: "abc123",
    createdDate: ISODate,        // ✅ Fecha
    creator: "user_id",          // ID del creador
    origin: "pharmacy_id",       // Farmacia origen
    target: "pharmacy_id",       // Farmacia destino
    items: [                     // ✅ Array de productos
        {
            code: "123",
            description: "...",
            quantity: 2,
            pvp: 10.50,
            pva: 8.30,
            ...
        }
    ],
    state: "state_id",
    stateValue: "Finalizado",
    active: 0 o 1,
    
    // PARTNER INFO (solo en pedidos de terceros)
    thirdUser: {                 // ✅ Info del partner
        user: "glovo",           // ✅ Nombre del partner
        price: 25.50,            // ✅ GMV del pedido
        booking: "...",
        gift: false,
        ...
    },
    
    shipping: {...},
    deliveryData: {...}
}
```

---

### 🏥 PHARMACIES

```javascript
{
    _id: ObjectId,
    description: "FARMACIA NOMBRE",  // ← Nombre (NO "name")
    active: 0 o 1,                   // ✅ Estado
    
    contact: {                        // ← Info de contacto
        contactName: "...",
        address: "Calle X, 123",      // ← Dirección
        street: "Calle X",
        number: "123",
        city: "Madrid",               // ← Ciudad
        province: "Madrid",
        postalCode: "28001",
        phone1: "...",
        email: "...",
        geometry: {lat: ..., lng: ...}
    },
    
    cooperador: "15220",             // Código cooperador
    fiscalCode: "...",               // NIF
    erp: "FARMATIC",                 // Sistema ERP
    type: "Customer",
    connected: true/false,
    lastSeen: ISODate,
    ...
}
```

---

### 💊 ITEMS

```javascript
{
    _id: ObjectId,
    description: "PRODUCTO NOMBRE",        // ← Nombre (NO "name")
    pharmacyDescription: "...",
    ean13: "8427950600043",                // ← EAN (NO "ean")
    active: 0 o 1,                         // ✅ Estado
    family: "P",                           // Familia/tipo
    categories: ["cat1", "cat2"],          // ← Array (NO "category")
    parapharmacyGroup: "Z",
    itemType: 3,
    
    // NO tiene price aquí
    // Los precios están en stockItems (pvp, pva)
}
```

---

### 📦 STOCKITEMS

```javascript
{
    _id: "pharmacy_id-item_id",            // String compuesto
    pharmacyId: "5c41b4ea...",            // ← ID farmacia
    itemId: "5ab0d643...",                // ← ID item
    code: "384677",                       // Código producto
    quantity: 5,                          // ✅ Cantidad
    pvp: 14.0,                            // ← Precio venta (NO "price")
    pva: 9.81,                            // ← Precio compra
    match: "DESCRIPTION",
    eventId: "...",
    updatedDate: ISODate
}
```

---

## 🔧 CORRECCIONES NECESARIAS

### PRIORIDAD ALTA (Cambios críticos)

1. **Pharmacies:**
   ```python
   # INCORRECTO
   field_path="name"
   field_path="city"
   field_path="address"
   
   # CORRECTO
   field_path="description"        # Nombre de farmacia
   field_path="contact.city"       # Ciudad
   field_path="contact.address"    # Dirección
   ```

2. **Items:**
   ```python
   # INCORRECTO
   field_path="name"
   field_path="ean"
   field_path="price"
   field_path="category"
   
   # CORRECTO
   field_path="description"        # Nombre del producto
   field_path="ean13"              # Código EAN
   # price NO existe en items
   field_path="categories"         # Array de categorías
   field_path="family"             # Familia de producto
   ```

3. **StockItems - Precios:**
   ```python
   # CORRECTO
   field_path="quantity"           # Cantidad en stock
   field_path="pvp"                # Precio venta público
   field_path="pva"                # Precio venta almacén
   field_path="pharmacyId"         # ID farmacia (string)
   field_path="itemId"             # ID item (string)
   ```

---

## 🎯 OTROS HALLAZGOS IMPORTANTES

### Partners Adicionales Encontrados
Además de Glovo, Uber, Danone, hay:
- uber, glovo (confirmado)
- justeat
- carrefour (confirmado)
- amazon
- perfumesclub
- procter
- chiesi
- pierre-fabre
- trebol-miravia-lc
- trizgo-miravia
- rempe

### Campos Útiles No Mapeados

**En pharmacies:**
- `cooperador` - Código de cooperador (útil para agrupación)
- `erp` - Sistema ERP ("FARMATIC", etc.)
- `connected` - Si está conectado en tiempo real
- `lastSeen` - Última vez vista (útil para "actividad reciente")
- `fiscalCode` - NIF de la farmacia

**En items:**
- `family` - Familia de producto (P, M, etc.)
- `parapharmacyGroup` - Grupo de parafarmacia
- `itemType` - Tipo de item (número)
- `categories` - Array de categorías

**En stockItems:**
- `pvp` - Precio venta público
- `pva` - Precio venta almacén
- `code` - Código nacional del producto

---

## ⚠️ ACCIÓN REQUERIDA

**NECESITAMOS CORREGIR EL DICCIONARIO SEMÁNTICO CON LOS CAMPOS REALES:**

1. ✅ Confirmar qué campos usar para cada concepto
2. ✅ Actualizar semantic_mapping.py con estructura real
3. ✅ Revisar lógica de negocio de cada campo
4. ✅ Añadir campos útiles que no estaban mapeados

---

## 📋 PREGUNTAS PARA VALIDAR LÓGICA DE NEGOCIO

### Partners:
1. ✅ **thirdUser.user** es correcto para partner
2. ✅ **thirdUser.price** es correcto para GMV
3. ❓ ¿Hay diferencia entre thirdUser.price y items[].pvp?

### Farmacias:
1. ❓ **description** es el nombre correcto de farmacia?
2. ❓ **contact.city** es correcto para ciudad?
3. ❓ **active** = 0 significa inactiva, = 1 activa?
4. ❓ **cooperador** es un campo importante para consultas?

### Productos:
1. ❓ **description** vs **pharmacyDescription** - ¿cuál es mejor?
2. ✅ **ean13** es el código de barras correcto
3. ❓ ¿Los precios solo están en stockItems, no en items?
4. ❓ **family** vs **categories** - ¿cuál es más útil para agrupar?

### Stock:
1. ✅ **quantity** es correcto
2. ❓ **pvp** vs **pva** - ¿cuál usar para "precio"?
3. ❓ **pharmacyId** y **itemId** son strings, no ObjectIds

---

*Auditoría completada - Requiere revisión y corrección del mapping*
*Luda Mind v4.2.0*
