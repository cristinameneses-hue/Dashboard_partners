# 📚 ANÁLISIS SEMÁNTICO DE PREGUNTAS - INTERPRETACIÓN

**Objetivo**: Entender cómo mapear lenguaje natural → campos de base de datos → intención del usuario

---

## 🏥 MODO PHARMACY (8 preguntas)

### ❓ Query 1: "¿Cuántas farmacias activas tenemos?"

**Interpretación semántica**:
- "Cuántas" → **OPERACIÓN**: Contar, devolver número
- "farmacias" → **COLECCIÓN**: `pharmacies`
- "activas" → **FILTRO**: `active = 1`
- "tenemos" → **ALCANCE**: Todas las disponibles

**Mapeo de campos**:
```
"farmacias" → collection: pharmacies
"activas" → field: pharmacies.active = 1
"cuántas" → aggregation: $count
```

**Lo que debe entender el sistema**:
1. Consultar colección `pharmacies`
2. Filtrar solo las activas (`active: 1`)
3. Devolver un contador (número)

**Lo que entendió GPT**:
✅ **CORRECTO** - Pipeline idéntico:
- Colección: `pharmacies`
- Match: `{active: 1}`
- Operación: `$count: "total"`

---

### ❓ Query 2: "Farmacias activas en {ciudad}"

**Interpretación semántica**:
- "Farmacias" → **COLECCIÓN**: `pharmacies`
- "activas" → **FILTRO**: `active = 1`
- "en {ciudad}" → **FILTRO GEOGRÁFICO**: `contact.city = "{ciudad}"`
- **IMPLÍCITO**: Query VAGA (sin verbo específico) → **AGREGACIÓN** (contar)

**Mapeo de campos**:
```
"farmacias" → collection: pharmacies
"activas" → field: pharmacies.active = 1
"en {ciudad}" → field: pharmacies.contact.city = "{ciudad}"
**INTENCIÓN**: Vaga → Agregación → $count: "total"
```

**Variables dinámicas**:
- `{ciudad}`: String, ejemplo: "Madrid", "Barcelona"

**Regla de Desambiguación aplicada**:
- Query SIN keywords explícitas (`listame`, `muéstrame`, `ver`) → AGREGACIÓN
- Si usuario quiere lista, debe decir: "Listame farmacias en Madrid"

**Lo que debe entender el sistema**:
1. Query es VAGA → asumir que quiere **TOTAL** (número)
2. Respuesta rápida: "Hay 45 farmacias activas en Madrid"
3. Si usuario quiere detalles, reformulará: "Listame las farmacias..."

**Lo que entendió GPT**:
✅ **CORRECTO** - Interpretó como COUNT (con sistema de validación)
- Usó `$count: "total"` → devuelve número
- Respuesta: agregación

**Sistema implementado**: ✅
- Detector de output type identifica como 'aggregation'
- GPT recibe hint para devolver count
- Resultado: query rápida y eficiente

---

### ❓ Query 3: "GMV total de la farmacia {farmacia_id}"

**Interpretación semántica**:
- "GMV" → **MÉTRICA**: Gross Merchandise Value = suma de ingresos
- "total" → **ALCANCE TEMPORAL**: Histórico, sin filtro de fecha
- "de la farmacia {farmacia_id}" → **FILTRO**: Pedidos donde `target = {farmacia_id}`

**Mapeo de campos**:
```
"GMV" → calculated: sum(items[].pvp * items[].quantity) por cada booking
"farmacia {farmacia_id}" → collection: bookings, filter: target = {farmacia_id}
"total" → time_range: null (histórico)
```

**Variables dinámicas**:
- `{farmacia_id}`: ObjectId o String, ejemplo: "507f1f77bcf86cd799439011"

**Lo que debe entender el sistema**:
1. Buscar en `bookings` (no en `pharmacies`)
2. Filtrar por farmacia destino (`target`)
3. Calcular GMV **estándar**: `items.pvp * items.quantity`
4. Sumar TODOS los pedidos históricos
5. **Bonus**: Devolver también `totalPedidos`

**Cálculo GMV**:
```javascript
// SIEMPRE usar este cálculo:
totalGMV = $reduce(
  input: $items,
  initialValue: 0,
  in: $add[$$value, $multiply[$$this.pvp, $$this.quantity]]
)
```

**Lo que entendió GPT**:
❌ **ERROR** - Devolvió JSON mal formateado (truncado)
- No generó pipeline válido
- Necesita hardcodearse

---

### ❓ Query 4: "GMV de {farmacia_id} en la última semana"

**Interpretación semántica**:
- "GMV" → **MÉTRICA**: Suma de ingresos
- "de {farmacia_id}" → **FILTRO**: `target = {farmacia_id}`
- "en la última semana" → **FILTRO TEMPORAL**: `createdDate >= (hoy - 7 días)`

**Mapeo de campos**:
```
"GMV" → calculated: sum(items[].pvp * items[].quantity)
"farmacia {farmacia_id}" → filter: bookings.target = {farmacia_id}
"última semana" → filter: bookings.createdDate >= Date.now() - 7 days
```

**Variables dinámicas**:
- `{farmacia_id}`: ObjectId/String
- `{fecha_inicio}`: Calculada = hoy - 7 días
- `{fecha_fin}`: Calculada = hoy

**Expresiones temporales a reconocer**:
- "última semana" / "esta semana" → 7 días
- "último mes" / "este mes" → 30 días
- "ayer" → 1 día
- "hoy" → desde las 00:00 de hoy

**Lo que debe entender el sistema**:
1. Igual que Query 3, pero con filtro temporal
2. **CRÍTICO**: Usar `createdDate` (NO `createdAt`)
3. Calcular fechas dinámicamente en Python antes de la query

---

### ❓ Query 5: "Pedidos de {farmacia_id} en {partner}"

**Interpretación semántica**:
- "Pedidos" → **ENTIDAD**: bookings, contar cantidad
- "de {farmacia_id}" → **FILTRO**: `target = {farmacia_id}`
- "en {partner}" → **FILTRO**: `thirdUser.user = {partner}`

**Mapeo de campos**:
```
"pedidos" → collection: bookings
"de {farmacia_id}" → filter: target = {farmacia_id}
"en {partner}" → filter: thirdUser.user = {partner}
**OUTPUT**: totalPedidos (count), totalGMV (sum)
```

**Variables dinámicas**:
- `{farmacia_id}`: ObjectId/String
- `{partner}`: String, uno de: [glovo, uber, danone, carrefour, justeat, amazon, procter, enna, nordic, chiesi, ferrer, glovo-otc]

**Lo que debe entender el sistema**:
1. Cruce de 2 dimensiones: farmacia + partner
2. Contar pedidos Y calcular GMV
3. Partners válidos: usar lista de 12 activos
4. Normalizar partner: "Glovo" → "glovo" (lowercase)

**Lo que entendió GPT**:
✅ **CORRECTO** - Generó pipeline adecuado

---

### ❓ Query 6: "Top 10 farmacias que más venden"

**Interpretación semántica**:
- "Top 10" → **OPERACIÓN**: Ranking, ordenar descendente, limitar a 10
- "farmacias" → **AGRUPACIÓN**: Agrupar por `target` (farmacia destino)
- "que más venden" → **MÉTRICA**: GMV total (suma de ingresos)
- **IMPLÍCITO**: Histórico, sin filtro de fecha

**Mapeo de campos**:
```
"farmacias" → group_by: bookings.target
"más venden" → order_by: totalGMV (desc)
"top 10" → limit: 10
**BONUS**: Hacer lookup a pharmacies para obtener nombres
```

**Lo que debe entender el sistema**:
1. Buscar en `bookings`
2. Agrupar por farmacia (`target`)
3. Calcular GMV estándar por farmacia
4. Contar pedidos por farmacia (`totalPedidos`)
5. Ordenar por GMV descendente
6. Limitar a 10
7. **Enriquecer**: Traer nombre de farmacia con `$lookup`

**Estructura del resultado esperado**:
```
Ranking:
1. Farmacia X - GMV: 50,000€ - Pedidos: 1,200
2. Farmacia Y - GMV: 45,000€ - Pedidos: 980
...
10. Farmacia Z - GMV: 20,000€ - Pedidos: 450
```

**Lo que entendió GPT**:
⚠️ **SIMILAR pero no idéntico**:
- Usó campo incorrecto para GMV (no el cálculo estándar)
- Estructura correcta: group → sort → limit → lookup

---

### ❓ Query 7: "Top 10 farmacias en {partner}"

**Interpretación semántica**:
- "Top 10 farmacias" → **OPERACIÓN**: Ranking de farmacias
- "en {partner}" → **FILTRO**: Solo pedidos de ese partner
- **IMPLÍCITO**: Ordenar por GMV (métrica por defecto para "top")

**Mapeo de campos**:
```
"en {partner}" → filter: bookings.thirdUser.user = {partner}
"farmacias" → group_by: bookings.target
"top 10" → order_by: totalGMV (desc), limit: 10
```

**Variables dinámicas**:
- `{partner}`: String de lista de 12 partners activos

**Lo que debe entender el sistema**:
1. **Primer filtro**: Solo bookings de ese partner
2. Luego agrupar por farmacia
3. Calcular GMV y pedidos
4. Ranking top 10

**Diferencia con Query 6**:
- Query 6: Todas las farmacias, todos los partners
- Query 7: Solo farmacias que venden en partner específico

**Lo que entendió GPT**:
✅ **EXCELENTE** - Pipeline casi perfecto con cálculo GMV correcto

---

### ❓ Query 8: "Farmacias con más de {cantidad} pedidos esta semana"

**Interpretación semántica**:
- "Farmacias" → **AGRUPACIÓN**: Agrupar por `target`
- "con más de {cantidad} pedidos" → **FILTRO POST-AGREGACIÓN**: `totalPedidos > {cantidad}`
- "esta semana" → **FILTRO TEMPORAL**: `createdDate >= (hoy - 7 días)`

**Mapeo de campos**:
```
"farmacias" → group_by: bookings.target
"más de {cantidad} pedidos" → having: totalPedidos > {cantidad}
"esta semana" → filter: createdDate >= Date.now() - 7 days
```

**Variables dinámicas**:
- `{cantidad}`: Integer, ejemplo: 50, 100, 200
- `{fecha_inicio}`: Calculada = hoy - 7 días

**Lo que debe entender el sistema**:
1. Filtro temporal ANTES de agrupar (más eficiente)
2. Agrupar por farmacia
3. Contar pedidos por farmacia
4. **Post-filtro** con `$match` después de `$group`: solo farmacias con `totalPedidos > {cantidad}`
5. Listar farmacias con nombre

**Uso de $match doble**:
```javascript
[
  {$match: {createdDate: {$gte: fecha}}},  // Pre-filtro temporal
  {$group: {_id: "$target", total: {$sum: 1}}},
  {$match: {total: {$gt: cantidad}}},  // Post-filtro por cantidad
  {$lookup: {...}}
]
```

**Lo que entendió GPT**:
⚠️ **SIMILAR** - Estructura correcta pero podría optimizarse

---

## 🧪 MODO PRODUCT (8 preguntas)

### ❓ Query 1: "¿Cuántos productos activos tenemos?"

**Interpretación semántica**:
- "Cuántos" → **OPERACIÓN**: Contar
- "productos" → **COLECCIÓN**: `items`
- "activos" → **FILTRO**: `active = 1`

**Mapeo de campos**:
```
"productos" → collection: items
"activos" → filter: items.active = 1
"cuántos" → aggregation: $count
```

**Lo que debe entender el sistema**:
- Consultar `items` (NO `stockItems`)
- Filtrar por `active: 1`
- Devolver número total

**Lo que entendió GPT**:
✅ **CORRECTO** - Idéntico al esperado

---

### ❓ Query 2: "Stock de {producto}"

**Interpretación semántica**:
- "Stock" → **MÉTRICA**: Cantidad disponible en farmacias
- "{producto}" → **FILTRO**: Puede ser descripción, code, o ean13

**Mapeo de campos**:
```
"{producto}" → Primero buscar en items por:
  - items.description (si es texto) → case insensitive
  - items.code (si es 6 dígitos) → exacto
  - items.ean13 (si es 13 dígitos) → exacto
  
Luego buscar en stockItems:
  - stockItems.code = code_encontrado
  - stockItems.quantity > 0 (opcional, mostrar todo)
  
Enriquecer con lookup:
  - pharmacies para obtener nombre de farmacia
```

**Variables dinámicas**:
- `{producto}`: String/Number
  - Ejemplos: "Paracetamol", "123456", "1234567890123"

**Lógica de identificación de producto**:
1. Si contiene letras → buscar por `description` (case insensitive)
2. Si son 6 dígitos → buscar por `code` (CN)
3. Si son 13 dígitos → buscar por `ean13`

**Lo que debe entender el sistema**:
1. **Paso 1**: Identificar tipo de búsqueda
2. **Paso 2**: Buscar producto en `items`
3. **Paso 3**: Si hay múltiples resultados → pedir al usuario que elija
4. **Paso 4**: Con el `code` confirmado, buscar en `stockItems`
5. **Paso 5**: Listar farmacias con stock, quantity, pvp

**Lo que entendió GPT**:
✅ **BUENO** - Estructura correcta con lookup

---

### ❓ Query 3: "Precio PVP de {producto}"

**Interpretación semántica**:
- "Precio PVP" → **MÉTRICA**: Precio de venta al público
- "{producto}" → **FILTRO**: Identificar producto (igual que Query 2)
- **IMPLÍCITO**: Dar estadísticas (min, max, promedio, moda)

**Mapeo de campos**:
```
"{producto}" → Identificar en items (description/code/ean13)
"Precio PVP" → field: stockItems.pvp (varía por farmacia)
**ESTADÍSTICAS**:
  - Moda (más común)
  - Mínimo
  - Máximo  
  - Promedio
```

**Lo que debe entender el sistema**:
1. Buscar producto en `items`
2. Obtener todos los registros en `stockItems` con ese `code`
3. Calcular estadísticas del campo `pvp`
4. Presentar al usuario: "El precio PVP varía entre X€ y Y€, siendo el más común Z€"

**Lo que entendió GPT**:
✅ **CORRECTO** - Usó operadores estadísticos ($min, $max, $avg, $first)

---

### ❓ Query 4: "¿Qué farmacias tienen {producto} en stock?"

**Interpretación semántica**:
- "Qué farmacias" → **RESULTADO**: Lista de farmacias
- "tienen {producto}" → **FILTRO**: `stockItems.code = {producto_code}`
- "en stock" → **FILTRO**: `quantity > 0`

**Mapeo de campos**:
```
"{producto}" → Identificar code
"en stock" → filter: stockItems.quantity > 0
"qué farmacias" → lookup: pharmacies, project: description, city
```

**Lo que debe entender el sistema**:
1. Identificar producto (misma lógica que Query 2 y 3)
2. Buscar en `stockItems` con `quantity > 0`
3. **Lookup** a `pharmacies` para traer:
   - Nombre (`description`)
   - Ciudad (`contact.city`)
   - Código postal (`contact.postalCode`)
4. Mostrar también: `quantity` y `pvp` de cada farmacia

**Lo que entendió GPT**:
❌ **INEFICIENTE** - Usó múltiples lookups innecesarios
- Debería hacer 1 lookup a pharmacies
- GPT hizo 3 lookups (sobrecomplejo)

---

### ❓ Query 5: "Productos más vendidos esta semana"

**Interpretación semántica**:
- "Productos" → **AGRUPACIÓN**: Agrupar por código de producto
- "más vendidos" → **MÉTRICA**: Cantidad vendida (`items.quantity`)
- "esta semana" → **FILTRO TEMPORAL**: `createdDate >= (hoy - 7 días)`

**Mapeo de campos**:
```
"productos" → group_by: items.code (dentro de bookings)
"más vendidos" → order_by: totalVendido (desc) = sum(items.quantity)
"esta semana" → filter: bookings.createdDate >= Date.now() - 7 days
**BONUS**: Calcular también GMV por producto
```

**Lo que debe entender el sistema**:
1. Buscar en `bookings` (NO en `items`)
2. Filtrar por fecha: última semana
3. **Descomponer** array `items` con `$unwind`
4. Agrupar por `items.code`
5. Calcular:
   - `totalVendido`: sum de `items.quantity`
   - `totalPedidos`: count de pedidos
   - `gmvTotal`: sum de `items.pvp * items.quantity`
6. Ordenar por `totalVendido` descendente
7. Limitar a 10
8. **Lookup** a `items` para traer nombre del producto

**Pipeline crítico**:
```javascript
[
  {$match: {createdDate: {$gte: fecha}}},
  {$unwind: "$items"},  // ← CRÍTICO para separar productos
  {$group: {
    _id: "$items.code",
    totalVendido: {$sum: "$items.quantity"},
    gmvTotal: {$sum: {$multiply: ["$items.pvp", "$items.quantity"]}}
  }},
  {$sort: {totalVendido: -1}},
  {$limit: 10},
  {$lookup: {from: "items", localField: "_id", foreignField: "code"}}
]
```

**Lo que entendió GPT**:
✅ **BUENO** - Estructura correcta con $unwind

---

### ❓ Query 6: "Top 10 productos por GMV"

**Interpretación semántica**:
- Similar a Query 5, pero ordenar por **GMV** en vez de cantidad vendida
- **IMPLÍCITO**: Histórico (sin filtro temporal)

**Mapeo de campos**:
```
"productos" → group_by: items.code
"por GMV" → order_by: gmvTotal (desc) = sum(items.pvp * items.quantity)
"top 10" → limit: 10
```

**Diferencia con Query 5**:
- Query 5: Ordenar por cantidad vendida (unidades)
- Query 6: Ordenar por dinero generado (GMV)

---

### ❓ Query 7: "Productos de parafarmacia (itemType = 3)"

**Interpretación semántica**:
- "Productos de parafarmacia" → **FILTRO**: `items.itemType = 3`
- **IMPLÍCITO**: Listar productos (no contar)

**Mapeo de campos**:
```
"parafarmacia" → filter: items.itemType = 3
**OUTPUT**: Lista de productos con description, code, ean13
```

**Regla de negocio**:
- `itemType = 3` → Parafarmacia
- `itemType != 3` → Medicamento

**Lo que debe entender el sistema**:
1. Consultar `items`
2. Filtrar por `itemType: 3`
3. Proyectar campos relevantes

---

### ❓ Query 8: "Medicamentos más demandados"

**Interpretación semántica**:
- "Medicamentos" → **FILTRO**: `items.itemType != 3`
- "más demandados" → **MÉTRICA**: Cantidad vendida
- **IMPLÍCITO**: Temporal = últimos 7 días (por defecto)

**Mapeo de campos**:
```
"medicamentos" → Primero: items.itemType != 3
                Luego: analizar en bookings
"más demandados" → order_by: totalVendido (desc)
```

**Lo que debe entender el sistema**:
1. Obtener lista de `code` de items con `itemType != 3`
2. Buscar en bookings esos productos
3. Aplicar lógica similar a Query 5

---

## 🤝 MODO PARTNER (8 preguntas)

### ❓ Query 1: "GMV total de {partner}"

**Interpretación semántica**:
- "GMV" → **MÉTRICA**: Suma de ingresos
- "total" → **ALCANCE TEMPORAL**: Histórico
- "de {partner}" → **FILTRO**: `thirdUser.user = {partner}`

**Mapeo de campos**:
```
"{partner}" → filter: bookings.thirdUser.user = {partner}
"GMV total" → aggregation: sum(items[].pvp * items[].quantity)
**BONUS**: totalPedidos, ticketPromedio
```

**Variables dinámicas**:
- `{partner}`: Uno de los 12 partners activos

**Lo que debe entender el sistema**:
1. Filtrar bookings por partner
2. Calcular GMV estándar
3. Contar pedidos
4. Calcular ticket promedio: GMV / pedidos

---

### ❓ Query 2: "GMV de {partner} esta semana"

**Interpretación semántica**:
- Igual que Query 1 pero con filtro temporal

**Mapeo de campos**:
```
"{partner}" → filter: thirdUser.user = {partner}
"esta semana" → filter: createdDate >= Date.now() - 7 days
"GMV" → sum(items.pvp * items.quantity)
```

---

### ❓ Query 3: "Pedidos totales por partner"

**Interpretación semántica**:
- "Pedidos totales" → **OPERACIÓN**: Count de bookings
- "por partner" → **AGRUPACIÓN**: Agrupar por `thirdUser.user`
- **IMPLÍCITO**: Ranking (ordenar descendente)

**Mapeo de campos**:
```
"por partner" → group_by: thirdUser.user
"pedidos totales" → aggregation: {$sum: 1}
**BONUS**: totalGMV, ticketPromedio
**ORDER**: totalPedidos (desc)
```

**Lo que debe entender el sistema**:
1. NO filtrar por partner (queremos TODOS)
2. Agrupar por `thirdUser.user`
3. Calcular por cada partner:
   - Total de pedidos
   - Total GMV
   - Ticket promedio
4. Ordenar por pedidos (descendente)

**Resultado esperado**:
```
Ranking de Partners:
1. Glovo - 10,000 pedidos - 500,000€ GMV - 50€ ticket
2. Uber - 8,500 pedidos - 425,000€ GMV - 50€ ticket
...
```

---

### ❓ Query 4: "Top 10 partners por GMV"

**Interpretación semántica**:
- Similar a Query 3 pero ordenar por GMV (no por pedidos)
- Limitar a top 10

**Mapeo de campos**:
```
"por GMV" → order_by: totalGMV (desc)
"top 10" → limit: 10
```

---

### ❓ Query 5: "Farmacias activas en {partner}"

**Interpretación semántica**:
- "Farmacias activas" → **COLECCIÓN**: pharmacies con `active = 1`
- "en {partner}" → **FILTRO**: Depende del partner

**Mapeo de campos (LÓGICA COMPLEJA)**:
```
**SI partner tiene TAGS** (Glovo, Amazon, Carrefour, etc.):
  collection: pharmacies
  filter: {active: 1, tags: {$in: [tags_del_partner]}}
  
**SI partner NO tiene tags** (Uber, Justeat):
  collection: bookings
  filter: {thirdUser.user: {partner}, createdDate: {$gte: fecha}}
  group_by: target (farmacias únicas)
  lookup: pharmacies con active: 1
```

**Reglas especiales por partner** (del diccionario):

**CON TAGS**:
- Glovo → `tags: "GLOVO"`
- Glovo-OTC → `tags: {$in: ["GLOVO-OTC_2H", "GLOVO-OTC_48H"]}`
- Amazon → `tags: {$in: ["AMAZON_2H", "AMAZON_48H"]}`
- Carrefour → `tags: {$in: ["CARREFOUR_2H", "CARREFOUR_48H"]}`
- Danone, Procter, Enna, Nordic → Similar (2H, 48H, BACKUP)
- Chiesi → `tags: {$in: ["CHIESI_48H", "CHIESI_BACKUP"]}`
- Ferrer → `tags: {$in: ["FERRER_2H", "FERRER_48H"]}`

**SIN TAGS**:
- Uber → Farmacias con pedidos de Uber en el período
- Justeat → Farmacias con pedidos de Justeat en el período

**IGNORAR**:
- Nutriben (no es partner activo)

**Lo que debe entender el sistema**:
1. **Paso 1**: Identificar si el partner usa tags o no
2. **Paso 2A (con tags)**: Consultar `pharmacies` con filtro de tags
3. **Paso 2B (sin tags)**: Consultar `bookings`, agrupar farmacias, lookup a `pharmacies`
4. **Paso 3**: Devolver lista con nombre, ciudad, tags

---

### ❓ Query 6: "GMV promedio por pedido en {partner}"

**Interpretación semántica**:
- "GMV promedio" → **MÉTRICA**: GMV total / número de pedidos
- "por pedido" → **OPERACIÓN**: Average
- "en {partner}" → **FILTRO**: `thirdUser.user = {partner}`

**Mapeo de campos**:
```
"{partner}" → filter: thirdUser.user = {partner}
"GMV promedio por pedido" → aggregation: $avg de GMV calculado
```

**Cálculo**:
```javascript
// Opción 1: Calcular GMV por pedido, luego promediar
{$addFields: {gmv_pedido: {$reduce: {...}}}},
{$group: {_id: null, avgGMV: {$avg: "$gmv_pedido"}}}

// Opción 2: Más directo
{$group: {
  _id: null,
  totalGMV: {$sum: {$reduce: {...}}},
  totalPedidos: {$sum: 1}
}},
{$addFields: {avgGMV: {$divide: ["$totalGMV", "$totalPedidos"]}}}
```

---

### ❓ Query 7: "Evolución de pedidos de {partner} (últimos 7 días)"

**Interpretación semántica**:
- "Evolución" → **OPERACIÓN**: Serie temporal, agrupar por fecha
- "de pedidos" → **MÉTRICA**: Count por día
- "últimos 7 días" → **FILTRO TEMPORAL**: Últimos 7 días

**Mapeo de campos**:
```
"{partner}" → filter: thirdUser.user = {partner}
"últimos 7 días" → filter: createdDate >= Date.now() - 7 days
"evolución" → group_by: date (extraer día de createdDate)
              order_by: date (asc)
```

**Lo que debe entender el sistema**:
1. Filtrar por partner y últimos 7 días
2. Agrupar por fecha (truncar a día)
3. Contar pedidos por día
4. **Opcional**: Calcular GMV por día
5. Ordenar por fecha (ascendente)

**Resultado esperado**:
```
Evolución Glovo:
2024-11-20: 120 pedidos - 6,000€
2024-11-21: 135 pedidos - 6,750€
2024-11-22: 110 pedidos - 5,500€
...
2024-11-26: 150 pedidos - 7,500€
```

---

### ❓ Query 8: "Partners con más crecimiento"

**Interpretación semántica**:
- "Partners" → **AGRUPACIÓN**: Por partner
- "con más crecimiento" → **MÉTRICA COMPLEJA**: Comparar período actual vs anterior
- **IMPLÍCITO**: Últimos 7 días vs 7 días previos

**Mapeo de campos (COMPLEJO)**:
```
**PASO 1**: Calcular GMV de últimos 7 días por partner
**PASO 2**: Calcular GMV de 7 días anteriores (días 8-14) por partner
**PASO 3**: Calcular % de crecimiento: ((actual - anterior) / anterior) * 100
**PASO 4**: Ordenar por % crecimiento (desc)
```

**Lógica temporal**:
```
Período actual: createdDate >= (hoy - 7 días) AND createdDate < hoy
Período anterior: createdDate >= (hoy - 14 días) AND createdDate < (hoy - 7 días)
```

**Lo que debe entender el sistema**:
1. Necesita 2 agregaciones o usar `$facet`
2. Comparar métricas entre períodos
3. Calcular porcentaje de cambio
4. Ordenar por crecimiento

**Esta es la más compleja** → Candidata a hardcodear

---

## 📊 RESUMEN DE PATRONES COMUNES

### 🔍 **Palabras clave de OPERACIÓN**:
- "Cuántas/Cuántos" → `$count`
- "Listar/Qué/Cuáles" → `$project` + lista
- "Top N" → `$sort` + `$limit`
- "Más" (más vendido, más pedidos) → `$sort` descendente
- "Total" → `$sum` o histórico (sin filtro temporal)
- "Promedio" → `$avg`
- "Evolución" → `$group` por fecha

### 📅 **Palabras clave TEMPORALES**:
- "Hoy" → `createdDate >= Date.now().startOfDay()`
- "Ayer" → `createdDate >= (hoy - 1 día).startOfDay() AND < hoy.startOfDay()`
- "Esta semana" / "Última semana" → `>= hoy - 7 días`
- "Este mes" / "Último mes" → `>= hoy - 30 días`
- "Total" / Sin mención → Histórico (sin filtro)

### 🎯 **Palabras clave de ENTIDAD**:
- "Farmacia" / "Farmacias" → Collections: `pharmacies`, `bookings.target`
- "Producto" / "Productos" → Collections: `items`, `stockItems`, `bookings.items[]`
- "Partner" / "Canal" → Field: `bookings.thirdUser.user`
- "Pedido" / "Pedidos" → Collection: `bookings`
- "Stock" → Collection: `stockItems`

### 💰 **Palabras clave de MÉTRICA**:
- "GMV" / "Ventas" / "Ingresos" → `sum(items.pvp * items.quantity)`
- "Pedidos" → `count` de bookings
- "Precio" / "PVP" → `stockItems.pvp` (con estadísticas)
- "Cantidad" / "Stock" → `stockItems.quantity`
- "Activo" / "Activa" → `active = 1`

---

## ✅ **CONCLUSIÓN**

**Claves para interpretar correctamente**:
1. ✅ Identificar la OPERACIÓN (contar, listar, ranking)
2. ✅ Identificar las ENTIDADES (farmacias, productos, partners)
3. ✅ Identificar los FILTROS (activo, fecha, partner)
4. ✅ Identificar las MÉTRICAS (GMV, pedidos, precio)
5. ✅ Mapear variables dinámicas correctamente
6. ✅ Usar campos correctos: `createdDate`, `active: 1`, cálculo GMV estándar

**GPT es robusto en**:
- Operaciones simples (count, sum, avg)
- Rankings con group + sort + limit
- Identificar colecciones correctas

**GPT necesita mejora en**:
- Interpretación de "listar" vs "contar"
- Queries complejas con múltiples lookups
- Comparaciones temporales (crecimiento)
- Usar SIEMPRE el cálculo GMV estándar (ahora corregido en prompt)

---

**¿Quieres que ahora repasemos alguna query específica con más detalle o hacemos pruebas reales con GPT?** 🚀

