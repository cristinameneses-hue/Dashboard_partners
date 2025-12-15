# 🧠 TrendsPro - Claude Context File

> **Intelligent natural language database query system with MySQL + MongoDB support**
> Last updated: 2025-01-13

---

## 📋 Table of Contents

1. [Project Overview](#project-overview)
2. [Architecture](#architecture)
3. [Tech Stack](#tech-stack)
4. [Directory Structure](#directory-structure)
5. [Database Systems](#database-systems)
6. [Key Components](#key-components)
7. [Integration Systems](#integration-systems)
8. [Development Workflow](#development-workflow)
9. [Environment Configuration](#environment-configuration)
10. [Testing Strategy](#testing-strategy)
11. [Security & Permissions](#security--permissions)
12. [Common Tasks](#common-tasks)
13. [Troubleshooting](#troubleshooting)

---

## 🎯 Project Overview

### What is TrendsPro?

TrendsPro is an advanced intelligent query system that allows users to query MySQL and MongoDB databases using **natural language in Spanish**. The system automatically detects which database to use based on the context of the question and generates intelligent responses using GPT-4o-mini.

### Core Features

- 🔄 **Automatic Database Routing**: Intelligently routes queries to MySQL (analytics) or MongoDB (operations)
- 🤖 **Dual LLM Integration**:
  - OpenAI GPT-4o-mini for primary queries
  - ChatGPT API for business team with optimized system prompts
- 🛡️ **Security First**: READ-ONLY mode by default with configurable query limits
- 🌐 **Web Interface**: Interactive Flask-based dashboard with query history
- 📊 **Multi-Database**: Supports multiple MySQL and MongoDB databases simultaneously
- 🔌 **MCP Integration**: Compatible with Anthropic's Model Context Protocol
- 💬 **Streaming Responses**: Real-time streaming for better UX

### Key Use Cases

1. **Analytics Queries** → MySQL
   - Sales trends and product performance
   - Risk group analysis (Z_Y scores)
   - Historical data and predictions

2. **Operational Queries** → MongoDB
   - Pharmacy and user management
   - Real-time bookings and stock
   - Partner GMV (Glovo, Uber, Danone, etc.)
   - Catalog and payments

---

## 🏗️ Architecture

### System Architecture Diagram

```
┌─────────────────────────────────────────────────────────────┐
│                    USER INTERFACE                           │
│                                                               │
│  ┌─────────────────┐          ┌──────────────────┐          │
│  │  Web Interface  │          │  MCP Client      │          │
│  │  (Flask)        │          │  (Claude, etc.)  │          │
│  └────────┬────────┘          └─────────┬────────┘          │
└───────────┼────────────────────────────┼─────────────────────┘
            │                            │
            v                            v
┌───────────────────────────────────────────────────────────────┐
│                  APPLICATION LAYER                            │
│                                                               │
│  ┌──────────────────────────────────────────────────────┐   │
│  │         Flask Server (server_unified.py)              │   │
│  │  - Routes: /query, /query_stream, /chat              │   │
│  │  - Authentication & Session Management                │   │
│  │  - Streaming Response Handler                         │   │
│  └────────────────┬─────────────────────────────────────┘   │
│                   │                                          │
│  ┌────────────────┴─────────────────────────────────────┐   │
│  │    Unified Database Manager                           │   │
│  │    (unified_database_manager.py)                      │   │
│  │    - Connection pooling                               │   │
│  │    - Query routing                                    │   │
│  │    - Permission enforcement                           │   │
│  └────────────────┬─────────────────────────────────────┘   │
└───────────────────┼───────────────────────────────────────────┘
                    │
         ┌──────────┴──────────┐
         v                     v
┌─────────────────┐   ┌─────────────────────────┐
│  LLM SERVICES   │   │   MCP SERVER (Node.js)  │
│                 │   │                         │
│  ┌───────────┐  │   │  ┌──────────────────┐  │
│  │  OpenAI   │  │   │  │  Unified Tools   │  │
│  │  GPT-4o   │  │   │  │  (TypeScript)    │  │
│  │  mini     │  │   │  └──────────────────┘  │
│  └─────┬─────┘  │   │                         │
│        │        │   │  - get_routing_context  │
│  ┌─────┴─────┐  │   │  - list_databases       │
│  │  ChatGPT  │  │   │  - unified_query        │
│  │   API     │  │   │                         │
│  └───────────┘  │   └──────────┬──────────────┘
└─────────────────┘              │
         │                       │
         v                       v
┌─────────────────────────────────────────────────────────┐
│                   DATABASE LAYER                        │
│                                                          │
│  ┌──────────────────────┐    ┌──────────────────────┐  │
│  │   MySQL (Analytics)  │    │  MongoDB (Operations)│  │
│  │                      │    │                      │  │
│  │  - trends_consolidado│    │  - ludafarma        │  │
│  │  - Sales data        │    │  - Pharmacies       │  │
│  │  - Risk groups       │    │  - Bookings         │  │
│  │  - Z_Y scores        │    │  - Catalog          │  │
│  │  - Predictions       │    │  - Payments         │  │
│  └──────────────────────┘    │  - Partner GMV      │  │
│                               └──────────────────────┘  │
└─────────────────────────────────────────────────────────┘
```

### Data Flow

#### Query Flow (Web Interface)
```
User Question → Flask Route → Routing Logic → LLM Processing → Database Query → Results → User
```

#### Query Flow (MCP)
```
MCP Client → MCP Server → Context Tool → Unified Query Tool → Database → Structured Response
```

### Routing Logic

The system uses keyword-based routing to decide which database to query:

**MySQL Keywords:**
- ventas, sales, trends, cazador, Z_Y, grupo de riesgo, analytics, prediction, bookings_agrupado

**MongoDB Keywords:**
- farmacia, usuario, booking, catálogo, stock actual, pago, notificación, partner, GMV de partner

**Decision Algorithm:**
```python
def route_query(question: str) -> Literal["mysql", "mongodb"]:
    mysql_score = count_mysql_keywords(question)
    mongodb_score = count_mongodb_keywords(question)

    if mysql_score > mongodb_score:
        return "mysql"
    else:
        return "mongodb"  # Default to operations
```

---

## 🛠️ Tech Stack

### Backend
- **Python 3.8+**
  - Flask 3.0+ (web server)
  - mysql.connector (MySQL client)
  - pymongo 4.17+ (MongoDB client)
  - python-dotenv (configuration)
  - openai (LLM integration)

- **Node.js 20+**
  - TypeScript 5.8+
  - @modelcontextprotocol/sdk (MCP integration)
  - mysql2 (MySQL client)
  - mongodb (MongoDB client)
  - @ai-sdk/openai (AI integration)

### Frontend
- **Vanilla JavaScript**
  - No frameworks (intentional for simplicity)
  - Native Fetch API for streaming
  - Server-Sent Events (SSE) for real-time updates

### Databases
- **MySQL 8.0+** - Analytics (trends_consolidado)
- **MongoDB 4.0+** - Operations (ludafarma)

### AI/ML Services
- **OpenAI GPT-4o-mini** - Primary query interpreter
- **ChatGPT API** - Business team interface with custom system prompts

### Testing
- **Python**: pytest (unit tests)
- **Node.js**: vitest (unit + integration)
- **E2E**: Playwright 1.56+

### DevOps
- **Git** with Gitflow (main, develop, pre, feature/*, hotfix/*)
- **Environment**: .env based configuration
- **CI/CD**: (To be implemented)

---

## 📁 Directory Structure

```
trends_mcp/
│
├── .claude/                          # Claude Code configuration
│   ├── settings.local.json           # Local Claude settings
│   └── claude.md                     # This context file
│
├── web/                              # Flask application
│   ├── server_unified.py             # Main Flask server
│   │   - Routes: /query, /query_stream, /chat, /login
│   │   - Session management
│   │   - Streaming response handler
│   │
│   ├── unified_database_manager.py   # Database manager (Python)
│   │   - UnifiedDatabaseManager class
│   │   - MySQL + MongoDB connection handling
│   │   - Query execution (execute_mysql, execute_mongodb)
│   │   - Routing logic (route_query)
│   │
│   └── requirements.txt              # Python dependencies
│
├── src/                              # MCP Server (TypeScript/Node.js)
│   ├── index.ts                      # MCP server entry point
│   │
│   ├── db/                           # Database modules
│   │   ├── unified-database-manager.ts  # Main unified manager
│   │   ├── multi-connection-manager.ts  # Connection pooling
│   │   ├── mongodb-connection-manager.ts
│   │   ├── permissions.ts            # Permission system
│   │   ├── utils.ts
│   │   └── index.ts
│   │
│   ├── context/                      # Context generation
│   │   └── unified-database-context.ts  # LLM routing context
│   │
│   ├── mcp/                          # MCP tools
│   │   └── unified-tools.ts          # MCP tool definitions
│   │       - get_routing_context
│   │       - list_databases
│   │       - unified_query
│   │
│   ├── utils/                        # Utilities
│   │   ├── connection-string-parser.ts
│   │   ├── mongodb-connection-parser.ts
│   │   └── index.ts
│   │
│   ├── types/                        # TypeScript types
│   │   ├── connection-strings.ts
│   │   ├── mongodb-connections.ts
│   │   └── index.ts
│   │
│   ├── config/
│   │   └── index.ts                  # Configuration loader
│   │
│   └── domain-context.ts             # Domain-specific context
│
├── templates/                        # HTML templates
│   ├── index.html                    # Main query interface
│   │   - Chat-like UI
│   │   - Streaming response support
│   │   - Query history
│   │   - Database toggle (OpenAI/ChatGPT)
│   │
│   └── login.html                    # Login page
│
├── static/                           # Static assets
│   ├── css/
│   │   └── style.css                 # Main styles
│   │
│   ├── js/
│   │   └── app.js                    # Frontend logic
│   │       - Streaming response handler
│   │       - Chat message rendering
│   │       - Example queries
│   │
│   └── images/
│       └── logo.svg                  # TrendsPro logo
│
├── tests/                            # E2E tests
│   ├── e2e.spec.cjs                  # End-to-end tests
│   └── debug-mode.spec.cjs           # Debug mode tests
│
├── docs/                             # Documentation
│   ├── SYSTEM_PROMPT_EQUIPO_NEGOCIO.txt  # ChatGPT system prompt
│   ├── GUIA_CHATGPT_API.md           # ChatGPT API guide
│   ├── INSTRUCCIONES_PRUEBA_CHATGPT.md
│   ├── COMPARACION_PROMPT_VS_FINETUNING.md
│   ├── CHATGPT_TRAINING_PARTNERS_GMV.md
│   ├── FINE_TUNING_DATASET.jsonl
│   └── API_SYSTEM_PROMPT.txt
│
├── chatgpt_query_system.py           # Standalone ChatGPT system
├── test_chatgpt_system.py            # ChatGPT system tests
│
├── package.json                      # Node.js dependencies & scripts
├── tsconfig.json                     # TypeScript configuration
├── vitest.config.ts                  # Test configuration
├── playwright.config.cjs             # Playwright configuration
│
├── .env                              # Environment variables (not in git)
├── .env.example                      # Environment template
├── .env.chatgpt                      # ChatGPT specific config
│
├── .gitignore                        # Git ignore rules
├── README.md                         # Main README
├── README_CHATGPT_SYSTEM.md          # ChatGPT system README
│
└── LICENSE                           # MIT License

```

### Key Files Explained

#### Backend - Python (Flask)

**`web/server_unified.py`** (Main server)
- Flask routes for web interface
- `/query` - Single query endpoint (non-streaming)
- `/query_stream` - Streaming query endpoint (SSE)
- `/chat` - ChatGPT API endpoint
- Session management and authentication
- CORS configuration

**`web/unified_database_manager.py`** (Database manager)
- `UnifiedDatabaseManager` class
- Connection management for MySQL and MongoDB
- Query execution methods:
  - `execute_mysql(sql, db_name)`
  - `execute_mongodb(collection, query, options, db_name)`
  - `execute_mongodb_aggregation(collection, pipeline, db_name)`
- Routing function: `route_query(question)`
- Environment-based configuration loading

#### Backend - Node.js (MCP)

**`src/db/unified-database-manager.ts`**
- TypeScript version of database manager
- Multi-database connection pooling
- Permission enforcement
- Query validation

**`src/mcp/unified-tools.ts`**
- MCP tool definitions
- `get_routing_context` - Provides routing rules to LLM
- `list_databases` - Lists available databases
- `unified_query` - Executes queries with auto-routing

**`src/context/unified-database-context.ts`**
- Generates context for LLM decision making
- Contains routing rules and keywords
- Database schema information

#### Frontend

**`templates/index.html`**
- Main query interface (chat-like)
- Streaming response container
- Database toggle (OpenAI/ChatGPT)
- Query history display
- Example queries

**`static/js/app.js`**
- Streaming response handler using Fetch API
- Chat message rendering
- Example query population
- Error handling

#### Testing

**`tests/e2e.spec.cjs`**
- Playwright E2E tests
- Tests query flow, streaming, examples

**`tests/debug-mode.spec.cjs`**
- Debug mode specific tests

**`test_chatgpt_system.py`**
- Python tests for ChatGPT system
- Quick test (3 cases)
- Full test (10 cases)
- Interactive test mode

---

## 💾 Database Systems

### MySQL - Analytics Database

**Database:** `trends_consolidado`

**Purpose:** Historical analytics, trends, predictions

**Key Tables:**

1. **`product_sales`** - Sales data
   - Columns: product_id, sales_count, date, revenue

2. **`risk_groups`** - Product risk classification
   - Columns: product_id, risk_group (1-4), Z_Y_score

3. **`bookings_agrupado`** - Aggregated booking statistics
   - Columns: date, total_bookings, channel, GMV

4. **`cazador_opportunities`** - Opportunity detection
   - Columns: product_id, opportunity_type, score

**Common Queries:**
- Top selling products
- Products in risk group 3-4
- Products with Z_Y < -0.30
- Sales trends by date range
- Booking analytics

**Access:** READ-ONLY by default

---

### MongoDB - Operations Database

**Database:** `ludafarma`

**Purpose:** Real-time operations, catalog, bookings

**Key Collections:**

1. **`pharmacies`** / **`allpharmacies`**
   - Active pharmacies
   - Schema: { name, address, city, active, createdAt }

2. **`users`** / **`thirdUsers`**
   - User accounts
   - Schema: { email, name, role, pharmacy_id, createdAt }

3. **`bookings`** / **`bookingRequests`**
   - Booking/reservation records
   - Schema: { pharmacy_id, product_id, quantity, status, creator, createdAt }
   - Important: `creator` field identifies partner (glovo, uber, danone, etc.)

4. **`items`** / **`eans`** / **`itemPrices`** / **`vademecum`**
   - Product catalog
   - Schema: { name, ean, price, category, active }

5. **`stockItems`** / **`stockEvents`**
   - Real-time inventory
   - Schema: { pharmacy_id, product_id, quantity, lastUpdate }

6. **`payments`** / **`invoices`** / **`billings`**
   - Financial records
   - Schema: { amount, status, pharmacy_id, date, method }

7. **`notifications`** / **`userNotifications`** / **`firebaseTokens`**
   - Notification system
   - Schema: { user_id, message, read, sentAt }

8. **`deliveryEvents`** / **`providers`**
   - Delivery tracking
   - Schema: { booking_id, status, provider, timestamp }

9. **`auditEvents`** / **`connectionEvents`**
   - Audit logs
   - Schema: { user_id, action, resource, timestamp }

**Common Queries:**
- Active pharmacies count
- Users registered in date range
- Pending bookings today
- Current stock for product X at pharmacy Y
- Payments processed this week
- GMV by partner (Glovo, Uber, etc.) using bookings.creator + aggregation
- Top products in catalog

**Access:** READ-ONLY by default

---

### Database Routing Rules

#### Use MySQL when query contains:
- ventas, sales, sold, vendidos
- trends, tendencias, demand, demanda
- cazador, hunter, opportunities
- Z_Y, z-score, riesgo, risk group
- performance, análisis, predicción
- bookings_agrupado (aggregated stats)

#### Use MongoDB when query contains:
- farmacia, pharmacy
- usuario, user
- booking, reserva, derivación (current bookings)
- catálogo, catalog, producto actual
- stock actual, current stock
- pago, payment, factura
- notificación, notification
- delivery, envío, pedido
- partner, proveedor, glovo, uber, danone, hartmann, carrefour
- GMV de partner (partner-specific GMV)

#### Default: MongoDB
If no clear indicators, default to MongoDB (operational data is more commonly queried)

---

## 🔧 Key Components

### 1. UnifiedDatabaseManager (Python)

**File:** `web/unified_database_manager.py`

**Class:** `UnifiedDatabaseManager`

**Initialization:**
```python
manager = UnifiedDatabaseManager()
# Automatically loads all databases from environment variables
# Patterns: DB_*_URL (MySQL), MONGO_*_URL (MongoDB)
```

**Key Methods:**

```python
# List all databases
databases = manager.list_databases()
# Returns: [{'name': 'trends', 'type': 'mysql', 'is_default': True}, ...]

# Execute MySQL query
result = manager.execute_mysql(
    sql="SELECT * FROM products LIMIT 10",
    db_name="trends"  # optional, uses default if None
)

# Execute MongoDB query
result = manager.execute_mongodb(
    collection="pharmacies",
    query={"active": True},
    options={"limit": 20, "sort": {"createdAt": -1}},
    db_name="ludafarma"  # optional
)

# Execute MongoDB aggregation
result = manager.execute_mongodb_aggregation(
    collection="bookings",
    pipeline=[
        {"$match": {"creator": "glovo"}},
        {"$group": {"_id": "$creator", "total": {"$sum": "$gmv"}}}
    ],
    db_name="ludafarma"
)

# Routing
database = route_query("¿Cuáles son los productos más vendidos?")
# Returns: "mysql"
```

**Response Format:**
```python
{
    'success': True,
    'database_type': 'mysql',  # or 'mongodb'
    'database_name': 'trends',
    'data': [...],  # list of records
    'count': 10,
    'total_count': 1000,  # MongoDB only
    'limited': True  # MongoDB only
}
```

---

### 2. Flask Server (Python)

**File:** `web/server_unified.py`

**Main Routes:**

```python
@app.route('/query', methods=['POST'])
# Single query endpoint (non-streaming)
# Request: {"question": "¿Cuántas farmacias hay?", "use_chatgpt": false}
# Response: {"answer": "...", "database": "mongodb", "count": 150}

@app.route('/query_stream', methods=['POST'])
# Streaming query endpoint (Server-Sent Events)
# Request: {"question": "...", "use_chatgpt": false}
# Response: Stream of SSE events
#   data: {"type": "token", "content": "Hay"}
#   data: {"type": "token", "content": " 150"}
#   data: {"type": "done"}

@app.route('/chat', methods=['POST'])
# ChatGPT API endpoint
# Request: {"message": "GMV de Glovo esta semana", "history": [...]}
# Response: {"response": "...", "cost_usd": 0.006}

@app.route('/login', methods=['GET', 'POST'])
# Login page
# Basic session-based authentication
```

**Session Management:**
```python
session['authenticated'] = True
session['username'] = username
```

---

### 3. MCP Server (TypeScript)

**File:** `src/index.ts`

**MCP Tools:**

```typescript
// Tool 1: Get routing context for LLM
get_routing_context()
// Returns: Markdown with routing rules and keywords

// Tool 2: List available databases
list_databases()
// Returns: [
//   {name: 'trends', type: 'mysql', is_default: true},
//   {name: 'ludafarma', type: 'mongodb', is_default: false}
// ]

// Tool 3: Unified query
unified_query({
  question: "¿Cuántas farmacias tenemos?",
  database?: "ludafarma",  // optional, auto-routes if not provided
  debug?: false
})
// Returns: {
//   database_used: 'mongodb',
//   result: {...},
//   query_executed: {...}
// }
```

**Usage with Claude:**
```
User: "Show me top 10 selling products"
Claude: [Calls get_routing_context()]
Claude: [Analyzes context, determines MySQL]
Claude: [Calls unified_query({question: "...", database: "trends"})]
Claude: "Here are the top 10 selling products: ..."
```

---

### 4. ChatGPT Integration System

**File:** `chatgpt_query_system.py`

**Class:** `LudaFarmaQuerySystem`

**Features:**
- System prompts optimized for business team
- Handles incomplete questions (asks for clarification)
- Intelligent defaults and inference
- Cost tracking per query
- Conversation history support

**Usage:**
```python
from chatgpt_query_system import LudaFarmaQuerySystem

system = LudaFarmaQuerySystem(model="gpt-4")

# Single query
result = system.query("GMV de Glovo esta semana")
print(result["answer"])
print(f"Cost: ${result['cost_usd']}")

# Interactive mode
system.interactive_mode()
# Tu pregunta: GMV de Glovo esta semana
# Respuesta: Voy a buscar el GMV de Glovo de esta semana...
```

**System Prompt Features:**
- Understands LudaFarma domain (pharmacies, bookings, partners)
- Knows when to use MySQL vs MongoDB
- Asks clarifying questions when info is missing
- Provides structured query instructions

**Testing:**
```bash
# Quick test (3 cases)
python test_chatgpt_system.py quick

# Full test (10 cases)
python test_chatgpt_system.py all

# Interactive test
python test_chatgpt_system.py interactive
```

---

### 5. Frontend (Vanilla JS)

**File:** `static/js/app.js`

**Key Functions:**

```javascript
// Send query with streaming
async function sendQuery() {
    const question = document.getElementById('queryInput').value;
    const useChatGPT = document.getElementById('useChatGPT').checked;

    const response = await fetch('/query_stream', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({question, use_chatgpt: useChatGPT})
    });

    const reader = response.body.getReader();
    const decoder = new TextDecoder();

    while (true) {
        const {done, value} = await reader.read();
        if (done) break;

        const chunk = decoder.decode(value);
        // Process SSE events
        const lines = chunk.split('\n');
        for (const line of lines) {
            if (line.startsWith('data: ')) {
                const data = JSON.parse(line.slice(6));
                if (data.type === 'token') {
                    appendToken(data.content);
                }
            }
        }
    }
}

// Render example queries
function populateExamples() {
    const examples = [
        "¿Cuáles son los 20 productos más vendidos?",
        "Productos en grupo de riesgo 3",
        "¿Cuántas farmacias tenemos activas?",
        "GMV de Glovo esta semana"
    ];

    examples.forEach(example => {
        const button = createExampleButton(example);
        examplesContainer.appendChild(button);
    });
}
```

**Streaming Response Handler:**
- Uses native Fetch API with ReadableStream
- Parses Server-Sent Events (SSE)
- Appends tokens to chat in real-time
- Handles errors gracefully

---

## 🔗 Integration Systems

### 1. OpenAI Integration (Primary)

**Configuration:**
```env
OPENAI_API_KEY=sk-proj-...
OPENAI_MODEL=gpt-4o-mini
OPENAI_TEMPERATURE=0.1
OPENAI_MAX_TOKENS=2000
```

**Usage in Flask:**
```python
from openai import OpenAI

client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))

response = client.chat.completions.create(
    model="gpt-4o-mini",
    messages=[
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": question}
    ],
    temperature=0.1,
    stream=True  # Enable streaming
)

for chunk in response:
    if chunk.choices[0].delta.content:
        yield chunk.choices[0].delta.content
```

**Cost Estimates:**
- GPT-4o-mini: ~$0.006 per query (normal)
- GPT-4o-mini: ~$0.012 per query (with long history)

---

### 2. ChatGPT API Integration (Business Team)

**Configuration:**
```env
# .env.chatgpt
OPENAI_API_KEY=sk-proj-...
OPENAI_MODEL=gpt-4
OPENAI_TEMPERATURE=0.1
```

**System Prompt Strategy:**
- Optimized prompts for business users (non-technical)
- Handles incomplete queries by asking clarifying questions
- Understands domain-specific terms:
  - Channels: Glovo, Uber, Danone, Hartmann, Carrefour
  - Shortage: Pharmacy-to-pharmacy derivations
  - GMV: Gross Merchandise Value by partner
  - Metrics: GMV, orders, units, products

**Interactive Flow:**
```
User: "Dame los datos de Glovo"
ChatGPT: "¿Qué datos de Glovo necesitas? (GMV, pedidos, productos, etc.)"
User: "GMV"
ChatGPT: "¿De qué período? (hoy, esta semana, este mes)"
User: "Esta semana"
ChatGPT: [Executes query]
```

**Why System Prompt vs Fine-Tuning?**
- ✅ 60% cheaper than fine-tuning
- ✅ More flexible (edit prompt vs retrain model)
- ✅ Better for incomplete questions (can ask clarifications)
- ✅ GPT-4 already excellent with good context
- ✅ Immediate setup (no 2-hour training wait)

**When to Consider Fine-Tuning:**
- If >10,000 queries/month
- If prompt success rate < 70%
- If ultra-fast responses needed

---

### 3. MCP (Model Context Protocol) Integration

**Purpose:** Allow Claude and other MCP-compatible clients to query databases

**MCP Server:** Node.js/TypeScript server exposing tools

**Tools Exposed:**

1. **`get_routing_context`**
   - Provides LLM with routing rules
   - No parameters
   - Returns: Markdown documentation

2. **`list_databases`**
   - Lists available databases
   - No parameters
   - Returns: Array of {name, type, is_default}

3. **`unified_query`**
   - Execute query with auto-routing
   - Parameters:
     - `question` (required): Natural language query
     - `database` (optional): Force specific database
     - `debug` (optional): Enable debug mode
   - Returns: Query results with metadata

**Configuration:**
```bash
# Install MCP server globally
npm install -g @trendspro/mcp-server-unified-db

# Configure in Claude Code
# .claude/settings.json
{
  "mcpServers": {
    "trends_mysql": {
      "command": "node",
      "args": ["C:\\path\\to\\trends_mcp\\dist\\index.js"],
      "env": {
        "DB_TRENDS_URL": "mysql://user:pass@host:port/database"
      }
    }
  }
}
```

**Usage Example:**
```
User: "How many pharmacies do we have?"
Claude: [Calls get_routing_context() to understand routing rules]
Claude: [Analyzes question, determines MongoDB]
Claude: [Calls unified_query({question: "..."})]
Claude: "We have 147 active pharmacies."
```

---

## 🔄 Development Workflow

### Git Branching Strategy (Gitflow)

```
main           Production-ready code
  ↑
  └── pre      Pre-production/staging
        ↑
        └── develop    Integration branch
              ↑
              ├── feature/new-dashboard
              ├── feature/chatgpt-streaming
              └── hotfix/login-bug
```

**Branch Types:**
- `main` - Production (protected)
- `pre` - Pre-production/staging
- `develop` - Main development branch
- `feature/*` - New features (branch from develop)
- `hotfix/*` - Urgent fixes (branch from main)

**Workflow:**

1. **Start new feature:**
```bash
git checkout develop
git pull origin develop
git checkout -b feature/my-feature
```

2. **Work on feature:**
```bash
# Make changes
git add .
git commit -m "feat: add new feature"
```

3. **Push and create PR:**
```bash
git push origin feature/my-feature
# Create PR to develop on GitHub
```

4. **After PR approval:**
```bash
git checkout develop
git pull origin develop
git branch -d feature/my-feature
```

5. **Release to pre:**
```bash
git checkout pre
git merge develop
git push origin pre
```

6. **Release to production:**
```bash
git checkout main
git merge pre
git push origin main
git tag -a v1.0.0 -m "Release v1.0.0"
git push origin v1.0.0
```

---

### Commit Message Convention

Follow conventional commits:

```
<type>(<scope>): <description>

[optional body]

[optional footer]
```

**Types:**
- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation changes
- `style`: Code style changes (formatting, etc.)
- `refactor`: Code refactoring
- `test`: Add or update tests
- `chore`: Maintenance tasks

**Examples:**
```
feat(chatgpt): add streaming support for chat responses
fix(mysql): resolve connection timeout issue
docs(readme): update installation instructions
refactor(database): simplify routing logic
test(e2e): add playwright tests for query flow
chore(deps): update openai to v1.3.22
```

---

### Development Scripts

**Python (Flask):**
```bash
# Install dependencies
pip install -r web/requirements.txt

# Run Flask server (development)
cd web
python server_unified.py

# Run tests
pytest

# Test database connections
python unified_database_manager.py
```

**Node.js (MCP):**
```bash
# Install dependencies
npm install

# Build TypeScript
npm run build

# Run in development mode
npm run dev

# Run tests
npm test

# Run specific test suite
npm run test:unit
npm run test:integration
npm run test:e2e

# Start MCP server
npm start
# or
node dist/index.js
```

**E2E Tests (Playwright):**
```bash
# Run all E2E tests
npx playwright test

# Run specific test file
npx playwright test tests/e2e.spec.cjs

# Run with UI
npx playwright test --ui

# Debug mode
npx playwright test --debug
```

---

## ⚙️ Environment Configuration

### Environment Files

**`.env`** (Main configuration, NOT in git)
```env
# MySQL
DB_TRENDS_URL=mysql://user:pass@127.0.0.1:3307/trends_consolidado
DB_TRENDS_CAN_INSERT=false
DB_TRENDS_CAN_UPDATE=false
DB_TRENDS_CAN_DELETE=false
DB_TRENDS_IS_DEFAULT=true

# MongoDB
MONGO_LUDAFARMA_URL=mongodb://user:pass@localhost:27017/ludafarma
MONGO_LUDAFARMA_CAN_INSERT=false
MONGO_LUDAFARMA_CAN_UPDATE=false
MONGO_LUDAFARMA_CAN_DELETE=false
MONGO_LUDAFARMA_IS_DEFAULT=false

# OpenAI
OPENAI_API_KEY=sk-proj-XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX
OPENAI_MODEL=gpt-4o-mini
OPENAI_TEMPERATURE=0.1
OPENAI_MAX_TOKENS=2000

# Security
ALLOW_INSERT_OPERATION=false
ALLOW_UPDATE_OPERATION=false
ALLOW_DELETE_OPERATION=false
ALLOW_DDL_OPERATION=false

# Flask
SECRET_KEY=your-secret-key-here
FLASK_ENV=development
```

**`.env.example`** (Template, in git)
- Sanitized version with placeholder values
- Documents all available configuration options

**`.env.chatgpt`** (ChatGPT system, NOT in git)
```env
OPENAI_API_KEY=sk-proj-...
OPENAI_MODEL=gpt-4
OPENAI_TEMPERATURE=0.1
```

### Configuration Loading

**Python (Flask):**
```python
from dotenv import load_dotenv
import os

load_dotenv()  # Loads .env file

mysql_host = os.getenv('MYSQL_HOST', '127.0.0.1')
openai_key = os.getenv('OPENAI_API_KEY')
```

**Node.js (MCP):**
```typescript
import dotenv from 'dotenv';
dotenv.config();

const mysqlUrl = process.env.DB_TRENDS_URL;
const openaiKey = process.env.OPENAI_API_KEY;
```

### Multi-Database Configuration Pattern

**Pattern:** `DB_<NAME>_URL` or `MONGO_<NAME>_URL`

**Examples:**
```env
# MySQL databases
DB_TRENDS_URL=mysql://...
DB_ANALYTICS_URL=mysql://...
DB_WAREHOUSE_URL=mysql://...

# MongoDB databases
MONGO_LUDAFARMA_URL=mongodb://...
MONGO_CATALOG_URL=mongodb://...
MONGO_LOGS_URL=mongodb://...
```

**Permissions per database:**
```env
DB_TRENDS_CAN_INSERT=false
DB_TRENDS_CAN_UPDATE=false
DB_TRENDS_CAN_DELETE=false
DB_TRENDS_IS_DEFAULT=true

MONGO_LUDAFARMA_CAN_INSERT=false
MONGO_LUDAFARMA_CAN_UPDATE=false
MONGO_LUDAFARMA_CAN_DELETE=false
```

---

## 🧪 Testing Strategy

### Test Structure

```
tests/
├── e2e.spec.cjs              # End-to-end tests (Playwright)
├── debug-mode.spec.cjs       # Debug mode tests
└── test-results/             # Test outputs

test_chatgpt_system.py        # ChatGPT system tests (Python)
```

### Python Tests (ChatGPT System)

**File:** `test_chatgpt_system.py`

**Test Modes:**

1. **Quick Test (3 cases):**
```bash
python test_chatgpt_system.py quick
```
Tests:
- Complete question: "GMV de Glovo esta semana"
- Missing metric: "Dame los datos de Glovo"
- Missing channel: "El GMV que tuvimos"

2. **Full Test (10 cases):**
```bash
python test_chatgpt_system.py all
```
Additional tests:
- Vague question: "Cuéntame de shortage"
- Inference: "Cómo va Danone este mes"
- Product query: "Top productos de Uber"
- General analytics: "Productos con problemas"
- Comparison: "Glovo vs Uber del mes pasado"
- Odd structure: "Los números de Glovo"
- Shortage: "GMV de derivaciones de ayer"

3. **Interactive Test (manual validation):**
```bash
python test_chatgpt_system.py interactive
```
Allows manual testing of ChatGPT responses

**Test Cases Covered:**
- ✅ Complete questions
- ✅ Incomplete questions (missing info)
- ✅ Clarification requests
- ✅ Intelligent inference
- ✅ Partner/channel queries
- ✅ Analytics vs operations routing
- ✅ Cost tracking

---

### E2E Tests (Playwright)

**File:** `tests/e2e.spec.cjs`

**Test Cases:**

```javascript
test('should load the query page', async ({ page }) => {
    await page.goto('http://localhost:5000');
    await expect(page).toHaveTitle(/TrendsPro/);
});

test('should send query and get response', async ({ page }) => {
    await page.goto('http://localhost:5000');
    await page.fill('#queryInput', '¿Cuántas farmacias hay?');
    await page.click('#sendButton');

    // Wait for streaming response
    await page.waitForSelector('.response-message');
    const response = await page.textContent('.response-message');
    expect(response).toBeTruthy();
});

test('should populate example queries', async ({ page }) => {
    await page.goto('http://localhost:5000');
    const examples = await page.$$('.example-query');
    expect(examples.length).toBeGreaterThan(0);
});

test('should toggle between OpenAI and ChatGPT', async ({ page }) => {
    await page.goto('http://localhost:5000');
    await page.check('#useChatGPT');
    const isChecked = await page.isChecked('#useChatGPT');
    expect(isChecked).toBe(true);
});
```

**Running E2E Tests:**
```bash
# Run all tests
npx playwright test

# Run with headed browser
npx playwright test --headed

# Run specific test
npx playwright test tests/e2e.spec.cjs

# Debug
npx playwright test --debug

# Generate report
npx playwright show-report
```

---

### Unit Tests (Node.js/Vitest)

**Configuration:** `vitest.config.ts`

**Test Structure:**
```typescript
import { describe, it, expect, beforeEach, afterEach } from 'vitest';
import { UnifiedDatabaseManager } from '../src/db/unified-database-manager';

describe('UnifiedDatabaseManager', () => {
    let manager: UnifiedDatabaseManager;

    beforeEach(() => {
        manager = new UnifiedDatabaseManager();
    });

    afterEach(() => {
        manager.closeAll();
    });

    it('should list all databases', () => {
        const databases = manager.listDatabases();
        expect(databases.length).toBeGreaterThan(0);
    });

    it('should route MySQL query correctly', () => {
        const db = routeQuery('¿Cuáles son los productos más vendidos?');
        expect(db).toBe('mysql');
    });

    it('should route MongoDB query correctly', () => {
        const db = routeQuery('¿Cuántas farmacias hay?');
        expect(db).toBe('mongodb');
    });
});
```

**Running Unit Tests:**
```bash
npm test
npm run test:watch
npm run test:coverage
```

---

## 🔒 Security & Permissions

### Default Security Posture

**READ-ONLY by default:**
- All write operations disabled
- Query limits enforced
- SQL injection prevention
- No DDL operations allowed

### Permission System

**Global Permissions (`.env`):**
```env
ALLOW_INSERT_OPERATION=false
ALLOW_UPDATE_OPERATION=false
ALLOW_DELETE_OPERATION=false
ALLOW_DDL_OPERATION=false
```

**Per-Database Permissions:**
```env
# MySQL
DB_TRENDS_CAN_INSERT=false
DB_TRENDS_CAN_UPDATE=false
DB_TRENDS_CAN_DELETE=false

# MongoDB
MONGO_LUDAFARMA_CAN_INSERT=false
MONGO_LUDAFARMA_CAN_UPDATE=false
MONGO_LUDAFARMA_CAN_DELETE=false
```

**Permission Hierarchy:**
1. Global settings (ALLOW_*)
2. Database-specific settings (DB_*_CAN_*)
3. Both must be true for operation to be allowed

### Query Limits

**MongoDB:**
- Default limit: 100 documents
- Maximum limit: 1000 documents
- Enforced in `execute_mongodb()`

**MySQL:**
- No automatic limit (user must specify in SQL)
- Consider adding LIMIT clause to all queries

### SQL Injection Prevention

**Python:**
```python
# ✅ Good: Parameterized queries
cursor.execute("SELECT * FROM products WHERE id = %s", (product_id,))

# ❌ Bad: String concatenation
cursor.execute(f"SELECT * FROM products WHERE id = {product_id}")
```

**Node.js:**
```typescript
// ✅ Good: Parameterized queries
connection.execute('SELECT * FROM products WHERE id = ?', [productId])

// ❌ Bad: Template literals
connection.execute(`SELECT * FROM products WHERE id = ${productId}`)
```

### Authentication

**Flask Session-Based:**
```python
@app.route('/query', methods=['POST'])
def query():
    if not session.get('authenticated'):
        return jsonify({'error': 'Not authenticated'}), 401
    # Process query
```

**TODO: Implement JWT-based auth for API endpoints**

### Secrets Management

**What NOT to commit:**
- `.env` files
- API keys
- Database passwords
- Secret keys

**What to commit:**
- `.env.example` (with placeholders)
- Documentation of required variables

**Git Protection:**
```gitignore
# .gitignore
.env
.env.local
.env.*.local
*.key
*.pem
credentials.json
```

---

## 🛠️ Common Tasks

### 1. Add New Database

**Step 1:** Add to `.env`
```env
# For MySQL
DB_NEWDB_URL=mysql://user:pass@host:port/database
DB_NEWDB_CAN_INSERT=false
DB_NEWDB_CAN_UPDATE=false
DB_NEWDB_CAN_DELETE=false
DB_NEWDB_IS_DEFAULT=false

# For MongoDB
MONGO_NEWDB_URL=mongodb://user:pass@host:port/database
MONGO_NEWDB_CAN_INSERT=false
MONGO_NEWDB_CAN_UPDATE=false
MONGO_NEWDB_CAN_DELETE=false
```

**Step 2:** Restart server
```bash
# Python
cd web
python server_unified.py

# Node.js
npm run build
npm start
```

**Step 3:** Test connection
```python
from unified_database_manager import UnifiedDatabaseManager

manager = UnifiedDatabaseManager()
databases = manager.list_databases()
print(databases)  # Should include new database
```

---

### 2. Update System Prompt (ChatGPT)

**File:** `docs/SYSTEM_PROMPT_EQUIPO_NEGOCIO.txt`

**Steps:**

1. **Edit system prompt:**
```text
# Add new instructions or concepts
- New partner: "Amazon" (amazon)
- New metric: "Average Order Value" (AOV)
```

2. **Update chatgpt_query_system.py:**
```python
# Load updated prompt
with open('docs/SYSTEM_PROMPT_EQUIPO_NEGOCIO.txt', 'r') as f:
    SYSTEM_PROMPT = f.read()
```

3. **Test with quick test:**
```bash
python test_chatgpt_system.py quick
```

4. **Validate with interactive test:**
```bash
python test_chatgpt_system.py interactive
```

5. **Document changes:**
```markdown
# docs/CHANGELOG_SYSTEM_PROMPT.md
## v1.1.0 (2025-01-13)
- Added Amazon partner support
- Added AOV metric definition
```

---

### 3. Add New Example Query

**File:** `templates/index.html`

**Step 1:** Add to examples array
```javascript
const examples = [
    // Existing examples
    "¿Cuáles son los 20 productos más vendidos?",
    "Productos en grupo de riesgo 3",

    // New example
    "GMV de Amazon este mes",
    "Productos con stock bajo en Madrid"
];
```

**Step 2:** Add to database routing rules if needed
```python
# web/unified_database_manager.py
ROUTING_RULES = {
    'mongodb': [
        # ... existing keywords
        'amazon',  # New partner
        'stock bajo', 'low stock'  # New feature
    ]
}
```

**Step 3:** Test in browser
```bash
cd web
python server_unified.py
# Open http://localhost:5000
# Click new example, verify it works
```

---

### 4. Debug Query Routing

**Enable debug mode:**

**Method 1: Flask debug route**
```python
# Add to server_unified.py
@app.route('/debug_route', methods=['POST'])
def debug_route():
    question = request.json.get('question')

    # Show routing decision
    mysql_score = sum(1 for kw in ROUTING_RULES['mysql'] if kw in question.lower())
    mongodb_score = sum(1 for kw in ROUTING_RULES['mongodb'] if kw in question.lower())

    return jsonify({
        'question': question,
        'mysql_score': mysql_score,
        'mongodb_score': mongodb_score,
        'decision': route_query(question),
        'mysql_keywords': [kw for kw in ROUTING_RULES['mysql'] if kw in question.lower()],
        'mongodb_keywords': [kw for kw in ROUTING_RULES['mongodb'] if kw in question.lower()]
    })
```

**Method 2: Python script**
```python
from web.unified_database_manager import route_query, ROUTING_RULES

test_questions = [
    "GMV de Glovo esta semana",
    "¿Cuántas farmacias tenemos?",
    "Productos con Z_Y menor a -0.30"
]

for q in test_questions:
    decision = route_query(q)
    print(f"\nQuestion: {q}")
    print(f"Decision: {decision}")

    # Show matching keywords
    mysql_kw = [kw for kw in ROUTING_RULES['mysql'] if kw in q.lower()]
    mongodb_kw = [kw for kw in ROUTING_RULES['mongodb'] if kw in q.lower()]
    print(f"MySQL keywords: {mysql_kw}")
    print(f"MongoDB keywords: {mongodb_kw}")
```

---

### 5. Add New MCP Tool

**File:** `src/mcp/unified-tools.ts`

**Step 1:** Define tool
```typescript
server.setRequestHandler(ListToolsRequestSchema, async () => {
    return {
        tools: [
            // Existing tools
            { name: 'get_routing_context', ... },
            { name: 'list_databases', ... },
            { name: 'unified_query', ... },

            // New tool
            {
                name: 'get_database_schema',
                description: 'Get schema information for a database',
                inputSchema: {
                    type: 'object',
                    properties: {
                        database: {
                            type: 'string',
                            description: 'Database name'
                        }
                    },
                    required: ['database']
                }
            }
        ]
    };
});
```

**Step 2:** Implement handler
```typescript
server.setRequestHandler(CallToolRequestSchema, async (request) => {
    if (request.params.name === 'get_database_schema') {
        const database = request.params.arguments.database;

        // Implement logic
        const schema = await getDatabaseSchema(database);

        return {
            content: [{
                type: 'text',
                text: JSON.stringify(schema, null, 2)
            }]
        };
    }
    // ... handle other tools
});
```

**Step 3:** Build and test
```bash
npm run build
npm start

# Test with MCP client
```

---

### 6. Add E2E Test

**File:** `tests/e2e.spec.cjs`

**Template:**
```javascript
const { test, expect } = require('@playwright/test');

test.describe('Feature Name', () => {
    test('should do something', async ({ page }) => {
        // Navigate
        await page.goto('http://localhost:5000');

        // Interact
        await page.fill('#queryInput', 'test query');
        await page.click('#sendButton');

        // Assert
        await page.waitForSelector('.response-message');
        const response = await page.textContent('.response-message');
        expect(response).toContain('expected text');
    });
});
```

**Run new test:**
```bash
npx playwright test tests/e2e.spec.cjs
```

---

## ❓ Troubleshooting

### Common Issues

#### 1. "OPENAI_API_KEY not found"

**Solution:**
```bash
# Check .env file exists
ls -la .env

# Check key is set
cat .env | grep OPENAI_API_KEY

# If missing, add it
echo "OPENAI_API_KEY=sk-proj-..." >> .env
```

#### 2. "Cannot connect to MySQL"

**Possible causes:**
- MySQL server not running
- Wrong host/port
- Wrong credentials
- Firewall blocking connection

**Debug:**
```bash
# Test MySQL connection manually
mysql -h 127.0.0.1 -P 3307 -u your_user -p

# Check MySQL is running
# Windows:
netstat -ano | findstr 3307

# Linux/Mac:
netstat -an | grep 3307

# Test from Python
python -c "import mysql.connector; conn = mysql.connector.connect(host='127.0.0.1', port=3307, user='user', password='pass'); print('Connected!')"
```

#### 3. "Cannot connect to MongoDB"

**Possible causes:**
- MongoDB server not running
- Wrong connection string
- Authentication failure
- Network/firewall issue

**Debug:**
```bash
# Test MongoDB connection manually
mongosh "mongodb://user:pass@localhost:27017/database"

# Check MongoDB is running
# Windows:
netstat -ano | findstr 27017

# Linux/Mac:
netstat -an | grep 27017

# Test from Python
python -c "from pymongo import MongoClient; client = MongoClient('mongodb://user:pass@localhost:27017/database'); print('Connected!')"
```

#### 4. "Rate limit exceeded" (OpenAI)

**Solution:**
- OpenAI limits requests per minute
- Wait 1 minute and retry
- Add delays between queries:

```python
import time

for query in queries:
    result = system.query(query)
    time.sleep(1)  # Wait 1 second between queries
```

#### 5. Flask server crashes on startup

**Check logs:**
```bash
cd web
python server_unified.py 2>&1 | tee server.log
```

**Common causes:**
- Missing dependencies: `pip install -r requirements.txt`
- Port already in use: Change `app.run(port=5001)`
- Database connection failure: Check `.env` credentials

#### 6. MCP server not working with Claude

**Debug steps:**

1. **Check MCP server logs:**
```bash
# Start with debug logging
DEBUG=* node dist/index.js
```

2. **Verify configuration:**
```json
// .claude/settings.json
{
  "mcpServers": {
    "trends_mysql": {
      "command": "node",
      "args": ["C:\\absolute\\path\\to\\dist\\index.js"]
    }
  }
}
```

3. **Test MCP tools manually:**
```bash
# Use MCP inspector
npx @modelcontextprotocol/inspector node dist/index.js
```

4. **Check environment variables:**
```bash
# MCP server inherits env from .env file
# Verify DB_*_URL and MONGO_*_URL are set
```

#### 7. Streaming response not working

**Frontend debug:**
```javascript
// Add debug logs to app.js
console.log('Starting stream...');
const response = await fetch('/query_stream', {...});
console.log('Response status:', response.status);
console.log('Response headers:', response.headers);

const reader = response.body.getReader();
while (true) {
    const {done, value} = await reader.read();
    console.log('Chunk received:', done, value);
    if (done) break;
}
```

**Backend debug:**
```python
# Add debug logs to server_unified.py
@app.route('/query_stream', methods=['POST'])
def query_stream():
    print(f"[DEBUG] Received question: {question}")

    def generate():
        print("[DEBUG] Starting stream generation")
        for chunk in response:
            print(f"[DEBUG] Yielding chunk: {chunk}")
            yield f"data: {json.dumps({'type': 'token', 'content': chunk})}\n\n"
        print("[DEBUG] Stream complete")

    return Response(generate(), mimetype='text/event-stream')
```

#### 8. Query returns no results

**Debug steps:**

1. **Check database routing:**
```python
question = "Your query here"
db = route_query(question)
print(f"Routed to: {db}")
```

2. **Check database connection:**
```python
manager = UnifiedDatabaseManager()
databases = manager.list_databases()
print(f"Available databases: {databases}")
```

3. **Test query directly:**
```python
# MySQL
result = manager.execute_mysql("SELECT COUNT(*) FROM products")
print(result)

# MongoDB
result = manager.execute_mongodb("pharmacies", {}, {"limit": 1})
print(result)
```

4. **Enable query logging:**
```python
# Add to unified_database_manager.py
def execute_mysql(self, sql: str, db_name: Optional[str] = None):
    print(f"[SQL] Executing: {sql}")
    print(f"[SQL] Database: {db_name}")
    # ... rest of code
```

---

### Performance Issues

#### Slow MySQL queries

**Solutions:**
1. Add indexes to frequently queried columns
2. Use EXPLAIN to analyze query plan
3. Limit result sets with LIMIT
4. Consider caching frequent queries

```sql
-- Analyze query
EXPLAIN SELECT * FROM products WHERE category = 'pharmacy';

-- Add index
CREATE INDEX idx_category ON products(category);
```

#### Slow MongoDB queries

**Solutions:**
1. Add indexes to queried fields
2. Use aggregation pipeline efficiently
3. Limit document size in projections
4. Monitor with explain()

```javascript
// Analyze query
db.pharmacies.find({active: true}).explain("executionStats")

// Add index
db.pharmacies.createIndex({active: 1, createdAt: -1})
```

#### High OpenAI costs

**Solutions:**
1. Switch from GPT-4 to GPT-4o-mini (60% cheaper)
2. Cache common queries
3. Reduce context length
4. Use system prompt optimization

```python
# Enable response caching
from functools import lru_cache

@lru_cache(maxsize=100)
def get_cached_response(question: str):
    return system.query(question)
```

---

### Debugging Tips

#### Enable verbose logging

**Python:**
```python
import logging

logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)
logger.debug("Debug message")
```

**Node.js:**
```typescript
const DEBUG = process.env.DEBUG === 'true';

function log(...args: any[]) {
    if (DEBUG) {
        console.log('[DEBUG]', ...args);
    }
}
```

#### Use breakpoints

**VS Code launch.json:**
```json
{
    "version": "0.2.0",
    "configurations": [
        {
            "name": "Python: Flask",
            "type": "python",
            "request": "launch",
            "module": "flask",
            "env": {
                "FLASK_APP": "web/server_unified.py",
                "FLASK_ENV": "development"
            },
            "args": ["run", "--no-debugger", "--no-reload"],
            "jinja": true
        },
        {
            "name": "Node: MCP Server",
            "type": "node",
            "request": "launch",
            "program": "${workspaceFolder}/dist/index.js",
            "preLaunchTask": "npm: build",
            "outFiles": ["${workspaceFolder}/dist/**/*.js"]
        }
    ]
}
```

---

## 📝 Notes for Future Development

### Planned Features

1. **Authentication Improvements**
   - JWT-based auth for API endpoints
   - Role-based access control (RBAC)
   - OAuth integration (Google, Microsoft)

2. **Query Optimization**
   - Response caching (Redis)
   - Query result pagination
   - Async query execution for long-running queries

3. **Monitoring & Analytics**
   - Query usage analytics
   - Cost tracking dashboard
   - Performance metrics (query time, token usage)
   - Error tracking (Sentry integration)

4. **UI Enhancements**
   - Rich text formatting for responses
   - Export query results (CSV, Excel)
   - Query history with filters
   - Dark mode

5. **Advanced Features**
   - Scheduled queries
   - Query templates
   - Multi-language support (English, Spanish)
   - Voice input

### Technical Debt

1. **Testing**
   - Increase unit test coverage (current: ~40%)
   - Add integration tests for database operations
   - Implement snapshot testing for UI

2. **Documentation**
   - API documentation (OpenAPI/Swagger)
   - Architecture decision records (ADRs)
   - Deployment guide

3. **Code Quality**
   - Add linting (ESLint, Pylint)
   - Implement pre-commit hooks
   - Type checking (mypy for Python)

4. **Infrastructure**
   - Dockerize application
   - CI/CD pipeline (GitHub Actions)
   - Production deployment guide

---

## 🔄 Changelog

### v2.1.0 (2025-01-13)
- feat: Add ChatGPT integration system with streaming support
- feat: Add E2E tests with Playwright
- feat: Integrate ChatGPT API into unified database manager
- feat: Update frontend with ChatGPT toggle and UI enhancements
- docs: Add comprehensive documentation for ChatGPT system
- test: Add debug mode tests

### v2.0.0 (2024-12-20)
- feat: Unified database manager (MySQL + MongoDB)
- feat: MCP server integration
- feat: Automatic query routing
- feat: Streaming responses
- docs: Complete README and setup guides

### v1.0.0 (2024-11-15)
- Initial release
- Basic MySQL query system
- OpenAI integration
- Flask web interface

---

## 🤝 Contributing Guidelines

When contributing to this project:

1. **Read this context file first** to understand the architecture
2. **Follow the Git workflow** (feature branches, PRs to develop)
3. **Write tests** for new features
4. **Update documentation** when changing functionality
5. **Use conventional commits** for clear history
6. **Ask questions** if anything is unclear

---

## 📞 Support & Resources

### Documentation
- Main README: `/README.md`
- ChatGPT System: `/README_CHATGPT_SYSTEM.md`
- API Guide: `/docs/GUIA_CHATGPT_API.md`

### External Resources
- [Flask Documentation](https://flask.palletsprojects.com/)
- [OpenAI API Reference](https://platform.openai.com/docs/)
- [MCP Documentation](https://modelcontextprotocol.io/)
- [Playwright Documentation](https://playwright.dev/)

### Team Contact
- Project: TrendsPro
- Team: AI Luda Team
- Repository: LudaMind

---

**Last Updated:** 2025-01-13
**Maintained by:** AI Luda Team
**Claude Code Version:** 2.1.0
