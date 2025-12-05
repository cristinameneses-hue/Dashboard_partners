# Dashboard Partners - LudaFarma

Dashboard web para visualizar métricas de partners de LudaFarma, con arquitectura de tres capas y principios SOLID.

## Arquitectura

```
┌─────────────────────────────────────────────────────────────┐
│                   CAPA DE PRESENTACIÓN                      │
│                      (React + Vite)                         │
│  - Vista Ecommerce (métricas por partner)                   │
│  - Vista Shortage (métricas globales)                       │
│  - Selector de períodos temporales                          │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                CAPA DE LÓGICA DE NEGOCIO                    │
│                       (FastAPI)                             │
│  - EcommerceService (métricas de partners)                  │
│  - ShortageService (métricas de transferencias)             │
│  - Cálculo de KPIs derivados                                │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                 CAPA DE ACCESO A DATOS                      │
│                   (Motor + MongoDB)                         │
│  - BookingRepository (queries de bookings)                  │
│  - PharmacyRepository (queries de farmacias)                │
│  - Conexión a LudaFarma-PRO                                 │
└─────────────────────────────────────────────────────────────┘
```

## Métricas

### Ecommerce (por Partner)

| Métrica | Descripción |
|---------|-------------|
| Gross Bookings | Total de pedidos |
| Cancelled Bookings | Pedidos cancelados |
| Net Bookings | Gross - Cancelled |
| Gross GMV | Valor total (items.pvp * quantity) |
| Cancelled GMV | GMV de cancelados |
| Net GMV | Gross GMV - Cancelled GMV |
| Average Ticket | Net GMV / Net Bookings |
| Avg Orders/Pharmacy | Net Bookings / farmacias únicas |
| Avg GMV/Pharmacy | Net GMV / farmacias únicas |
| % Cancelled Bookings | (Cancelled / Gross) * 100 |
| % Cancelled GMV | (Cancelled GMV / Gross GMV) * 100 |
| % Active Pharmacies | Farmacias con pedidos / Farmacias con tag |

### Shortage (Global)

Mismas métricas que Ecommerce más:

| Métrica | Descripción |
|---------|-------------|
| Active Pharmacies | Farmacias con active=1 |
| Sending Pharmacies | Farmacias que han enviado (origin) |
| Receiving Pharmacies | Farmacias que han recibido (target) |

## Períodos Temporales

- This Year / Last Year
- This Month / Last Month
- This Week / Last Week
- Q1, Q2, Q3, Q4 (año actual)
- Custom (fecha inicio - fecha fin)

## Partners (12)

**Delivery/Marketplace:** glovo, glovo-otc, uber, justeat, amazon, carrefour

**Labs Corporativos:** danone, procter, enna, nordic, chiesi, ferrer

> **Nota:** uber y justeat no tienen tags de farmacias, por lo que `% Active Pharmacies` no está disponible para ellos.

## Requisitos

- Python 3.10+
- Node.js 18+
- MongoDB (LudaFarma-PRO)

## Instalación

### Backend

```bash
cd backend
python -m venv venv

# Windows
venv\Scripts\activate

# Linux/Mac
source venv/bin/activate

pip install -r requirements.txt
```

### Frontend

```bash
cd frontend
npm install
```

## Ejecución

### Backend

```bash
cd backend
uvicorn app.main:app --reload --port 8000
```

API disponible en: http://localhost:8000/docs

### Frontend

```bash
cd frontend
npm run dev
```

Dashboard disponible en: http://localhost:5173

## API Endpoints

### Ecommerce

| Método | Endpoint | Descripción |
|--------|----------|-------------|
| GET | `/api/ecommerce` | Métricas de todos los partners |
| GET | `/api/ecommerce/partners` | Lista de partners disponibles |
| GET | `/api/ecommerce/partner/{partner}` | Métricas de un partner específico |

### Shortage

| Método | Endpoint | Descripción |
|--------|----------|-------------|
| GET | `/api/shortage` | Métricas globales de shortages |

### Pharmacies

| Método | Endpoint | Descripción |
|--------|----------|-------------|
| GET | `/api/pharmacies/count/active` | Total farmacias activas |
| GET | `/api/pharmacies/distribution/province` | Distribución por provincia |
| GET | `/api/pharmacies/distribution/partner` | Distribución por partner |

## Parámetros de Consulta

Todos los endpoints de métricas aceptan:

| Parámetro | Tipo | Descripción |
|-----------|------|-------------|
| `period_type` | enum | this_year, last_year, this_month, last_month, this_week, last_week, q1-q4, custom |
| `start_date` | date | Fecha inicio (solo para custom) |
| `end_date` | date | Fecha fin (solo para custom) |

## Estructura del Proyecto

```
Dashboard_partners/
├── backend/
│   ├── app/
│   │   ├── api/
│   │   │   ├── ecommerce.py      # Endpoints ecommerce
│   │   │   ├── shortage.py       # Endpoints shortage
│   │   │   └── pharmacies.py     # Endpoints farmacias
│   │   ├── core/
│   │   │   ├── config.py         # Configuración
│   │   │   └── database.py       # Conexión MongoDB
│   │   ├── repositories/
│   │   │   ├── booking_repository.py
│   │   │   └── pharmacy_repository.py
│   │   ├── schemas/
│   │   │   ├── metrics.py        # DTOs de métricas
│   │   │   └── periods.py        # Lógica de períodos
│   │   ├── services/
│   │   │   ├── ecommerce_service.py
│   │   │   └── shortage_service.py
│   │   └── main.py
│   └── requirements.txt
│
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   │   ├── Layout.tsx
│   │   │   ├── MetricCard.tsx
│   │   │   ├── PeriodSelector.tsx
│   │   │   ├── DataTable.tsx
│   │   │   └── charts/
│   │   ├── pages/
│   │   │   ├── Ecommerce.tsx
│   │   │   └── Shortage.tsx
│   │   ├── hooks/
│   │   │   ├── useEcommerce.ts
│   │   │   └── useShortage.ts
│   │   ├── services/
│   │   │   ├── ecommerceService.ts
│   │   │   ├── shortageService.ts
│   │   │   └── pharmacyService.ts
│   │   └── types/
│   │       └── index.ts
│   └── package.json
│
├── semantic_mapping.py           # Contexto de BD (referencia)
└── README.md
```

## Conexión a Base de Datos

El dashboard se conecta a:

```
mongodb://iimReports:Reports2019@localhost:27017/LudaFarma-PRO
```

Colecciones utilizadas:
- `bookings` - Pedidos (ecommerce y shortage)
- `pharmacies` - Farmacias

## Licencia

MIT
