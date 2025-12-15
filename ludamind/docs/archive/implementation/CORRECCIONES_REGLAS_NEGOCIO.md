# 🔧 CORRECCIONES REGLAS DE NEGOCIO

**Fecha**: 2025-11-27  
**Tipo**: Actualización de estándares

---

## ✅ **CORRECCIONES APLICADAS**

### 1️⃣ **CAMPO DE FECHA EN BOOKINGS**

#### ❌ INCORRECTO (Análisis previo):
```markdown
GPT usa `createdDate` → ERROR  
Debería usar `createdAt`
```

#### ✅ CORRECTO:
```markdown
GPT usa `createdDate` → CORRECTO ✅
El campo real en MongoDB es `createdDate`
```

**Evidencia**:
```javascript
// Verificado en MongoDB
db.bookings.findOne({}, {createdDate: 1})
// → { "_id": ..., "createdDate": ISODate("2024-11-20T...") }
```

**Actualización**:
- ✅ Diccionario semántico ya tenía `createdDate` correcto
- ✅ Prompt de GPT corregido para enfatizar uso de `createdDate`

---

### 2️⃣ **CÁLCULO ESTÁNDAR DE GMV**

#### ❌ INCORRECTO (Implementación previa):
```javascript
// Cálculo híbrido (DEPRECADO)
"totalGMV": {
  "$sum": {
    "$cond": {
      "if": {"$gt": ["$thirdUser.price", null]},
      "then": "$thirdUser.price",  // ← Usar si existe
      "else": {
        "$sum": {
          "$map": {
            "input": "$items",
            "as": "item",
            "in": {"$multiply": ["$$item.pvp", "$$item.quantity"]}
          }
        }
      }
    }
  }
}
```

**Problema**: Inconsistencia. Algunos bookings con `thirdUser.price`, otros sin él.

#### ✅ CORRECTO (Nuevo estándar):
```javascript
// Cálculo estándar SIEMPRE desde items
"totalGMV": {
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

**O con $map + $sum**:
```javascript
"totalGMV": {
  "$sum": {
    "$map": {
      "input": "$items",
      "as": "item",
      "in": {
        "$multiply": [
          {"$toDouble": {"$ifNull": ["$$item.pvp", 0]}},
          {"$toInt": {"$ifNull": ["$$item.quantity", 0]}}
        ]
      }
    }
  }
}
```

**Beneficios**:
- ✅ **Consistencia**: Todos los pedidos se calculan igual
- ✅ **Transparencia**: Siempre basado en precios de productos
- ✅ **Trazabilidad**: Se puede ver detalle item por item
- ✅ **Precisión**: Evita discrepancias entre `thirdUser.price` e items

---

## 📋 **IMPACTO EN EL CÓDIGO**

### Archivos Actualizados:

1. ✅ **`domain/knowledge/semantic_mapping.py`**
   - Actualizada regla GMV en `BUSINESS_CONTEXT['bookings']`
   - Añadido ejemplo de pipeline con cálculo estándar
   - Enfatizado uso de `createdDate`

2. ✅ **`domain/services/query_interpreter.py`**
   - Actualizado prompt para GPT
   - Añadidas instrucciones explícitas para cálculo GMV estándar
   - Ejemplos de pipeline con $reduce

3. ⏳ **`presentation/api/app_luda_mind.py`** (Pendiente)
   - 11 lugares donde se usa `thirdUser.price`
   - Necesitan actualizarse a cálculo estándar

---

## 🎯 **PRÓXIMOS PASOS**

### 1️⃣ **Actualizar `app_luda_mind.py`** (Alta prioridad)

Reemplazar todos los cálculos híbridos en:
- `process_partner_query()` (líneas ~734, 835, 904, 976, 1077)
- `process_pharmacy_query()` (líneas similares)
- Cualquier otra función que calcule GMV

### 2️⃣ **Testing E2E**

Verificar que las queries existentes siguen funcionando:
- "GMV de Glovo"
- "Top 10 farmacias en Glovo"
- "Pedidos totales por partner"

### 3️⃣ **Actualizar Documentación**

- ✅ ANALISIS_PREGUNTAS_PREDEFINIDAS_RESUMEN.md (ya incluye las correcciones)
- ⏳ Ejemplos de uso de API
- ⏳ Guías de desarrollo

---

## 📊 **VALIDACIÓN**

### Test Manual Recomendado:

```bash
# 1. Verificar campo de fecha en bookings
mongo LudaFarma-PRO --eval "db.bookings.findOne({}, {createdDate: 1, createdAt: 1})"

# 2. Comparar GMV calculado vs thirdUser.price
mongo LudaFarma-PRO --eval '
db.bookings.aggregate([
  {$match: {thirdUser: {$exists: true}}},
  {$limit: 10},
  {$addFields: {
    gmv_from_items: {
      $reduce: {
        input: "$items",
        initialValue: 0,
        in: {
          $add: [
            "$$value",
            {$multiply: ["$$this.pvp", "$$this.quantity"]}
          ]
        }
      }
    },
    gmv_from_third: "$thirdUser.price"
  }},
  {$project: {
    _id: 1,
    gmv_from_items: 1,
    gmv_from_third: 1,
    diferencia: {$subtract: ["$gmv_from_items", "$gmv_from_third"]}
  }}
])
'
```

---

## ✅ **CHECKLIST DE CORRECCIONES**

- [x] Diccionario semántico actualizado
- [x] Prompt de GPT actualizado
- [ ] `app_luda_mind.py` actualizado
- [ ] Tests E2E ejecutados
- [ ] Documentación actualizada
- [ ] Commit a `develop`

---

**Responsable**: AI Assistant  
**Revisado por**: Usuario (dgfre)  
**Estado**: 🟡 En progreso (66% completado)

