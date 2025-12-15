/**
 * Unified Database Context Generator
 *
 * Generates context for LLMs to decide between MySQL and MongoDB
 */

import * as fs from "fs";
import * as path from "path";
import { fileURLToPath } from "url";

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

/**
 * Database routing rules
 */
export const DATABASE_ROUTING_RULES = `
# 🎯 Database Routing Rules

## When to Use MySQL (trends database)

Use MySQL for queries related to:

### Sales and Analytics
- ✅ **Ventas** (sales data, historical sales)
- ✅ **Trends** (product trends, demand predictions)
- ✅ **Cazador** (hunter system, opportunity detection)
- ✅ **Stock analysis** (inventory trends over time)
- ✅ **Z_Y scores** (product risk metrics)
- ✅ **Grupos de riesgo** (risk groups 1-4)
- ✅ **Bookings analytics** (booking statistics and trends)
- ✅ **Product performance** (best sellers, slow movers)

### Keywords that indicate MySQL:
- "ventas", "sales", "sold"
- "trends", "tendencias", "demand", "demanda"
- "cazador", "hunter", "opportunities", "oportunidades"
- "Z_Y", "z-score", "riesgo", "risk group", "grupo"
- "performance", "rendimiento", "análisis"
- "predicción", "prediction", "forecast"

### Example MySQL Queries:
- "¿Cuáles son los productos más vendidos?"
- "Productos en grupo de riesgo 3"
- "Análisis de ventas del último mes"
- "Productos con Z_Y menor a -0.30"
- "Bookings totales esta semana"

---

## When to Use MongoDB (ludafarma database)

Use MongoDB for queries related to:

### Core Operations
- ✅ **Catálogo de productos** (items, eans, itemPrices, vademecum)
- ✅ **Farmacias** (pharmacies, allpharmacies, itemPharmacies)
- ✅ **Usuarios** (users, userNotifications, thirdUsers)
- ✅ **Reservas y derivaciones** (bookings, bookingRequests, bookingCancelations)
- ✅ **Stock en tiempo real** (stockItems, stockEvents)
- ✅ **Pagos y facturación** (payments, invoices, billings, accountingEntries)
- ✅ **Notificaciones** (notifications, alerts, firebaseTokens)
- ✅ **eCommerce y delivery** (deliveryEvents, providers)
- ✅ **Auditoría** (auditEvents, connectionEvents)
- ✅ **Partners y GMV** (bookings.creator + users.idUser para Glovo, Uber, etc.)

### Keywords that indicate MongoDB:
- "farmacia", "pharmacy", "pharmacies"
- "usuario", "user", "users"
- "reserva", "booking", "derivación"
- "catálogo", "catalog", "producto actual"
- "stock actual", "current stock" (not trends)
- "pago", "payment", "factura", "invoice"
- "notificación", "notification", "alert"
- "delivery", "envío", "pedido"
- "audit", "auditoría", "log"
- "partner", "proveedor", "glovo", "uber", "danone", "hartmann", "carrefour"
- "GMV de partner/proveedor" (GMV by delivery provider)

### Example MongoDB Queries:
- "¿Cuántas farmacias tenemos activas?"
- "Usuarios registrados en el último mes"
- "Reservas pendientes hoy"
- "Stock actual del producto X en la farmacia Y"
- "Pagos procesados esta semana"
- "Productos en el catálogo con precio > 50€"
- "GMV que se ha movido en Glovo la última semana"
- "Pedidos totales de Uber este mes"

---

## Decision Algorithm

\`\`\`
IF query contains ("ventas" OR "trends" OR "cazador" OR "Z_Y" OR "grupo de riesgo" OR "analytics"):
    → USE MySQL
ELSE IF query contains ("farmacia" OR "usuario" OR "booking" OR "catálogo" OR "pago" OR "notificación"):
    → USE MongoDB
ELSE:
    → ASK USER for clarification
\`\`\`

---

## Important Notes

1. **MySQL = Historical Analytics** (what happened, predictions)
2. **MongoDB = Current Operations** (what's happening now, transactions)
3. **When in doubt**, ask the user which system they want to query
4. **Never query both** databases for a single question (choose one)
5. **Product data exists in BOTH**:
   - MongoDB: Current catalog, prices, availability
   - MySQL: Sales history, trends, performance

---

## 🎯 SPECIAL CASE: Partners GMV Queries

**CRITICAL**: When querying GMV/sales for delivery partners (Glovo, Uber, etc.), ALWAYS use MongoDB, NOT MySQL.

### Why MongoDB for Partners GMV?

Partners like Glovo, Uber, Danone, etc. create bookings directly through the system. The GMV is stored in:
- **Collection**: \`bookings\`
- **Partner identification**: \`bookings.creator\` (ObjectId) → \`users._id\` where \`users.idUser\` = "glovo", "uber", etc.
- **GMV calculation**: \`SUM(items[].pvp * items[].quantity)\` for all bookings by that partner

### Known Partners (users.idUser):
- "glovo" → Glovo standard
- "glovo-otc" → Glovo OTC
- "uber" → Uber Eats
- "danone" → Danone
- "hartmann" → Hartmann
- "procter" → Procter & Gamble
- "procterclearblue" → Procter Clearblue
- "trebol-miravia-lc" → Trébol/Miravia
- "carrefour" → Carrefour
- "arise" → Arise
- "aliexpress" → AliExpress
- "enna" → Enna
- "nordic" → Nordic
- "ludaalmacen" → Luda Almacén

### Query Pattern for Partners GMV:

**Step 1**: Get partner's ObjectId from users
\`\`\`javascript
db.users.findOne({ idUser: "glovo" }, { _id: 1 })
// Result: { _id: ObjectId("...") }
\`\`\`

**Step 2**: Aggregate bookings by that creator
\`\`\`javascript
db.bookings.aggregate([
  {
    $match: {
      creator: "5a123456789...",  // ObjectId as string
      createdDate: {
        $gte: new Date("2025-01-01"),
        $lte: new Date("2025-01-07")
      },
      state: { $ne: "5a54c525b2948c860f00000d" }  // Exclude cancelled
    }
  },
  {
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
    $group: {
      _id: null,
      totalGMV: { $sum: "$gmv" },
      totalBookings: { $sum: 1 }
    }
  }
])
\`\`\`

### Important Fields:
- \`bookings.creator\`: Partner's user ObjectId (string format)
- \`bookings.createdDate\`: Creation timestamp
- \`bookings.state\`: "5a54c525b2948c860f00000d" = cancelled
- \`bookings.items[]\`: Array with \`pvp\` (price) and \`quantity\`
- \`bookings.origin\`: If present → shortage (not partner booking)

### Decision Logic:
\`\`\`
IF query mentions (Glovo, Uber, Danone, Hartmann, Carrefour, etc.) + (GMV, ventas, pedidos):
    → MongoDB \`bookings\` collection
    → Join with \`users\` via \`creator\` → \`_id\`
    → Calculate GMV from \`items\`
    → NEVER use MySQL for this
\`\`\`
`;

/**
 * MongoDB collections summary (from documentation)
 */
export const MONGODB_COLLECTIONS_SUMMARY = `
# 📊 MongoDB Database - LudaFarma PRO

## Total Collections: 123
## Total Documents: 60+ million

### Main Categories:

#### 1. Catálogo de Productos (Product Catalog)
- \`items\` (705,487 docs) - Main product catalog
- \`eans\` (363,040 docs) - EAN/barcode references
- \`itemPrices\` (801,105 docs) - Product pricing
- \`autocompleteItems\` (257,486 docs) - Search autocomplete
- \`vademecum\` (24,675 docs) - Drug information

#### 2. Farmacias (Pharmacies)
- \`pharmacies\` (4,831 docs) - Active pharmacies
- \`allpharmacies\` (2,874 docs) - All pharmacies (including inactive)
- \`itemPharmacies\` (229,039 docs) - Products per pharmacy
- \`pharmacyEvents\` (74,952 docs) - Pharmacy events

#### 3. Stock Gestión
- \`stockItems\` (20,106,557 docs) - Stock records
- \`stockEvents-YYYYMMDD\` (44,399 docs) - Daily stock events
- \`stockEventsAnalysis\` (1,844,777 docs) - Stock analysis
- \`auxStockItemsRequest\` (1,278,184 docs) - Stock requests

#### 4. Reservas y Derivaciones (Bookings)
- \`bookings\` (1,230,131 docs) - Confirmed bookings
- \`bookingRequests\` (1,245,849 docs) - Booking requests
- \`bookingCancelations\` (116,270 docs) - Cancelled bookings

#### 5. Usuarios (Users)
- \`users\` (11,628 docs) - Registered users
- \`userNotifications\` (9,802 docs) - User notifications
- \`thirdUsers\` (32 docs) - Third-party users

#### 6. Pagos y Facturación (Payments)
- \`payments\` (5,555 docs) - Payment records
- \`invoices\` (209,294 docs) - Invoices
- \`accountingEntries\` (904,937 docs) - Accounting entries
- \`billings\` (2,575 docs) - Billing information

#### 7. Notificaciones (Notifications)
- \`notifications\` (1,496,143 docs) - System notifications
- \`alerts\` (2,903,007 docs) - User alerts
- \`publicAlerts\` (206,524 docs) - Public alerts

#### 8. eCommerce y Delivery
- \`deliveryEvents\` (2,737,136 docs) - Delivery tracking
- \`providers\` (9 docs) - Delivery providers

#### 9. Auditoría (Audit)
- \`auditEvents\` (8,177,538 docs) - Audit log
- \`connectionEvents\` (342,168 docs) - Connection logs
`;

/**
 * MySQL database summary
 */
export const MYSQL_DATABASE_SUMMARY = `
# 📊 MySQL Database - TrendsPro

## Main Tables: 109

### Core Analytics Tables:

#### trends_consolidado
Main table for product analytics and trends
- \`id_farmaco\` - Product ID
- \`id_grupo\` - Risk group (1-4)
- \`Z_Y\` - Z-score metric (risk indicator)
- \`Booking_total\` - Total bookings
- \`Ventas_promedio\` - Average sales
- \`Stock\` - Current stock level

#### cazador_* tables
Hunter system for opportunity detection
- Product opportunities
- Price analysis
- Market gaps

#### ventas_* tables
Sales historical data
- Daily sales records
- Sales by pharmacy
- Sales by product

#### api_pharmacies
Pharmacy configuration for automated purchasing
- Active/inactive status
- Hunter settings
- Filters and parameters
`;

/**
 * Generate full unified context
 */
export function generateUnifiedDatabaseContext(): string {
  return `
${DATABASE_ROUTING_RULES}

${MYSQL_DATABASE_SUMMARY}

${MONGODB_COLLECTIONS_SUMMARY}

---

## How to Query

### MySQL Example:
\`\`\`sql
SELECT id_farmaco, Ventas_promedio, Z_Y
FROM trends_consolidado
WHERE id_grupo = 3
LIMIT 10
\`\`\`

### MongoDB Example:
\`\`\`javascript
db.pharmacies.find({ active: true }).limit(10)
// Or using the API:
{ collection: "pharmacies", query: { active: true }, limit: 10 }
\`\`\`

---

## Remember:
1. **Always choose ONE database per query**
2. **Use routing rules to decide**
3. **MySQL = Analytics & Trends**
4. **MongoDB = Current Operations**
`;
}

/**
 * Load MongoDB documentation if available
 */
export function loadMongoDBDocumentation(): string | null {
  try {
    const docPath = path.join(__dirname, "../../MONGODB_DOCUMENTATION_MASTER.md");

    if (fs.existsSync(docPath)) {
      return fs.readFileSync(docPath, "utf-8");
    }

    return null;
  } catch (error) {
    console.error("Error loading MongoDB documentation:", error);
    return null;
  }
}

/**
 * Get routing decision prompt for LLM
 */
export function getDatabaseRoutingPrompt(userQuery: string): string {
  return `
Given the user query: "${userQuery}"

Analyze the query and decide which database to use based on these rules:

${DATABASE_ROUTING_RULES}

Your decision:
1. Database to use: [MySQL or MongoDB]
2. Reason: [Brief explanation why]
3. Query to execute: [SQL for MySQL or MongoDB query object]

Remember:
- MySQL is for: ventas, trends, cazador, analytics, predictions
- MongoDB is for: farmacias, usuarios, bookings, catálogo, pagos, current operations
`;
}
