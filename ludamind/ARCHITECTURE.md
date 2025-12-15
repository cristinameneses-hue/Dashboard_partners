# 🏗️ ARQUITECTURA - LUDA MIND

**Versión:** 4.4.0  
**Fecha:** 20 Noviembre 2024

---

## 📊 Visión General

Luda Mind utiliza **Clean Architecture** con separación clara en 3 capas:
- **Domain**: Lógica de negocio pura
- **Infrastructure**: Implementaciones técnicas
- **Presentation**: Interfaces de usuario y API

---

## 🎯 Arquitectura del Sistema

```
┌─────────────────────────────────────────────────────────────┐
│                      FRONTEND                                │
│  index_luda_mind_v2.html + Markdown Rendering               │
└──────────────────────────┬──────────────────────────────────┘
                           │
                           v
┌─────────────────────────────────────────────────────────────┐
│                    PRESENTATION LAYER                        │
│                  app_luda_mind.py (Flask)                    │
│                                                               │
│  ┌─────────────────────────────────────────────────┐        │
│  │           MODO HÍBRIDO                           │        │
│  ├─────────────────────────────────────────────────┤        │
│  │  if conversational → SmartProcessor            │        │
│  │  elif is_predefined → Hardcoded (optimized)    │        │
│  │  else → SmartProcessor (semantic)              │        │
│  └─────────────────────────────────────────────────┘        │
└──────────────────────────┬──────────────────────────────────┘
                           │
          ┌────────────────┴────────────────┐
          v                                  v
┌─────────────────────┐         ┌─────────────────────┐
│  HARDCODED LOGIC    │         │  SMART PROCESSOR     │
│  (Optimized)        │         │  (Semantic)          │
│                     │         │                      │
│  • process_pharmacy │         │  • semantic_mapping  │
│  • process_product  │         │  • query_interpreter │
│  • process_partner  │         │  • GPT-4o-mini       │
└──────────┬──────────┘         └──────────┬───────────┘
           │                               │
           └───────────┬───────────────────┘
                       v
┌─────────────────────────────────────────────────────────────┐
│                    DOMAIN LAYER                              │
│                                                               │
│  Entities: Query, QueryMode, Conversation, User             │
│  Services: QueryRouter, ContextService                       │
│  Use Cases: ExecuteQuery, StreamingQuery                    │
│  Knowledge: semantic_mapping.py (18 campos)                 │
└──────────────────────────┬──────────────────────────────────┘
                           │
                           v
┌─────────────────────────────────────────────────────────────┐
│                 INFRASTRUCTURE LAYER                         │
│                                                               │
│  Repositories: MongoDB, MySQL, OpenAI                       │
│  Services: ConnectionFactory, PromptManager                  │
│  Bootstrap: Inicialización, Health Checks                   │
│  DI Container: Dependency Injection                         │
└──────────────────────────┬──────────────────────────────────┘
                           │
          ┌────────────────┴────────────────┐
          v                                  v
┌─────────────────────┐         ┌─────────────────────┐
│     MONGODB         │         │     MYSQL            │
│  LudaFarma-PRO      │         │  trends_consolidado  │
│                     │         │                      │
│  • pharmacies       │         │  • Sell In           │
│  • items            │         │  • Sell Out          │
│  • bookings         │         │  (Solo reportes)     │
│  • stockItems       │         │                      │
│  • thirdUsers       │         │                      │
└─────────────────────┘         └─────────────────────┘
```

---

## 🧠 Sistema de Interpretación Semántica

### Diccionario Semántico

**18 campos mapeados** con:
- Field path (ej: `thirdUser.user`)
- Keywords (ej: "partner", "canal", "marketplace")
- Synonyms (ej: "glovo", "uber")
- Aggregation hints (ej: "$group by")
- Business context

### Query Interpreter

Usa GPT-4o-mini con:
- Contexto semántico enriquecido
- Mappings detectados automáticamente
- Patterns de agregación sugeridos
- Explicaciones en lenguaje natural

### Smart Query Processor

Orquesta:
1. Detección de campos relevantes
2. Interpretación con GPT
3. Ejecución en MongoDB
4. Formateo de respuesta

---

## 📚 Estructura de Datos MongoDB

### Farmacias (pharmacies)
```javascript
{
    _id: ObjectId,
    description: "FARMACIA NOMBRE",      // Nombre
    active: 1,                            // 1=activa, 0=inactiva
    contact: {
        city: "Madrid",                   // Ciudad
        postalCode: "28010",              // CP
        address: "Calle X, 123"           // Dirección
    }
}
```

### Productos (items)
```javascript
{
    _id: ObjectId,
    description: "NATALBEN SUPRA...",    // Nombre
    code: "154653",                       // CN (6 dígitos, STRING)
    ean13: "8470001546531",              // EAN (13 dígitos, STRING)
    active: 1,                            // 1=activo, 0=inactivo
    itemType: 3                           // 3=parafarmacia, otro=medicamento
}
```

### Pedidos (bookings)
```javascript
{
    _id: ObjectId,
    createdDate: ISODate,
    target: "pharmacy_id",               // Farmacia destino
    origin: "pharmacy_id",               // Si existe = shortage
    
    thirdUser: {                          // Si existe = pedido partner
        user: "glovo",                    // Partner
        price: 48.70                      // GMV (si existe)
    },
    
    items: [
        {
            description: "...",
            code: "154653",
            ean13: "...",
            pvp: 20.10,
            quantity: 1
        }
    ]
}
```

### Stock (stockItems)
```javascript
{
    pharmacyId: "...",                   // STRING (no ObjectId)
    itemId: "...",                       // STRING (no ObjectId)
    code: "154653",
    quantity: 2,
    pvp: 20.00,                          // Precio público
    pva: 14.48                           // Precio almacén
}
```

---

## 💰 Lógica de Negocio

### Cálculo de GMV (Híbrido)

```python
if booking.thirdUser and booking.thirdUser.price:
    gmv = thirdUser.price
else:
    gmv = sum(item.pvp * item.quantity for item in booking.items)
```

### Tipos de Bookings

1. **Ecommerce** (pedidos de partners):
   - Tienen `thirdUser.user`
   - GMV calculado con método híbrido
   
2. **Shortage** (transferencias internas):
   - Tienen `origin` (farmacia origen)
   - GMV calculado desde items
   - NO tienen thirdUser

### Separación en Reportes

```
GMV Total:
• GMV Ecommerce: €111,580
• GMV Shortage: €77,413
• TOTAL: €188,993
```

---

## 🤝 Partners Activos (12)

### Delivery/Marketplace (6)
- glovo (mayor volumen)
- glovo-otc
- uber
- justeat
- carrefour
- amazon

### Labs Corporativos (6)
- danone
- procter
- enna
- nordic
- chiesi
- ferrer

**Campo:** `thirdUsers.idUser` = `bookings.thirdUser.user`

---

## 🔄 Flujo de Query

```
1. Usuario escribe query
   ↓
2. Sistema detecta modo (pharmacy/product/partner/conversational)
   ↓
3. is_predefined_query()?
   ├─ SÍ → Lógica optimizada (hardcoded)
   └─ NO → SmartQueryProcessor
          ├─ Detecta campos (semantic_mapping)
          ├─ Interpreta con GPT
          ├─ Genera aggregation MongoDB
          └─ Ejecuta y formatea
   ↓
4. Respuesta en Markdown
   ↓
5. marked.js → HTML elegante
   ↓
6. Usuario ve respuesta formateada
```

---

## 🎨 Frontend

### Componentes
- Sidebar: Modos + Historial (localStorage)
- Dropdown: Ejemplos por modo
- Chat: Mensajes con markdown rendering
- Input: Textarea con enter-to-send

### Estilos
- Color verde corporativo (#41A837)
- Logo LUDA horizontal
- Markdown CSS completo
- Responsive design

---

## 🔧 Configuración

### Variables de Entorno (.env)

```env
# MongoDB (Principal)
MONGO_LUDAFARMA_URL=mongodb://...

# MySQL (Solo sell in/sell out)
MYSQL_HOST=127.0.0.1
MYSQL_PORT=3307
MYSQL_USER=...
MYSQL_PASS=...
MYSQL_DB=trends_consolidado

# OpenAI
OPENAI_API_KEY=sk-proj-...
OPENAI_MODEL=gpt-4o-mini
```

### Puertos
- **Web**: 5000 (Flask)
- **MySQL**: 3307 (túnel SSH)
- **MongoDB**: 27017 (túnel SSH)

---

## 📈 Performance

### Modo Híbrido
- Queries predefinidas: ~100ms (hardcoded)
- Queries semánticas: ~500ms (incluye GPT)
- Conversacionales: ~800ms (análisis complejo)

### Optimizaciones
- Conexiones pooled a MongoDB
- Caché de queries frecuentes (futuro)
- Límites en agregaciones (100-1000 docs)

---

## 🔐 Seguridad

### Implementado
- ✅ Credenciales en `.env` (nunca hardcodeadas)
- ✅ Queries parametrizadas
- ✅ Validación de inputs
- ✅ Pre-commit hooks
- ✅ Límites de resultados
- ✅ READ-ONLY por defecto

### Pre-commit Hooks
- Detecta credenciales hardcodeadas
- Valida sintaxis Python
- Formatea con Black
- Type checking con MyPy
- Security scan con Bandit

---

## 🧪 Testing

### E2E Test
```bash
python tests/e2e_test_modes.py
```

### Test Template
```bash
# Usar tests/test_template.py como base
```

### Integration Tests
```bash
python tests/integration/test_critical_paths.py
```

---

## 📚 Más Documentación

Ver carpeta `/docs/` para:
- Diccionario semántico completo
- Configuración de base de datos
- Arquitectura de agentes
- Partners activos
- Lógica de GMV
- Changelog histórico

---

**Luda Mind - Clean Architecture con interpretación semántica inteligente 💚**
