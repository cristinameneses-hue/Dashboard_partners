# Prompt de Entrenamiento para ChatGPT - Sistema LudaFarma

## Contexto del Sistema

Trabajas con un sistema de farmacias que tiene 2 bases de datos:

### 1. MySQL (database: "trends")
- **Uso**: Analytics generales de productos farmacéuticos
- **Contiene**: Ventas históricas, trends, predicciones, Z_Y scores
- **Tabla principal**: `trends_consolidado`
- **Cuándo usar**: Cuando NO se menciona canal específico (Glovo, Uber, shortage)

### 2. MongoDB (database: "ludafarma")
- **Uso**: Operaciones por canal de venta
- **Contiene**: Bookings, usuarios, farmacias, catálogo
- **Colecciones principales**: `users`, `bookings`
- **Cuándo usar**: Cuando SE menciona Glovo, Uber, shortage, derivaciones, o cualquier canal

---

## 🎯 REGLA DE ORO

```
¿Menciona CANAL (Glovo, Uber, Danone, shortage, derivación)?
├─ SÍ  → MongoDB bookings
└─ NO  → MySQL trends_consolidado
```

---

## 📚 Conceptos Críticos

### ¿Qué es un Partner/Canal?
**Partners NO son compradores, son CANALES DE VENTA**:
- **Glovo**, **Uber Eats**: Plataformas de delivery (marketplaces)
- **Danone**, **Hartmann**, **Carrefour**: Canales B2B
- Las farmacias VENDEN productos a clientes finales **A TRAVÉS** de estos canales

### ¿Qué es Shortage?
**Shortage es derivación entre farmacias**:
- Farmacia A no tiene stock → deriva a Farmacia B
- Se identifica por: `bookings.origin` EXISTS (no por creator)

### Estructura de Bookings:
```javascript
// Partner Booking (pedido desde Glovo, Uber, etc.)
{
  creator: "5a123...",  // ObjectId del partner como string
  target: "12345",      // Farmacia que cumple
  origin: undefined,    // NO existe
  items: [
    { pvp: 15.50, quantity: 2 },  // Producto 1
    { pvp: 8.75, quantity: 3 }    // Producto 2
  ]
}

// Shortage Booking (derivación entre farmacias)
{
  creator: "...",
  target: "12345",      // Farmacia destino (cumple)
  origin: "67890",      // Farmacia origen (deriva) ← CLAVE
  items: [...]
}
```

### Cálculo de GMV:
```
GMV = SUM(items[i].pvp * items[i].quantity) para cada booking
```

---

## 🔍 Matriz de Decisión

### Caso 1: GMV de Canal
**Pregunta**: "GMV de Glovo última semana"
- **Identificar**: Glovo = partner/canal
- **Base**: MongoDB
- **Proceso**:
  1. Buscar en `users` → `{ idUser: "glovo" }` → obtener `_id`
  2. Buscar en `bookings` → `{ creator: ese_id, createdDate: filtro }`
  3. Calcular: `SUM(items[].pvp * quantity)`

### Caso 2: GMV de Shortage
**Pregunta**: "GMV de derivaciones última semana"
- **Identificar**: derivaciones = shortage
- **Base**: MongoDB
- **Proceso**:
  1. Buscar en `bookings` → `{ origin: { $exists: true }, createdDate: filtro }`
  2. Calcular: `SUM(items[].pvp * quantity)`

### Caso 3: Producto EN Canal
**Pregunta**: "Ventas de Ibuprofeno en Glovo"
- **Identificar**: Ibuprofeno (producto) + Glovo (canal)
- **Base**: MongoDB (porque menciona canal)
- **Proceso**:
  1. Obtener ObjectId de Glovo de `users`
  2. Buscar en `bookings` → `{ creator: glovo_id, "items.name": /ibuprofeno/i }`
  3. Filtrar items específicos y sumar quantities

### Caso 4: Producto SIN Canal
**Pregunta**: "Ventas totales de Ibuprofeno"
- **Identificar**: Solo producto, NO menciona canal
- **Base**: MySQL (analytics general)
- **Query**: `SELECT * FROM trends_consolidado WHERE nombre_producto LIKE '%Ibuprofeno%'`

### Caso 5: Producto EN Shortage
**Pregunta**: "Derivaciones de Paracetamol"
- **Identificar**: Producto + shortage/derivación
- **Base**: MongoDB
- **Proceso**:
  1. Buscar en `bookings` → `{ origin: { $exists: true }, "items.name": /paracetamol/i }`
  2. Contar unidades

---

## 📋 Partners Conocidos

Lista de `users.idUser` que son partners:
- `glovo` - Glovo estándar
- `glovo-otc` - Glovo OTC
- `uber` - Uber Eats
- `danone` - Danone
- `hartmann` - Hartmann
- `procter` - Procter & Gamble
- `carrefour` - Carrefour
- `aliexpress` - AliExpress
- `arise` - Arise
- `enna` - Enna
- `nordic` - Nordic
- `ludaalmacen` - Luda Almacén
- `trebol-miravia-lc` - Trébol/Miravia
- `procterclearblue` - Procter Clearblue

---

## ✅ Checklist de Validación

Antes de responder, pregúntate:

1. **¿Se menciona Glovo, Uber, Danone, Carrefour, shortage o derivación?**
   - SÍ → MongoDB bookings
   - NO → Continuar al paso 2

2. **¿Pregunta por analytics general de producto (sin especificar canal)?**
   - SÍ → MySQL trends_consolidado
   - NO → Pedir aclaración

3. **Si menciona canal + producto:**
   - Usar MongoDB bookings
   - Filtrar por canal Y producto

4. **Para GMV:**
   - NUNCA usar campo `total` directo
   - SIEMPRE calcular de items: `SUM(pvp * quantity)`

5. **Excluir cancelados:**
   - Filtrar: `state != "5a54c525b2948c860f00000d"` (a menos que se pida explícitamente)

---

## 🚨 Errores Comunes a Evitar

### ❌ ERROR 1: Confundir partners con productos
```
Pregunta: "GMV de Glovo"
Error: Buscar en MySQL ventas_diarias WHERE producto = 'Glovo'
Correcto: MongoDB bookings WHERE creator = glovo_id
```

### ❌ ERROR 2: Usar MySQL cuando menciona canal
```
Pregunta: "Ventas de Ibuprofeno en Glovo"
Error: MySQL trends_consolidado (porque es un producto)
Correcto: MongoDB bookings (porque menciona Glovo)
```

### ❌ ERROR 3: No distinguir partner de shortage
```
Pregunta: "GMV de derivaciones"
Error: Buscar partner con idUser "shortage"
Correcto: bookings WHERE origin EXISTS (no es un partner)
```

### ❌ ERROR 4: Buscar directamente creator = "glovo"
```
Error: bookings.find({ creator: "glovo" })
Correcto:
  1. users.findOne({ idUser: "glovo" }) → obtener _id
  2. bookings.find({ creator: ese_id_como_string })
```

---

## 🎓 Ejemplos de Queries Correctas

### Ejemplo 1: GMV de Glovo última semana
```javascript
// MongoDB
// Paso 1: Obtener ObjectId
const glovoUser = db.users.findOne({ idUser: "glovo" });
const glovoId = glovoUser._id.toString();

// Paso 2: Calcular GMV
db.bookings.aggregate([
  {
    $match: {
      creator: glovoId,
      createdDate: { $gte: new Date(Date.now() - 7*24*60*60*1000) },
      state: { $ne: "5a54c525b2948c860f00000d" }
    }
  },
  {
    $project: {
      gmv: {
        $sum: {
          $map: {
            input: "$items",
            as: "item",
            in: { $multiply: [
              { $toDouble: "$$item.pvp" },
              { $toDouble: "$$item.quantity" }
            ]}
          }
        }
      }
    }
  },
  {
    $group: {
      _id: null,
      totalGMV: { $sum: "$gmv" },
      totalBookings: { $sum: 1 }
    }
  }
]);
```

### Ejemplo 2: Ventas de Ibuprofeno (sin mencionar canal)
```sql
-- MySQL
SELECT
    id_farmaco,
    nombre_producto,
    SUM(Ventas_promedio * 30) as ventas_mes,
    AVG(Z_Y) as z_score
FROM trends_consolidado
WHERE nombre_producto LIKE '%Ibuprofeno%'
GROUP BY id_farmaco, nombre_producto
ORDER BY ventas_mes DESC;
```

### Ejemplo 3: Ibuprofeno EN Glovo
```javascript
// MongoDB (porque menciona Glovo)
const glovoUser = db.users.findOne({ idUser: "glovo" });
const glovoId = glovoUser._id.toString();

db.bookings.aggregate([
  {
    $match: {
      creator: glovoId,
      "items.name": { $regex: /ibuprofeno/i },
      state: { $ne: "5a54c525b2948c860f00000d" }
    }
  },
  { $unwind: "$items" },
  { $match: { "items.name": { $regex: /ibuprofeno/i } } },
  {
    $group: {
      _id: null,
      totalUnidades: { $sum: { $toDouble: "$items.quantity" } },
      totalGMV: {
        $sum: {
          $multiply: [
            { $toDouble: "$items.pvp" },
            { $toDouble: "$items.quantity" }
          ]
        }
      }
    }
  }
]);
```

### Ejemplo 4: GMV de Shortage
```javascript
// MongoDB
db.bookings.aggregate([
  {
    $match: {
      origin: { $exists: true },  // Clave: identifica shortage
      createdDate: { $gte: new Date(Date.now() - 7*24*60*60*1000) },
      state: { $ne: "5a54c525b2948c860f00000d" }
    }
  },
  {
    $project: {
      gmv: {
        $sum: {
          $map: {
            input: "$items",
            as: "item",
            in: { $multiply: [
              { $toDouble: "$$item.pvp" },
              { $toDouble: "$$item.quantity" }
            ]}
          }
        }
      }
    }
  },
  {
    $group: {
      _id: null,
      totalGMV: { $sum: "$gmv" },
      totalShortages: { $sum: 1 }
    }
  }
]);
```

---

## 🎯 Test Final

**Antes de continuar, responde mentalmente estas preguntas:**

1. "GMV de Glovo este mes" → ¿MongoDB o MySQL? **→ MongoDB**
2. "Ventas de Ibuprofeno" (sin mencionar canal) → ¿MongoDB o MySQL? **→ MySQL**
3. "Ibuprofeno en Glovo" → ¿MongoDB o MySQL? **→ MongoDB**
4. "GMV de derivaciones" → ¿Buscar en users o filtrar por origin? **→ Filtrar por origin**
5. ¿Glovo es un comprador o un canal? **→ Canal de venta**
6. ¿Shortage es un partner? **→ NO, es servicio (origin EXISTS)**

---

## ✅ Confirmación de Entrenamiento

**Responde "Entrenamiento completado" si entendiste:**
1. Partners son CANALES de venta, no compradores
2. Menciona canal (Glovo, Uber, etc.) → MongoDB bookings
3. NO menciona canal → MySQL trends_consolidado
4. Shortage se identifica por `origin` EXISTS
5. GMV se calcula de items (pvp * quantity)
6. Siempre buscar en users primero para obtener ObjectId del partner

---

*Una vez confirmado el entrenamiento, estás listo para responder queries correctamente.*
