# 📊 ANÁLISIS PREGUNTAS PREDEFINIDAS - HARDCODED vs GPT

**Fecha**: 2025-11-27  
**Objetivo**: Validar la robustez del sistema conversacional GPT comparándolo con esquemas hardcodeados optimizados.

---

## 🎯 RESUMEN EJECUTIVO

Se analizaron **24 preguntas predefinidas** distribuidas en 3 modos:
- **Pharmacy**: 8 preguntas
- **Product**: 8 preguntas  
- **Partner**: 8 preguntas

**Resultado general**: 
- ✅ GPT genera queries **correctas y similares** en **18/24 casos** (75%)
- ⚠️  GPT genera queries **diferentes pero válidas** en **4/24 casos** (17%)
- ❌ GPT genera queries **incorrectas o mal formateadas** en **2/24 casos** (8%)

---

## 📋 MODO PHARMACY (8 preguntas)

### ✅ **Query 1: ¿Cuántas farmacias activas tenemos?**
- **Similitud**: 100%
- **Hardcoded**:
```json
{
  "collection": "pharmacies",
  "pipeline": [
    {"$match": {"active": 1}},
    {"$count": "total"}
  ]
}
```
- **GPT**: ✅ Idéntico
- **Conclusión**: ✅ Hardcodear NO es necesario, GPT perfecto

---

### ⚠️ **Query 2: Farmacias activas en {ciudad}**
- **Similitud**: 53%
- **Hardcoded**: Lista farmacias con `$project`
- **GPT**: Cuenta farmacias con `$group` y `$sum`
- **Conclusión**: ⚠️ GPT interpreta "en {ciudad}" como "cuántas hay", no "cuáles son". **HARDCODEAR para listar**.

**ESQUEMA HARDCODEADO RECOMENDADO**:
```json
{
  "collection": "pharmacies",
  "variables": ["ciudad"],
  "pipeline": [
    {"$match": {"active": 1, "contact.city": "{ciudad}"}},
    {"$project": {
      "description": 1,
      "contact.city": 1,
      "contact.postalCode": 1
    }}
  ]
}
```

---

### ❌ **Query 3: GMV total de la farmacia {farmacia_id}**
- **Similitud**: 0%
- **GPT**: Devolvió JSON mal formateado (truncado)
- **Conclusión**: ❌ **HARDCODEAR esta query** con cálculo híbrido GMV

**ESQUEMA HARDCODEADO RECOMENDADO**:
```json
{
  "collection": "bookings",
  "variables": ["farmacia_id"],
  "pipeline": [
    {"$match": {"target": "{farmacia_id}"}},
    {"$group": {
      "_id": null,
      "totalGMV": {
        "$sum": {
          "$cond": {
            "if": {"$gt": ["$thirdUser.price", null]},
            "then": "$thirdUser.price",
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
      },
      "totalPedidos": {"$sum": 1}
    }}
  ]
}
```

---

### ✅ **Query 4: GMV de {farmacia_id} en la última semana**
- **Similitud**: 85%
- **GPT**: Muy similar, solo usa `createdDate` en vez de `createdAt`
- **Conclusión**: ✅ GPT robusto, pero **HARDCODEAR para consistencia de campos**

---

### ✅ **Query 5: Pedidos de {farmacia_id} en {partner}**
- **Similitud**: 90%
- **GPT**: Casi idéntico
- **Conclusión**: ✅ GPT perfecto

---

### ✅ **Query 6: Top 10 farmacias que más venden**
- **Similitud**: 80%
- **GPT**: Usa `$amount` en vez del cálculo híbrido GMV
- **Conclusión**: ⚠️ **HARDCODEAR para garantizar cálculo híbrido GMV correcto**

**ESQUEMA HARDCODEADO RECOMENDADO**:
```json
{
  "collection": "bookings",
  "variables": [],
  "pipeline": [
    {"$group": {
      "_id": "$target",
      "totalGMV": {
        "$sum": {
          "$cond": {
            "if": {"$gt": ["$thirdUser.price", null]},
            "then": "$thirdUser.price",
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
      },
      "totalPedidos": {"$sum": 1}
    }},
    {"$sort": {"totalGMV": -1}},
    {"$limit": 10},
    {"$lookup": {
      "from": "pharmacies",
      "localField": "_id",
      "foreignField": "_id",
      "as": "pharmacy_info"
    }}
  ]
}
```

---

### ✅ **Query 7: Top 10 farmacias en {partner}**
- **Similitud**: 95%
- **GPT**: Casi perfecto, usa cálculo híbrido GMV correctamente
- **Conclusión**: ✅ GPT excelente, pero **HARDCODEAR para rendimiento**

---

### ⚠️ **Query 8: Farmacias con más de {cantidad} pedidos esta semana**
- **Similitud**: 70%
- **GPT**: Usa `createdDate` en vez de `createdAt`
- **Conclusión**: ⚠️ **HARDCODEAR para consistencia de campos**

---

## 📋 MODO PRODUCT (8 preguntas)

### ✅ **Query 1: ¿Cuántos productos activos tenemos?**
- **Similitud**: 100%
- **GPT**: Idéntico
- **Conclusión**: ✅ GPT perfecto

---

### ✅ **Query 2: Stock de {producto} (por code o ean13)**
- **Similitud**: 90%
- **GPT**: Muy similar
- **Conclusión**: ✅ GPT robusto, pero **HARDCODEAR para rendimiento**

**ESQUEMA HARDCODEADO RECOMENDADO**:
```json
{
  "collection": "stockItems",
  "variables": ["producto_code"],
  "pipeline": [
    {"$match": {"code": "{producto_code}"}},
    {"$lookup": {
      "from": "pharmacies",
      "localField": "target",
      "foreignField": "_id",
      "as": "pharmacy_info"
    }},
    {"$project": {
      "target": 1,
      "quantity": 1,
      "pvp": 1,
      "pva": 1,
      "pharmacy_name": {"$arrayElemAt": ["$pharmacy_info.description", 0]}
    }}
  ]
}
```

---

### ✅ **Query 3: Precio PVP de {producto}**
- **Similitud**: 85%
- **GPT**: Usa operadores estadísticos correctos
- **Conclusión**: ✅ GPT bueno

---

### ⚠️ **Query 4: ¿Qué farmacias tienen {producto} en stock?**
- **Similitud**: 43%
- **GPT**: Usa múltiples `$lookup` innecesarios (ineficiente)
- **Conclusión**: ❌ **HARDCODEAR con query optimizada**

**ESQUEMA HARDCODEADO RECOMENDADO**:
```json
{
  "collection": "stockItems",
  "variables": ["producto_code"],
  "pipeline": [
    {"$match": {"code": "{producto_code}", "quantity": {"$gt": 0}}},
    {"$lookup": {
      "from": "pharmacies",
      "localField": "target",
      "foreignField": "_id",
      "as": "pharmacy_info"
    }},
    {"$project": {
      "pharmacy_id": "$target",
      "quantity": 1,
      "pvp": 1,
      "pharmacy_name": {"$arrayElemAt": ["$pharmacy_info.description", 0]},
      "pharmacy_city": {"$arrayElemAt": ["$pharmacy_info.contact.city", 0]}
    }}
  ]
}
```

---

### ✅ **Query 5: Productos más vendidos esta semana**
- **Similitud**: 85%
- **GPT**: Usa `createdDate` en vez de `createdAt`, pero estructura correcta
- **Conclusión**: ⚠️ **HARDCODEAR para consistencia**

**ESQUEMA HARDCODEADO RECOMENDADO**:
```json
{
  "collection": "bookings",
  "variables": ["fecha_inicio"],
  "pipeline": [
    {"$match": {"createdAt": {"$gte": "{fecha_inicio}"}}},
    {"$unwind": "$items"},
    {"$group": {
      "_id": "$items.code",
      "totalVendido": {"$sum": "$items.quantity"},
      "totalPedidos": {"$sum": 1},
      "gmvTotal": {
        "$sum": {"$multiply": ["$items.pvp", "$items.quantity"]}
      }
    }},
    {"$sort": {"totalVendido": -1}},
    {"$limit": 10},
    {"$lookup": {
      "from": "items",
      "localField": "_id",
      "foreignField": "code",
      "as": "product_info"
    }}
  ]
}
```

---

### ✅ **Query 6-8: Top 10 productos por GMV, Parafarmacia, Medicamentos**
- **Similitud**: 80-90%
- **GPT**: Genera queries similares con pequeñas diferencias
- **Conclusión**: ✅ GPT robusto

---

## 📋 MODO PARTNER (8 preguntas)

### ✅ **Query 1: GMV total de {partner}**
- **Similitud**: 95%
- **GPT**: Usa cálculo híbrido GMV correctamente
- **Conclusión**: ✅ GPT excelente, pero **HARDCODEAR para rendimiento**

**ESQUEMA HARDCODEADO RECOMENDADO**:
```json
{
  "collection": "bookings",
  "variables": ["partner"],
  "pipeline": [
    {"$match": {"thirdUser.user": "{partner}"}},
    {"$group": {
      "_id": null,
      "totalGMV": {
        "$sum": {
          "$cond": {
            "if": {"$gt": ["$thirdUser.price", null]},
            "then": "$thirdUser.price",
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
      },
      "totalPedidos": {"$sum": 1}
    }}
  ]
}
```

---

### ✅ **Query 2: GMV de {partner} esta semana**
- **Similitud**: 90%
- **GPT**: Usa `createdDate` en vez de `createdAt`
- **Conclusión**: ⚠️ **HARDCODEAR para consistencia**

---

### ✅ **Query 3: Pedidos totales por partner**
- **Similitud**: 95%
- **GPT**: Genera ranking correcto
- **Conclusión**: ✅ GPT excelente

**ESQUEMA HARDCODEADO RECOMENDADO**:
```json
{
  "collection": "bookings",
  "variables": [],
  "pipeline": [
    {"$group": {
      "_id": "$thirdUser.user",
      "totalPedidos": {"$sum": 1},
      "totalGMV": {
        "$sum": {
          "$cond": {
            "if": {"$gt": ["$thirdUser.price", null]},
            "then": "$thirdUser.price",
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
      },
      "ticketPromedio": {"$avg": "$thirdUser.price"}
    }},
    {"$sort": {"totalPedidos": -1}}
  ]
}
```

---

### ✅ **Query 4-6: Top partners, Farmacias activas, GMV promedio**
- **Similitud**: 85-95%
- **GPT**: Genera queries correctas
- **Conclusión**: ✅ GPT robusto

---

### ⚠️ **Query 7: Evolución de pedidos de {partner} (últimos 7 días)**
- **Similitud**: 70%
- **GPT**: Agrupa por fecha correctamente, pero usa `createdDate`
- **Conclusión**: ⚠️ **HARDCODEAR para consistencia**

---

### ❌ **Query 8: Partners con más crecimiento**
- **Similitud**: 0%
- **GPT**: No hay esquema hardcodeado definido, pero GPT genera una query razonable
- **Conclusión**: ⚠️ **DEFINIR ESQUEMA HARDCODEADO** (requiere comparación temporal)

---

## 🎯 CONCLUSIONES FINALES

### ✅ **GPT ES ROBUSTO EN:**
1. Queries de conteo simple (`$count`)
2. Agregaciones por partner/farmacia con GMV (`$group`, `$sum`)
3. Rankings con `$sort` y `$limit`
4. Cálculo híbrido de GMV (lo aprendió del diccionario)
5. Uso de `$lookup` para nombres de farmacias

### ⚠️ **GPT TIENE PROBLEMAS EN:**
1. **Inconsistencia de nombres de campos**: Usa `createdDate` en vez de `createdAt`, `amount` en vez de `thirdUser.price`
2. **Interpretación de intención**: A veces cuenta cuando debe listar
3. **Formato de respuesta**: Algunos casos devuelve JSON truncado o mal formateado
4. **Queries complejas con múltiples joins**: Genera pipelines ineficientes

### 🔧 **RECOMENDACIONES PARA HARDCODING:**

#### **🟢 QUERIES QUE DEBEN SER 100% HARDCODEADAS (Alta prioridad)**:
1. ✅ **GMV total de farmacia** (query 3 pharmacy)
2. ✅ **Top 10 farmacias que más venden** (query 6 pharmacy)
3. ✅ **Farmacias con {producto} en stock** (query 4 product)
4. ✅ **Productos más vendidos** (query 5 product)
5. ✅ **GMV total de partner** (query 1 partner)
6. ✅ **Pedidos totales por partner** (query 3 partner)

**Razón**: Estas son queries de alto uso, requieren rendimiento óptimo y cálculo híbrido GMV preciso.

#### **🟡 QUERIES QUE PUEDEN SER HÍBRIDAS (Media prioridad)**:
1. ⚠️ **¿Cuántas farmacias activas?** → GPT perfecto, NO hardcodear
2. ⚠️ **Stock de producto** → GPT bueno, hardcodear solo para rendimiento
3. ⚠️ **Top partners por GMV** → GPT excelente, hardcodear opcional

#### **🔴 QUERIES QUE REQUIEREN MEJORA DEL DICCIONARIO**:
1. ❌ **Farmacias activas en {ciudad}** → Afinar prompt para "listar" vs "contar"
2. ❌ **Evolución temporal** → Añadir al diccionario patrones de series temporales
3. ❌ **Crecimiento comparativo** → Añadir lógica de comparación entre períodos

---

## 📝 PRÓXIMOS PASOS

### 1️⃣ **IMPLEMENTAR QUERIES HARDCODEADAS**
- Crear módulo `domain/queries/predefined_queries.py`
- Implementar las 6 queries de alta prioridad
- Añadir detección de patterns en `process_query()`

### 2️⃣ **MEJORAR DICCIONARIO SEMÁNTICO**
- Añadir campo `field_aliases` para manejar `createdDate` vs `createdAt`
- Añadir ejemplos de queries de series temporales
- Mejorar contexto para "listar" vs "contar"

### 3️⃣ **REFINAR PROMPTS GPT**
- Explicitar uso de `createdAt` (no `createdDate`)
- Explicitar uso de `thirdUser.price` (no `amount`)
- Añadir ejemplos de formato de respuesta esperado

### 4️⃣ **TESTING E2E**
- Crear suite de tests con las 24 preguntas
- Validar formato de respuesta
- Validar correctness de resultados

---

## 📊 MÉTRICAS DE ÉXITO

| Métrica | Actual | Objetivo |
|---------|--------|----------|
| Similitud GPT vs Hardcoded | 75% | 90% |
| Queries correctas | 18/24 (75%) | 22/24 (92%) |
| Queries mal formateadas | 2/24 (8%) | 0/24 (0%) |
| Tiempo respuesta P95 | ~3s | <1.5s (hardcoded) |

---

**FIN DEL ANÁLISIS** ✅

