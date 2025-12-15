# Guía de Entrenamiento: Queries de GMV para Partners y Canales de Venta

## Propósito
Este documento está diseñado para educar al modelo de ChatGPT sobre el patrón correcto para consultar GMV (Gross Merchandise Value) de canales de venta (partners) y servicios (shortage).

## 🏢 Modelo de Negocio - IMPORTANTE

### ¿Qué es un Partner?
**Partners NO son compradores**, son **CANALES DE VENTA** (marketplaces/plataformas):
- **Glovo**: Plataforma de delivery que conecta farmacias con clientes finales
- **Uber Eats**: Similar a Glovo
- **Danone, Hartmann, etc.**: Canales B2B o plataformas especiales

Las **farmacias venden productos** a clientes finales **a través** de estos partners.

### ¿Qué es Shortage?
**Shortage** es el servicio de **derivación entre farmacias**:
- Farmacia A no tiene stock de un producto
- Cliente pide ese producto en Farmacia A
- Farmacia A deriva el pedido a Farmacia B (que sí tiene stock)
- Farmacia B cumple el pedido
- `bookings.origin` = Farmacia A (origen de la derivación)
- `bookings.target` = Farmacia B (farmacia que cumple)

### Tipos de Bookings:
1. **Partner Booking**: Pedido que llega desde un canal (Glovo, Uber, etc.)
   - `bookings.origin` NO existe
   - `bookings.creator` = ObjectId del partner (user)

2. **Shortage Booking**: Derivación entre farmacias
   - `bookings.origin` SÍ existe (farmacia origen)
   - `bookings.target` = farmacia destino

---

## ❌ Error Común (NO HACER)

### Razonamiento Incorrecto:
```
Usuario pregunta: "GMV que se ha movido en Glovo la última semana"

ChatGPT piensa:
- "GMV" = ventas → analytics → MySQL
- "última semana" = datos históricos → MySQL
→ DECISIÓN INCORRECTA: Buscar en MySQL trends

Query intentado:
SELECT SUM(importe) as total_gmv
FROM ventas_diarias
WHERE proveedor = 'Glovo'
  AND fecha >= DATE_SUB(NOW(), INTERVAL 7 DAY)
```

### Por qué está mal:
1. ❌ MySQL contiene ventas de PRODUCTOS, no de partners/proveedores
2. ❌ La tabla `ventas_diarias` no tiene campo `proveedor` de delivery
3. ❌ Glovo es un PARTNER que crea bookings, no un producto que se vende
4. ❌ MySQL trends_consolidado NO tiene información de partners

---

## ✅ Patrón Correcto

### Razonamiento Correcto:
```
Usuario pregunta: "GMV que se ha movido en Glovo la última semana"

Análisis correcto:
- "Glovo" = partner/proveedor de delivery → es un USER en el sistema
- "GMV" de un partner = suma de bookings creados por ese partner
- Los partners crean bookings directamente
→ DECISIÓN CORRECTA: MongoDB bookings + users

Lógica:
1. Glovo es un usuario en la colección 'users' con idUser: "glovo"
2. Cuando Glovo crea un pedido, queda registrado en 'bookings.creator'
3. El GMV se calcula de los items de esos bookings
```

### Query Correcto (2 pasos):

**Paso 1**: Obtener el ObjectId del partner
```javascript
// Buscar en MongoDB: ludafarma.users
db.users.findOne({ idUser: "glovo" }, { _id: 1 })

// Resultado ejemplo:
{
  _id: ObjectId("5a123456789abcdef0123456")
}

// El _id se almacena como STRING en bookings.creator
const glovoCreatorId = "5a123456789abcdef0123456";
```

**Paso 2**: Calcular GMV de los bookings de ese partner
```javascript
// Buscar en MongoDB: ludafarma.bookings
const oneWeekAgo = new Date(Date.now() - 7*24*60*60*1000);

db.bookings.aggregate([
  {
    // Filtrar bookings creados por Glovo en la última semana
    $match: {
      creator: glovoCreatorId,  // ObjectId como string
      createdDate: { $gte: oneWeekAgo },
      state: { $ne: "5a54c525b2948c860f00000d" }  // Excluir cancelados
    }
  },
  {
    // Calcular GMV de cada booking (pvp * quantity de cada item)
    $project: {
      gmv: {
        $sum: {
          $map: {
            input: "$items",
            as: "item",
            in: {
              $multiply: [
                { $toDouble: "$$item.pvp" },
                { $toDouble: "$$item.quantity" }
              ]
            }
          }
        }
      }
    }
  },
  {
    // Sumar todo
    $group: {
      _id: null,
      totalGMV: { $sum: "$gmv" },
      totalBookings: { $sum: 1 }
    }
  }
])

// Resultado ejemplo:
{
  totalGMV: 45678.50,
  totalBookings: 234
}
```

---

## 🎓 Matriz de Decisión Completa

### PASO 1: Identificar si se menciona Partner o Shortage

```
¿La pregunta menciona Partner (Glovo, Uber, etc.) O Shortage?
│
├─ SÍ → Ir al PASO 2 (MongoDB bookings)
│
└─ NO → ¿Pregunta sobre productos/analytics?
         ├─ SÍ → MySQL (trends_consolidado, ventas_*)
         └─ NO → Pedir aclaración al usuario
```

### PASO 2: Determinar tipo de query en MongoDB

```
Menciona Partner/Shortage + ¿qué pregunta?
│
├─ GMV total del canal
│  Ejemplo: "GMV de Glovo última semana"
│  → MongoDB bookings WHERE creator = partner_id
│  → SUM(items[].pvp * quantity)
│
├─ Ventas de producto específico EN un canal
│  Ejemplo: "Ventas de Ibuprofeno en Glovo"
│  → MongoDB bookings WHERE creator = partner_id AND items contiene Ibuprofeno
│  → SUM(quantity) donde item.name = "Ibuprofeno"
│
├─ GMV de shortage
│  Ejemplo: "GMV de derivaciones última semana"
│  → MongoDB bookings WHERE origin EXISTS
│  → SUM(items[].pvp * quantity)
│
└─ Ventas de producto EN shortage
   Ejemplo: "Cuántas derivaciones de Paracetamol"
   → MongoDB bookings WHERE origin EXISTS AND items contiene Paracetamol
   → SUM(quantity) donde item.name = "Paracetamol"
```

### PASO 3: Casos Especiales

```
"Ventas totales de Ibuprofeno" (SIN mencionar canal)
→ MySQL trends_consolidado
→ Analytics generales de producto

"Comparar ventas de Ibuprofeno en Glovo vs shortage"
→ MongoDB bookings
→ Dos queries: una con creator = glovo, otra con origin EXISTS
→ Comparar resultados

"Productos más vendidos en Glovo"
→ MongoDB bookings WHERE creator = glovo
→ GROUP BY item.name
→ ORDER BY SUM(quantity) DESC
```

---

## 🎯 Reglas de Decisión Simplificadas

### Regla 1: Detección de Canal/Servicio
```
SI menciona (Glovo, Uber, Danone, Hartmann, Carrefour, shortage, derivación):
  → MongoDB bookings (operaciones por canal)

SI NO menciona ningún canal:
  → MySQL trends (analytics generales de producto)
```

### Regla 2: Producto + Canal
```
SI menciona PRODUCTO + CANAL:
  Ejemplo: "Ibuprofeno en Glovo"
  → MongoDB bookings (filtrar por canal Y producto)

SI menciona solo PRODUCTO:
  Ejemplo: "Ventas de Ibuprofeno"
  → MySQL trends_consolidado (analytics generales)
```

### Regla 3: GMV vs Producto
```
"GMV de X":
  → Si X es canal (Glovo, shortage) → MongoDB bookings
  → Si X es producto → MySQL trends

"Ventas de Y":
  → Si dice "en Z" (canal) → MongoDB bookings
  → Si no menciona canal → MySQL trends
```

---

## 📋 Lista Completa de Partners Conocidos

Estos valores están en `users.idUser`:

| idUser | Descripción |
|--------|-------------|
| `glovo` | Glovo estándar |
| `glovo-otc` | Glovo OTC |
| `uber` | Uber Eats |
| `danone` | Danone |
| `hartmann` | Hartmann |
| `procter` | Procter & Gamble |
| `procterclearblue` | Procter Clearblue |
| `trebol-miravia-lc` | Trébol/Miravia |
| `carrefour` | Carrefour |
| `arise` | Arise |
| `aliexpress` | AliExpress |
| `enna` | Enna |
| `nordic` | Nordic |
| `ludaalmacen` | Luda Almacén |

---

## 🔍 Anatomía de un Booking de Partner

```javascript
{
  _id: ObjectId("..."),
  creator: "5a123456789abcdef0123456",  // ObjectId del user (partner) como string
  target: "12345",  // Luda ID de la farmacia que recibe el pedido
  createdDate: ISODate("2025-01-15T10:30:00Z"),
  state: "5a54c525b2948c860f00000a",  // Estado del booking
  // state "5a54c525b2948c860f00000d" = CANCELADO

  items: [
    {
      pvp: 15.50,  // Precio unitario
      quantity: 2,  // Cantidad
      // GMV de este item = 15.50 * 2 = 31.00
    },
    {
      pvp: 8.75,
      quantity: 3,
      // GMV de este item = 8.75 * 3 = 26.25
    }
  ],
  // GMV total de este booking = 31.00 + 26.25 = 57.25

  origin: undefined  // Si está presente → es shortage, NO partner
}
```

### Distinción Importante:
- **Sin campo `origin`** → Booking de partner directo
- **Con campo `origin`** → Shortage (derivación entre farmacias)

---

## 📊 Ejemplos de Queries Reales

### Caso 1: GMV Total de un Canal (Partner)

**Pregunta**: "GMV de Glovo última semana"

**Análisis**:
- Menciona "Glovo" (partner) → MongoDB bookings
- Pide GMV total del canal → Sumar todos los bookings de ese partner
- No filtra por producto específico

**Query**:
```javascript
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

---

### Caso 2: Ventas de Producto EN un Canal

**Pregunta**: "Cuántas unidades de Ibuprofeno se vendieron en Glovo este mes"

**Análisis**:
- Menciona "Glovo" (partner) + "Ibuprofeno" (producto) → MongoDB bookings
- Filtrar por canal Y producto
- Contar unidades vendidas

**Query**:
```javascript
// Paso 1: Obtener ObjectId del partner
const glovoUser = db.users.findOne({ idUser: "glovo" });
const glovoId = glovoUser._id.toString();

// Paso 2: Filtrar bookings y buscar el producto
db.bookings.aggregate([
  {
    $match: {
      creator: glovoId,
      createdDate: {
        $gte: new Date("2025-01-01"),
        $lt: new Date("2025-02-01")
      },
      state: { $ne: "5a54c525b2948c860f00000d" },
      "items.name": { $regex: /ibuprofeno/i }  // Buscar en items
    }
  },
  {
    $unwind: "$items"
  },
  {
    $match: {
      "items.name": { $regex: /ibuprofeno/i }
    }
  },
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
      },
      totalBookings: { $sum: 1 }
    }
  }
]);

// Resultado:
// { totalUnidades: 450, totalGMV: 3500.50, totalBookings: 120 }
```

---

### Caso 3: GMV de Shortage (Derivaciones)

**Pregunta**: "GMV que generaron las derivaciones la última semana"

**Análisis**:
- Menciona "derivaciones" (shortage) → MongoDB bookings
- Identificador: bookings.origin EXISTS
- Calcular GMV de esos bookings

**Query**:
```javascript
db.bookings.aggregate([
  {
    $match: {
      origin: { $exists: true },  // Es shortage
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

### Caso 4: Producto EN Shortage

**Pregunta**: "Cuántas veces se derivó Paracetamol este mes"

**Análisis**:
- Menciona producto + derivaciones (shortage) → MongoDB bookings
- Filtrar: origin EXISTS + items contiene Paracetamol

**Query**:
```javascript
db.bookings.aggregate([
  {
    $match: {
      origin: { $exists: true },  // Es shortage
      createdDate: {
        $gte: new Date("2025-01-01"),
        $lt: new Date("2025-02-01")
      },
      state: { $ne: "5a54c525b2948c860f00000d" },
      "items.name": { $regex: /paracetamol/i }
    }
  },
  {
    $unwind: "$items"
  },
  {
    $match: {
      "items.name": { $regex: /paracetamol/i }
    }
  },
  {
    $group: {
      _id: null,
      totalUnidades: { $sum: { $toDouble: "$items.quantity" } },
      totalDerivaciones: { $sum: 1 }
    }
  }
]);
```

---

### Caso 5: Analytics General de Producto (SIN Canal)

**Pregunta**: "Ventas totales de Ibuprofeno el último mes"

**Análisis**:
- Menciona producto PERO NO menciona canal/shortage → MySQL trends
- Analytics generales sin filtro de canal
- Datos históricos consolidados

**Query**:
```sql
-- MySQL trends database
SELECT
    id_farmaco,
    nombre_producto,
    SUM(Ventas_promedio * 30) as ventas_ultimo_mes,
    AVG(Z_Y) as z_score,
    id_grupo as grupo_riesgo
FROM trends_consolidado
WHERE nombre_producto LIKE '%Ibuprofeno%'
GROUP BY id_farmaco, nombre_producto
ORDER BY ventas_ultimo_mes DESC;
```

**Diferencia clave**: Este query no sabe DÓNDE se vendieron (Glovo, shortage, etc.), solo el total general.

---

### Caso 6: Comparación Entre Canales

**Pregunta**: "Comparar ventas de Ibuprofeno en Glovo vs shortage"

**Análisis**:
- Menciona producto + múltiples canales → MongoDB bookings (2 queries)
- Necesito separar resultados por canal

**Query**:
```javascript
// Query 1: Ibuprofeno en Glovo
const glovoUser = db.users.findOne({ idUser: "glovo" });
const glovoId = glovoUser._id.toString();

const glovoSales = db.bookings.aggregate([
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
      _id: "Glovo",
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

// Query 2: Ibuprofeno en Shortage
const shortageSales = db.bookings.aggregate([
  {
    $match: {
      origin: { $exists: true },
      "items.name": { $regex: /ibuprofeno/i },
      state: { $ne: "5a54c525b2948c860f00000d" }
    }
  },
  { $unwind: "$items" },
  { $match: { "items.name": { $regex: /ibuprofeno/i } } },
  {
    $group: {
      _id: "Shortage",
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

// Combinar resultados:
// Glovo: { totalUnidades: 450, totalGMV: 3500.50 }
// Shortage: { totalUnidades: 120, totalGMV: 950.00 }
```

---

### Ejemplo 1: GMV de Glovo última semana
```javascript
// 1. Obtener ObjectId
const glovoUser = db.users.findOne({ idUser: "glovo" });
const glovoId = glovoUser._id.toString();

// 2. Calcular GMV
db.bookings.aggregate([
  {
    $match: {
      creator: glovoId,
      createdDate: {
        $gte: new Date("2025-01-01"),
        $lte: new Date("2025-01-07")
      },
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

### Ejemplo 2: Comparar GMV de todos los partners este mes
```javascript
// 1. Obtener todos los partners
const partners = db.users.find(
  { idUser: { $in: ["glovo", "uber", "danone", "carrefour"] } },
  { _id: 1, idUser: 1 }
).toArray();

// Crear mapa de ObjectId → nombre
const partnerMap = {};
partners.forEach(p => {
  partnerMap[p._id.toString()] = p.idUser;
});

// 2. Agrupar bookings por creator
db.bookings.aggregate([
  {
    $match: {
      creator: { $in: Object.keys(partnerMap) },
      createdDate: {
        $gte: new Date("2025-01-01"),
        $lt: new Date("2025-02-01")
      },
      state: { $ne: "5a54c525b2948c860f00000d" }
    }
  },
  {
    $project: {
      creator: 1,
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
      _id: "$creator",
      totalGMV: { $sum: "$gmv" },
      totalBookings: { $sum: 1 }
    }
  },
  {
    $sort: { totalGMV: -1 }
  }
]);

// Resultado ejemplo:
[
  { _id: "5a123...", totalGMV: 125000.50, totalBookings: 450 },  // Glovo
  { _id: "5a456...", totalGMV: 89000.25, totalBookings: 320 },   // Uber
  { _id: "5a789...", totalGMV: 45000.00, totalBookings: 150 },   // Danone
  ...
]
```

### Ejemplo 3: GMV de Uber incluyendo cancelados (para análisis)
```javascript
const uberUser = db.users.findOne({ idUser: "uber" });

db.bookings.aggregate([
  {
    $match: {
      creator: uberUser._id.toString(),
      createdDate: {
        $gte: new Date("2025-01-01"),
        $lte: new Date("2025-01-31")
      }
    }
  },
  {
    $project: {
      isCancelled: {
        $eq: ["$state", "5a54c525b2948c860f00000d"]
      },
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
      completedGMV: {
        $sum: {
          $cond: [{ $eq: ["$isCancelled", false] }, "$gmv", 0]
        }
      },
      cancelledGMV: {
        $sum: {
          $cond: [{ $eq: ["$isCancelled", true] }, "$gmv", 0]
        }
      },
      totalBookings: { $sum: 1 },
      completedBookings: {
        $sum: { $cond: [{ $eq: ["$isCancelled", false] }, 1, 0] }
      },
      cancelledBookings: {
        $sum: { $cond: [{ $eq: ["$isCancelled", true] }, 1, 0] }
      }
    }
  }
]);

// Resultado ejemplo:
{
  totalGMV: 95000.00,
  completedGMV: 89000.25,
  cancelledGMV: 5999.75,
  totalBookings: 330,
  completedBookings: 320,
  cancelledBookings: 10
}
```

---

## 🎯 Casos de Prueba para Validación

Use estos casos para verificar que el modelo entiende el patrón:

### Test 1: GMV de Canal (Partner)
**Pregunta**: "¿Cuánto GMV ha generado Glovo este mes?"
- ✅ **Correcto**: MongoDB → users + bookings (filtrar por creator)
- ❌ **Incorrecto**: MySQL → ventas_*

**Razón**: Glovo es un canal de venta, no un producto

### Test 2: GMV de Shortage
**Pregunta**: "GMV de derivaciones la última semana"
- ✅ **Correcto**: MongoDB → bookings WHERE origin EXISTS
- ❌ **Incorrecto**: MySQL o buscar por "shortage" como partner

**Razón**: Shortage se identifica por campo `origin`, no por `creator`

### Test 3: Producto EN Canal
**Pregunta**: "Ventas de Ibuprofeno en Glovo este mes"
- ✅ **Correcto**: MongoDB → bookings WHERE creator = glovo AND items contiene Ibuprofeno
- ❌ **Incorrecto**: MySQL trends_consolidado

**Razón**: Menciona Glovo (canal) → siempre MongoDB, aunque pregunte por producto

### Test 4: Producto EN Shortage
**Pregunta**: "Cuántas unidades de Paracetamol se derivaron"
- ✅ **Correcto**: MongoDB → bookings WHERE origin EXISTS AND items contiene Paracetamol
- ❌ **Incorrecto**: MySQL o búsqueda sin filtro origin

**Razón**: Derivaciones = shortage = origin EXISTS

### Test 5: Producto SIN Mencionar Canal
**Pregunta**: "Ventas totales de Ibuprofeno"
- ✅ **Correcto**: MySQL → trends_consolidado
- ❌ **Incorrecto**: MongoDB bookings sin filtro de canal

**Razón**: NO menciona Glovo/Uber/shortage → analytics general → MySQL

### Test 6: Distinción Partner vs Producto
**Pregunta A**: "¿Cuánto GMV tiene Ibuprofeno?"
- → MySQL (producto farmacéutico, analytics general)

**Pregunta B**: "¿Cuánto GMV tiene Danone?"
- → MongoDB (partner/canal de venta)

**Pregunta C**: "¿Cuánto Ibuprofeno se vendió en Danone?"
- → MongoDB (producto EN canal)

### Test 7: Comparación Entre Canales
**Pregunta**: "Comparar ventas de Aspirina en Glovo vs shortage"
- ✅ **Correcto**: 2 queries MongoDB:
  1. WHERE creator = glovo AND items contiene Aspirina
  2. WHERE origin EXISTS AND items contiene Aspirina
- ❌ **Incorrecto**: Una sola query o usar MySQL

### Test 8: Productos Más Vendidos EN Canal
**Pregunta**: "Top 10 productos en Uber Eats"
- ✅ **Correcto**: MongoDB → bookings WHERE creator = uber, GROUP BY item.name
- ❌ **Incorrecto**: MySQL trends_consolidado

**Razón**: Menciona Uber Eats (canal específico)

---

## 📝 Checklist de Validación

Antes de ejecutar una query, verificar:

### Para Queries de Canal/Partner:
- [ ] Identificaste que se menciona un CANAL (Glovo, Uber, etc.) o SHORTAGE
- [ ] Decidiste usar MongoDB bookings (NO MySQL)
- [ ] Si es partner: vas a buscar en `users` primero para obtener ObjectId
- [ ] Si es shortage: usarás filtro `origin: { $exists: true }`
- [ ] Si pregunta por producto EN canal: filtrarás por canal Y producto
- [ ] Calcularás GMV sumando `items[].pvp * items[].quantity`
- [ ] Filtrarás por fecha usando `createdDate`
- [ ] Consideraste excluir cancelados (`state != "5a54c525b2948c860f00000d"`)

### Para Analytics Generales de Producto:
- [ ] Verificaste que NO se menciona canal/shortage
- [ ] Decidiste usar MySQL trends_consolidado
- [ ] La pregunta es sobre analytics generales (no por canal específico)
- [ ] NO estás mezclando datos de MySQL y MongoDB

---

## 🚨 Errores Comunes a Evitar

1. **Confundir partners con productos**
   - ❌ "Glovo es un producto" → ✅ "Glovo es un partner/user"

2. **Buscar partners en MySQL**
   - ❌ `SELECT * FROM ventas WHERE proveedor = 'Glovo'`
   - ✅ MongoDB users + bookings

3. **Olvidar el paso de users**
   - ❌ Buscar directamente `bookings.creator = "glovo"`
   - ✅ Primero encontrar ObjectId en users.idUser

4. **Mal cálculo de GMV**
   - ❌ Solo sumar `bookings.total`
   - ✅ Sumar `items[i].pvp * items[i].quantity` de cada item

5. **Olvidar excluir cancelados**
   - ❌ Incluir todos los bookings
   - ✅ Filtrar `state != "5a54c525b2948c860f00000d"` (a menos que se solicite explícitamente)

6. **Formato de ObjectId**
   - ❌ `creator: ObjectId("5a123...")`
   - ✅ `creator: "5a123..."` (string en bookings)

---

## 🎓 Resumen Final

### MySQL (trends) es para:
- **Productos farmacéuticos** (analytics generales)
- **Analytics históricos de ventas** (SIN especificar canal)
- **Trends de demanda** y predicciones
- **Cazador** (oportunidades de mercado)
- **Z_Y scores** y grupos de riesgo
- **Performance de productos** (sin filtro de canal)

**Uso**: Cuando NO se menciona Glovo, Uber, shortage u otro canal específico

### MongoDB (ludafarma) es para:
- **Canales de venta** (Partners: Glovo, Uber, Danone, etc.)
- **Shortage** (servicio de derivación entre farmacias)
- **GMV de canales** específicos
- **Ventas de productos EN un canal** ("Ibuprofeno en Glovo")
- **Bookings operacionales** por canal
- **Catálogo actual** y stock en tiempo real
- **Usuarios y farmacias**

**Uso**: Cuando SE menciona Glovo, Uber, shortage, derivaciones, o cualquier canal

---

## 🎯 Preguntas Clave para Decidir

### Pregunta 1:
**"¿Se menciona Glovo, Uber, Danone, Carrefour, shortage o derivaciones?"**
- ✅ **SÍ** → MongoDB bookings
- ❌ **NO** → Ir a Pregunta 2

### Pregunta 2:
**"¿Pregunta por analytics general de un producto (sin mencionar dónde se vendió)?"**
- ✅ **SÍ** → MySQL trends_consolidado
- ❌ **NO** → Pedir aclaración al usuario

### Pregunta 3 (si menciona canal + producto):
**"¿Dice 'Ibuprofeno EN Glovo' o similar?"**
- ✅ **SÍ** → MongoDB bookings (filtrar por canal Y producto)
- ❌ Solo canal sin producto → MongoDB bookings (GMV total del canal)
- ❌ Solo producto sin canal → MySQL trends_consolidado

---

## 📌 Regla de Oro Simplificada

```
MENCIONA CANAL/SHORTAGE → MongoDB bookings
NO MENCIONA CANAL      → MySQL trends_consolidado

Canales: Glovo, Uber, Danone, Hartmann, Carrefour, shortage, derivación
```

---

## 💡 Conceptos Críticos

1. **Glovo NO es un comprador** → Es un CANAL de venta (marketplace)
2. **Shortage NO es un partner** → Es servicio de derivación (identificado por `origin`)
3. **"Ventas en Glovo"** → MongoDB (especifica canal)
4. **"Ventas de producto"** → MySQL (general, sin canal)
5. **Partners crean bookings** → `bookings.creator` = ObjectId del partner
6. **Shortage tiene origin** → `bookings.origin` EXISTS
7. **GMV se calcula de items** → `SUM(pvp * quantity)` no de totales

---

*Este documento debe ser usado para entrenar y validar que ChatGPT entiende correctamente el patrón de routing para queries de GMV de canales, shortage y productos.*
