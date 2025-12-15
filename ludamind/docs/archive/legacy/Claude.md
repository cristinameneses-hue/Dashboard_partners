# Claude Integration Guide - TrendsPro Enterprise Architecture

## 1. Configuración del Proyecto

### 1.1 Estructura de Directorios - Arquitectura de 3 Capas

```
trends_mcp/
├── src/                              # Backend - Python (FastAPI)
│   ├── api/                         # CAPA DE PRESENTACIÓN
│   │   ├── routes/
│   │   │   ├── __init__.py
│   │   │   ├── query_routes.py     # Endpoints de consultas
│   │   │   ├── analytics_routes.py  # Endpoints de analytics
│   │   │   ├── admin_routes.py     # Endpoints administrativos
│   │   │   └── websocket_routes.py # WebSocket para streaming
│   │   ├── middlewares/
│   │   │   ├── auth_middleware.py   # JWT Authentication
│   │   │   ├── cors_middleware.py   # CORS configuration
│   │   │   ├── rate_limit_middleware.py
│   │   │   └── logging_middleware.py
│   │   ├── dependencies/
│   │   │   ├── auth_deps.py        # Authentication dependencies
│   │   │   ├── database_deps.py    # Database session management
│   │   │   └── cache_deps.py       # Cache dependencies
│   │   └── schemas/
│   │       ├── request_schemas.py   # Pydantic request models
│   │       ├── response_schemas.py  # Pydantic response models
│   │       └── error_schemas.py    # Error response models
│   │
│   ├── domain/                      # CAPA DE DOMINIO (Business Logic)
│   │   ├── entities/
│   │   │   ├── __init__.py
│   │   │   ├── query.py            # Query entity
│   │   │   ├── product.py          # Product entity
│   │   │   ├── pharmacy.py         # Pharmacy entity
│   │   │   ├── booking.py          # Booking entity
│   │   │   └── partner.py          # Partner entity
│   │   ├── value_objects/
│   │   │   ├── query_intent.py     # Query intent VO
│   │   │   ├── time_range.py       # Time range VO
│   │   │   ├── gmv.py              # GMV calculation VO
│   │   │   ├── risk_score.py       # Z_Y score VO
│   │   │   └── database_route.py   # Database routing VO
│   │   ├── interfaces/
│   │   │   ├── repositories.py     # Repository interfaces
│   │   │   ├── services.py         # Service interfaces
│   │   │   └── external.py         # External service interfaces
│   │   ├── exceptions/
│   │   │   ├── domain_exceptions.py # Domain-specific exceptions
│   │   │   └── validation_errors.py # Validation exceptions
│   │   └── specifications/
│   │       ├── query_specs.py      # Query specifications
│   │       └── product_specs.py    # Product specifications
│   │
│   ├── application/                 # CAPA DE APLICACIÓN (Use Cases)
│   │   ├── use_cases/
│   │   │   ├── __init__.py
│   │   │   ├── execute_query/
│   │   │   │   ├── execute_query_use_case.py
│   │   │   │   ├── execute_query_dto.py
│   │   │   │   └── execute_query_validator.py
│   │   │   ├── analyze_intent/
│   │   │   │   ├── analyze_intent_use_case.py
│   │   │   │   └── intent_analyzer_service.py
│   │   │   ├── route_database/
│   │   │   │   ├── route_database_use_case.py
│   │   │   │   └── routing_rules_engine.py
│   │   │   ├── format_response/
│   │   │   │   ├── format_response_use_case.py
│   │   │   │   └── response_formatter_service.py
│   │   │   ├── manage_cache/
│   │   │   │   ├── cache_manager_use_case.py
│   │   │   │   └── cache_strategies.py
│   │   │   └── monitor_performance/
│   │   │       ├── performance_monitor_use_case.py
│   │   │       └── metrics_aggregator.py
│   │   ├── services/
│   │   │   ├── query_orchestrator.py    # Main orchestration service
│   │   │   ├── llm_integration.py       # LLM service
│   │   │   ├── streaming_service.py     # SSE streaming
│   │   │   └── notification_service.py  # Alert notifications
│   │   └── dto/
│   │       ├── query_dto.py            # Query DTOs
│   │       ├── response_dto.py         # Response DTOs
│   │       └── analytics_dto.py        # Analytics DTOs
│   │
│   ├── infrastructure/              # CAPA DE INFRAESTRUCTURA
│   │   ├── repositories/
│   │   │   ├── mysql/
│   │   │   │   ├── mysql_query_repository.py
│   │   │   │   ├── mysql_product_repository.py
│   │   │   │   └── mysql_analytics_repository.py
│   │   │   ├── mongodb/
│   │   │   │   ├── mongodb_pharmacy_repository.py
│   │   │   │   ├── mongodb_booking_repository.py
│   │   │   │   └── mongodb_user_repository.py
│   │   │   └── cache/
│   │   │       ├── redis_cache_repository.py
│   │   │       └── memory_cache_repository.py
│   │   ├── external_services/
│   │   │   ├── openai_service.py       # OpenAI integration
│   │   │   ├── chatgpt_service.py      # ChatGPT integration
│   │   │   ├── mcp_client_service.py   # MCP client
│   │   │   └── webhook_service.py      # External webhooks
│   │   ├── database/
│   │   │   ├── mysql_connection.py     # MySQL connection pool
│   │   │   ├── mongodb_connection.py   # MongoDB connection pool
│   │   │   ├── redis_connection.py     # Redis connection
│   │   │   └── migrations/             # Database migrations
│   │   │       ├── mysql/
│   │   │       └── mongodb/
│   │   ├── messaging/
│   │   │   ├── event_bus.py           # Event bus implementation
│   │   │   ├── message_queue.py       # RabbitMQ/Redis Queue
│   │   │   └── websocket_manager.py   # WebSocket connections
│   │   └── monitoring/
│   │       ├── prometheus_metrics.py   # Prometheus integration
│   │       ├── logging_config.py      # Structured logging
│   │       └── tracing_config.py      # OpenTelemetry
│   │
│   ├── shared/                      # CÓDIGO COMPARTIDO
│   │   ├── utils/
│   │   │   ├── datetime_utils.py      # Date/time utilities
│   │   │   ├── string_utils.py        # String manipulation
│   │   │   ├── validation_utils.py    # Common validations
│   │   │   └── encryption_utils.py    # Encryption helpers
│   │   ├── constants/
│   │   │   ├── database_constants.py  # DB constants
│   │   │   ├── routing_keywords.py    # Routing keywords
│   │   │   └── error_codes.py        # Error code definitions
│   │   └── decorators/
│   │       ├── retry_decorator.py     # Retry logic
│   │       ├── cache_decorator.py     # Cache decoration
│   │       ├── timing_decorator.py    # Performance timing
│   │       └── transaction_decorator.py # Transaction management
│   │
│   └── main.py                      # FastAPI application entry point
│
├── frontend/                        # Frontend - React + TypeScript
│   ├── src/
│   │   ├── components/
│   │   │   ├── common/
│   │   │   │   ├── Button/
│   │   │   │   │   ├── Button.tsx
│   │   │   │   │   ├── Button.styles.ts
│   │   │   │   │   ├── Button.test.tsx
│   │   │   │   │   └── Button.stories.tsx
│   │   │   │   ├── Input/
│   │   │   │   ├── Card/
│   │   │   │   └── Modal/
│   │   │   ├── layout/
│   │   │   │   ├── Header/
│   │   │   │   ├── Sidebar/
│   │   │   │   ├── Footer/
│   │   │   │   └── Layout/
│   │   │   └── features/
│   │   │       ├── QueryInterface/
│   │   │       ├── ResultsDisplay/
│   │   │       ├── Analytics/
│   │   │       └── Admin/
│   │   ├── features/
│   │   │   ├── query/
│   │   │   │   ├── components/
│   │   │   │   ├── hooks/
│   │   │   │   ├── services/
│   │   │   │   ├── store/
│   │   │   │   └── types/
│   │   │   ├── analytics/
│   │   │   ├── admin/
│   │   │   └── auth/
│   │   ├── hooks/
│   │   │   ├── useQuery.ts
│   │   │   ├── useWebSocket.ts
│   │   │   ├── useAuth.ts
│   │   │   └── useCache.ts
│   │   ├── services/
│   │   │   ├── api/
│   │   │   │   ├── client.ts
│   │   │   │   ├── endpoints.ts
│   │   │   │   └── interceptors.ts
│   │   │   ├── websocket/
│   │   │   └── storage/
│   │   ├── store/
│   │   │   ├── index.ts
│   │   │   ├── slices/
│   │   │   └── middleware/
│   │   ├── utils/
│   │   ├── types/
│   │   └── App.tsx
│   │
│   ├── public/
│   ├── tests/
│   │   ├── unit/
│   │   ├── integration/
│   │   └── e2e/
│   └── package.json
│
├── tests/                           # Tests (Python)
│   ├── unit/
│   │   ├── domain/
│   │   ├── application/
│   │   └── infrastructure/
│   ├── integration/
│   │   ├── api/
│   │   ├── database/
│   │   └── external/
│   ├── e2e/
│   │   └── scenarios/
│   └── fixtures/
│
├── scripts/
│   ├── generate/
│   │   ├── generate_entity.py      # Entity generator
│   │   ├── generate_use_case.py    # Use case generator
│   │   ├── generate_repository.py  # Repository generator
│   │   └── generate_component.py   # React component generator
│   ├── migration/
│   │   ├── migrate_to_3_layer.py   # 3-layer migration script
│   │   └── refactor_imports.py     # Import refactoring
│   └── deployment/
│       ├── build.sh
│       ├── deploy.sh
│       └── rollback.sh
│
├── docs/
│   ├── architecture/
│   │   ├── ADR/                    # Architecture Decision Records
│   │   ├── diagrams/
│   │   └── patterns/
│   ├── api/
│   │   └── openapi.yaml
│   └── guides/
│
├── .claude/                         # Claude configuration
│   ├── commands/
│   │   ├── generate.md             # Generation commands
│   │   ├── refactor.md             # Refactoring commands
│   │   └── test.md                 # Testing commands
│   └── templates/
│       ├── entity.template.py
│       ├── use_case.template.py
│       └── component.template.tsx
│
├── docker/
│   ├── Dockerfile.backend
│   ├── Dockerfile.frontend
│   └── docker-compose.yml
│
├── kubernetes/
│   ├── deployments/
│   ├── services/
│   ├── configmaps/
│   └── secrets/
│
├── .github/
│   └── workflows/
│       ├── ci.yml
│       ├── cd.yml
│       └── security.yml
│
├── Makefile
├── pyproject.toml
├── poetry.lock
├── package.json
├── package-lock.json
├── tsconfig.json
├── .env.example
├── .gitignore
└── README.md
```

### 1.2 Comandos de Generación

#### Backend (Python) - FastAPI

```bash
# Generar entidad completa con repository y tests
claude generate entity Product \
  --with-repository \
  --with-tests \
  --with-value-objects price,sku,category \
  --layer domain

# Generar caso de uso con todas las capas
claude generate use-case GetTopSellingProducts \
  --layers all \
  --with-dto \
  --with-validator \
  --with-tests

# Generar repositorio con implementaciones
claude generate repository ProductRepository \
  --implementations mysql,mongodb,cache \
  --with-interface \
  --with-tests

# Generar API endpoint completo
claude generate endpoint /api/v1/products \
  --methods GET,POST,PUT,DELETE \
  --with-schemas \
  --with-middleware auth,rate-limit \
  --with-docs

# Generar servicio de aplicación
claude generate service QueryOrchestrator \
  --layer application \
  --dependencies "QueryAnalyzer,DatabaseRouter,ResponseFormatter" \
  --with-tests

# Generar migración de base de datos
claude generate migration AddRiskGroupTable \
  --database mysql \
  --with-rollback
```

#### Frontend (React + TypeScript)

```bash
# Generar componente con todo
claude generate component QueryInterface \
  --with-tests \
  --with-stories \
  --with-styles \
  --with-hooks \
  --type feature

# Generar feature completa
claude generate feature Analytics \
  --with-redux \
  --with-api \
  --with-routing \
  --with-tests

# Generar hook personalizado
claude generate hook useQueryStream \
  --with-cache \
  --with-error-handling \
  --with-tests

# Generar servicio API
claude generate service QueryAPI \
  --with-interceptors \
  --with-retry \
  --with-cache

# Generar slice de Redux
claude generate redux-slice query \
  --with-thunks \
  --with-selectors \
  --with-tests
```

#### Generación de Tests

```bash
# Test unitario con mocks automáticos
claude generate test unit \
  src/application/use_cases/execute_query/execute_query_use_case.py \
  --with-mocks \
  --with-fixtures \
  --coverage 90

# Test de integración
claude generate test integration \
  "Query execution with caching" \
  --components "API,Database,Cache" \
  --with-docker

# Test E2E con Playwright
claude generate test e2e \
  "Complete query flow with streaming" \
  --browser chromium \
  --with-video \
  --with-trace

# Test de carga
claude generate test load \
  --endpoint /api/v1/query \
  --users 1000 \
  --duration 10m \
  --tool k6
```

## 2. Patrones de Código

### 2.1 Backend - Python (FastAPI)

#### Entity Pattern (Domain Layer)

```python
# src/domain/entities/query.py
from dataclasses import dataclass, field
from typing import Optional, List, Dict, Any
from datetime import datetime
from uuid import uuid4

from src.domain.value_objects import QueryIntent, TimeRange, DatabaseRoute
from src.domain.exceptions import DomainException, ValidationError
from src.domain.specifications import QuerySpecification

@dataclass
class Query:
    """Query entity representing a user's database query"""

    # Identity
    id: str = field(default_factory=lambda: str(uuid4()))

    # Properties
    text: str
    intent: Optional[QueryIntent] = None
    time_range: Optional[TimeRange] = None
    database_route: Optional[DatabaseRoute] = None

    # Metadata
    user_id: Optional[str] = None
    session_id: Optional[str] = None
    created_at: datetime = field(default_factory=datetime.utcnow)
    processed_at: Optional[datetime] = None

    # Results
    results: Optional[List[Dict[str, Any]]] = None
    execution_time_ms: Optional[int] = None
    cache_hit: bool = False

    def __post_init__(self):
        """Validate entity after initialization"""
        self.validate()

    def validate(self):
        """Validate query entity"""
        if not self.text or len(self.text.strip()) == 0:
            raise ValidationError("Query text cannot be empty")

        if len(self.text) > 1000:
            raise ValidationError("Query text exceeds maximum length (1000 chars)")

        if self.intent and not self.intent.is_valid():
            raise ValidationError("Invalid query intent")

    def analyze_intent(self, analyzer_service):
        """Analyze query intent using external service"""
        self.intent = analyzer_service.analyze(self.text)
        return self.intent

    def route_to_database(self, router_service):
        """Determine database routing"""
        self.database_route = router_service.route(self.text, self.intent)
        return self.database_route

    def mark_as_processed(self, results: List[Dict[str, Any]],
                          execution_time_ms: int):
        """Mark query as processed with results"""
        self.results = results
        self.execution_time_ms = execution_time_ms
        self.processed_at = datetime.utcnow()

    def satisfies(self, specification: QuerySpecification) -> bool:
        """Check if query satisfies a specification"""
        return specification.is_satisfied_by(self)

    @property
    def is_processed(self) -> bool:
        """Check if query has been processed"""
        return self.processed_at is not None

    @property
    def processing_duration(self) -> Optional[float]:
        """Get processing duration in seconds"""
        if self.processed_at and self.created_at:
            return (self.processed_at - self.created_at).total_seconds()
        return None
```

#### Value Object Pattern

```python
# src/domain/value_objects/query_intent.py
from dataclasses import dataclass
from enum import Enum
from typing import List, Optional

class IntentType(Enum):
    ANALYTICS = "analytics"
    OPERATIONS = "operations"
    REPORTING = "reporting"
    COMPARISON = "comparison"
    AGGREGATION = "aggregation"

@dataclass(frozen=True)
class QueryIntent:
    """Value object representing query intent"""

    type: IntentType
    confidence: float
    entities: List[str]
    sub_intents: Optional[List[str]] = None

    def __post_init__(self):
        if not 0 <= self.confidence <= 1:
            raise ValueError("Confidence must be between 0 and 1")

    def is_valid(self) -> bool:
        return self.confidence >= 0.7

    def requires_clarification(self) -> bool:
        return self.confidence < 0.5

    def __str__(self) -> str:
        return f"{self.type.value} (confidence: {self.confidence:.2f})"
```

#### Repository Pattern (Interface)

```python
# src/domain/interfaces/repositories.py
from abc import ABC, abstractmethod
from typing import Optional, List, Dict, Any
from datetime import datetime

from src.domain.entities import Query

class QueryRepository(ABC):
    """Abstract repository for Query entity"""

    @abstractmethod
    async def save(self, query: Query) -> Query:
        """Save a query"""
        pass

    @abstractmethod
    async def get_by_id(self, query_id: str) -> Optional[Query]:
        """Get query by ID"""
        pass

    @abstractmethod
    async def get_by_user(self, user_id: str,
                          limit: int = 10) -> List[Query]:
        """Get queries by user"""
        pass

    @abstractmethod
    async def get_recent(self,
                         since: datetime,
                         limit: int = 100) -> List[Query]:
        """Get recent queries"""
        pass

    @abstractmethod
    async def search(self,
                    text_pattern: str,
                    filters: Optional[Dict[str, Any]] = None) -> List[Query]:
        """Search queries"""
        pass

    @abstractmethod
    async def update(self, query: Query) -> Query:
        """Update existing query"""
        pass

    @abstractmethod
    async def delete(self, query_id: str) -> bool:
        """Delete query"""
        pass

    @abstractmethod
    async def get_statistics(self,
                            start_date: datetime,
                            end_date: datetime) -> Dict[str, Any]:
        """Get query statistics"""
        pass
```

#### Use Case Pattern (Application Layer)

```python
# src/application/use_cases/execute_query/execute_query_use_case.py
from dataclasses import dataclass
from typing import Optional, Dict, Any
import asyncio
from datetime import datetime

from src.domain.entities import Query
from src.domain.interfaces.repositories import QueryRepository
from src.application.dto import ExecuteQueryDTO, QueryResultDTO
from src.application.services import (
    QueryOrchestrator,
    IntentAnalyzer,
    DatabaseRouter,
    CacheManager,
    ResponseFormatter
)
from src.shared.decorators import timing, retry, transaction

@dataclass
class ExecuteQueryUseCase:
    """Use case for executing database queries"""

    # Dependencies (injected)
    query_repository: QueryRepository
    orchestrator: QueryOrchestrator
    intent_analyzer: IntentAnalyzer
    database_router: DatabaseRouter
    cache_manager: CacheManager
    response_formatter: ResponseFormatter

    @timing
    @retry(max_attempts=3, backoff="exponential")
    @transaction
    async def execute(self, dto: ExecuteQueryDTO) -> QueryResultDTO:
        """
        Execute a query with full processing pipeline

        Args:
            dto: Query execution DTO

        Returns:
            QueryResultDTO with formatted results

        Raises:
            ValidationError: If query is invalid
            DatabaseError: If database operation fails
            TimeoutError: If query exceeds timeout
        """

        # Step 1: Create and validate query entity
        query = Query(
            text=dto.query_text,
            user_id=dto.user_id,
            session_id=dto.session_id
        )

        # Step 2: Check cache
        cache_key = self.cache_manager.generate_key(query.text)
        cached_result = await self.cache_manager.get(cache_key)

        if cached_result and not dto.force_refresh:
            query.cache_hit = True
            query.results = cached_result['data']
            query.execution_time_ms = 0

            # Save query for analytics
            await self.query_repository.save(query)

            return QueryResultDTO(
                query_id=query.id,
                results=cached_result['data'],
                formatted_response=cached_result['formatted'],
                from_cache=True,
                execution_time_ms=0
            )

        # Step 3: Analyze intent
        query.intent = await self.intent_analyzer.analyze(query.text)

        # Step 4: Route to database
        query.database_route = await self.database_router.route(
            query.text,
            query.intent
        )

        # Step 5: Execute query (parallel if multi-database)
        start_time = datetime.utcnow()

        if query.database_route.requires_join:
            # Execute on multiple databases in parallel
            tasks = []
            for db in query.database_route.databases:
                tasks.append(
                    self.orchestrator.execute_on_database(
                        query.text,
                        db,
                        dto.options
                    )
                )

            results = await asyncio.gather(*tasks)
            query.results = self._merge_results(results)
        else:
            # Execute on single database
            query.results = await self.orchestrator.execute_on_database(
                query.text,
                query.database_route.primary_database,
                dto.options
            )

        execution_time = (datetime.utcnow() - start_time).total_seconds() * 1000
        query.execution_time_ms = int(execution_time)

        # Step 6: Format response
        formatted_response = await self.response_formatter.format(
            query.results,
            query.intent,
            dto.format_options
        )

        # Step 7: Update cache
        if execution_time < 5000:  # Only cache fast queries
            await self.cache_manager.set(
                cache_key,
                {
                    'data': query.results,
                    'formatted': formatted_response
                },
                ttl=self._calculate_ttl(query)
            )

        # Step 8: Save query
        query.mark_as_processed(query.results, query.execution_time_ms)
        await self.query_repository.save(query)

        # Step 9: Return result
        return QueryResultDTO(
            query_id=query.id,
            results=query.results,
            formatted_response=formatted_response,
            from_cache=False,
            execution_time_ms=query.execution_time_ms,
            database_used=query.database_route.primary_database,
            intent=str(query.intent) if query.intent else None
        )

    def _merge_results(self, results: list) -> list:
        """Merge results from multiple databases"""
        # Implementation for merging results
        merged = []
        for result_set in results:
            if isinstance(result_set, list):
                merged.extend(result_set)
        return merged

    def _calculate_ttl(self, query: Query) -> int:
        """Calculate cache TTL based on query characteristics"""
        base_ttl = 3600  # 1 hour

        # Adjust based on intent
        if query.intent and query.intent.type.value == "analytics":
            return base_ttl * 4  # 4 hours for analytics
        elif query.intent and query.intent.type.value == "operations":
            return base_ttl // 4  # 15 minutes for operations

        return base_ttl
```

#### Repository Implementation (Infrastructure Layer)

```python
# src/infrastructure/repositories/mysql/mysql_query_repository.py
from typing import Optional, List, Dict, Any
from datetime import datetime
import json
from sqlalchemy import select, insert, update, delete, and_, or_, func
from sqlalchemy.ext.asyncio import AsyncSession

from src.domain.entities import Query
from src.domain.interfaces.repositories import QueryRepository
from src.infrastructure.database.models import QueryModel
from src.shared.decorators import database_transaction

class MySQLQueryRepository(QueryRepository):
    """MySQL implementation of QueryRepository"""

    def __init__(self, session: AsyncSession):
        self.session = session

    @database_transaction
    async def save(self, query: Query) -> Query:
        """Save query to MySQL"""

        query_model = QueryModel(
            id=query.id,
            text=query.text,
            intent=query.intent.type.value if query.intent else None,
            intent_confidence=query.intent.confidence if query.intent else None,
            database_route=query.database_route.primary_database if query.database_route else None,
            user_id=query.user_id,
            session_id=query.session_id,
            created_at=query.created_at,
            processed_at=query.processed_at,
            results=json.dumps(query.results) if query.results else None,
            execution_time_ms=query.execution_time_ms,
            cache_hit=query.cache_hit
        )

        self.session.add(query_model)
        await self.session.commit()

        return query

    async def get_by_id(self, query_id: str) -> Optional[Query]:
        """Get query by ID from MySQL"""

        stmt = select(QueryModel).where(QueryModel.id == query_id)
        result = await self.session.execute(stmt)
        query_model = result.scalar_one_or_none()

        if not query_model:
            return None

        return self._model_to_entity(query_model)

    async def get_by_user(self, user_id: str, limit: int = 10) -> List[Query]:
        """Get queries by user from MySQL"""

        stmt = (
            select(QueryModel)
            .where(QueryModel.user_id == user_id)
            .order_by(QueryModel.created_at.desc())
            .limit(limit)
        )

        result = await self.session.execute(stmt)
        query_models = result.scalars().all()

        return [self._model_to_entity(model) for model in query_models]

    async def get_recent(self, since: datetime, limit: int = 100) -> List[Query]:
        """Get recent queries from MySQL"""

        stmt = (
            select(QueryModel)
            .where(QueryModel.created_at >= since)
            .order_by(QueryModel.created_at.desc())
            .limit(limit)
        )

        result = await self.session.execute(stmt)
        query_models = result.scalars().all()

        return [self._model_to_entity(model) for model in query_models]

    async def search(self, text_pattern: str,
                    filters: Optional[Dict[str, Any]] = None) -> List[Query]:
        """Search queries in MySQL"""

        stmt = select(QueryModel)

        # Add text pattern filter
        if text_pattern:
            stmt = stmt.where(QueryModel.text.like(f"%{text_pattern}%"))

        # Add additional filters
        if filters:
            if 'user_id' in filters:
                stmt = stmt.where(QueryModel.user_id == filters['user_id'])
            if 'intent' in filters:
                stmt = stmt.where(QueryModel.intent == filters['intent'])
            if 'database' in filters:
                stmt = stmt.where(QueryModel.database_route == filters['database'])

        stmt = stmt.order_by(QueryModel.created_at.desc()).limit(100)

        result = await self.session.execute(stmt)
        query_models = result.scalars().all()

        return [self._model_to_entity(model) for model in query_models]

    async def update(self, query: Query) -> Query:
        """Update existing query in MySQL"""

        stmt = (
            update(QueryModel)
            .where(QueryModel.id == query.id)
            .values(
                processed_at=query.processed_at,
                results=json.dumps(query.results) if query.results else None,
                execution_time_ms=query.execution_time_ms,
                cache_hit=query.cache_hit
            )
        )

        await self.session.execute(stmt)
        await self.session.commit()

        return query

    async def delete(self, query_id: str) -> bool:
        """Delete query from MySQL"""

        stmt = delete(QueryModel).where(QueryModel.id == query_id)
        result = await self.session.execute(stmt)
        await self.session.commit()

        return result.rowcount > 0

    async def get_statistics(self, start_date: datetime,
                            end_date: datetime) -> Dict[str, Any]:
        """Get query statistics from MySQL"""

        # Total queries
        total_stmt = (
            select(func.count(QueryModel.id))
            .where(and_(
                QueryModel.created_at >= start_date,
                QueryModel.created_at <= end_date
            ))
        )
        total_result = await self.session.execute(total_stmt)
        total_queries = total_result.scalar()

        # Average execution time
        avg_time_stmt = (
            select(func.avg(QueryModel.execution_time_ms))
            .where(and_(
                QueryModel.created_at >= start_date,
                QueryModel.created_at <= end_date,
                QueryModel.execution_time_ms.isnot(None)
            ))
        )
        avg_time_result = await self.session.execute(avg_time_stmt)
        avg_execution_time = avg_time_result.scalar() or 0

        # Cache hit rate
        cache_hits_stmt = (
            select(func.count(QueryModel.id))
            .where(and_(
                QueryModel.created_at >= start_date,
                QueryModel.created_at <= end_date,
                QueryModel.cache_hit == True
            ))
        )
        cache_hits_result = await self.session.execute(cache_hits_stmt)
        cache_hits = cache_hits_result.scalar()

        # Intent distribution
        intent_stmt = (
            select(
                QueryModel.intent,
                func.count(QueryModel.id).label('count')
            )
            .where(and_(
                QueryModel.created_at >= start_date,
                QueryModel.created_at <= end_date,
                QueryModel.intent.isnot(None)
            ))
            .group_by(QueryModel.intent)
        )
        intent_result = await self.session.execute(intent_stmt)
        intent_distribution = {
            row.intent: row.count for row in intent_result
        }

        return {
            'total_queries': total_queries,
            'average_execution_time_ms': float(avg_execution_time),
            'cache_hit_rate': (cache_hits / total_queries) if total_queries > 0 else 0,
            'intent_distribution': intent_distribution,
            'period': {
                'start': start_date.isoformat(),
                'end': end_date.isoformat()
            }
        }

    def _model_to_entity(self, model: QueryModel) -> Query:
        """Convert SQLAlchemy model to domain entity"""

        from src.domain.value_objects import QueryIntent, IntentType, DatabaseRoute

        # Reconstruct intent if available
        intent = None
        if model.intent:
            intent = QueryIntent(
                type=IntentType(model.intent),
                confidence=model.intent_confidence or 0.0,
                entities=[]  # Would need to store/retrieve separately
            )

        # Reconstruct database route if available
        database_route = None
        if model.database_route:
            database_route = DatabaseRoute(
                primary_database=model.database_route,
                databases=[model.database_route],
                requires_join=False
            )

        return Query(
            id=model.id,
            text=model.text,
            intent=intent,
            database_route=database_route,
            user_id=model.user_id,
            session_id=model.session_id,
            created_at=model.created_at,
            processed_at=model.processed_at,
            results=json.loads(model.results) if model.results else None,
            execution_time_ms=model.execution_time_ms,
            cache_hit=model.cache_hit
        )
```

#### API Route Pattern (Presentation Layer)

```python
# src/api/routes/query_routes.py
from typing import Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, Query as QueryParam, BackgroundTasks
from fastapi.responses import StreamingResponse
from sse_starlette.sse import EventSourceResponse
import asyncio
import json

from src.api.dependencies import get_current_user, get_query_use_case, rate_limit
from src.api.schemas import (
    QueryRequest,
    QueryResponse,
    QueryStreamResponse,
    ErrorResponse
)
from src.application.use_cases import ExecuteQueryUseCase
from src.application.dto import ExecuteQueryDTO
from src.domain.exceptions import ValidationError, DatabaseError
from src.shared.decorators import api_timing, api_error_handler

router = APIRouter(
    prefix="/api/v1/queries",
    tags=["queries"],
    responses={
        400: {"model": ErrorResponse, "description": "Bad Request"},
        401: {"model": ErrorResponse, "description": "Unauthorized"},
        429: {"model": ErrorResponse, "description": "Too Many Requests"},
        500: {"model": ErrorResponse, "description": "Internal Server Error"}
    }
)

@router.post(
    "/",
    response_model=QueryResponse,
    summary="Execute a database query",
    description="Execute a natural language query against MySQL or MongoDB"
)
@api_timing
@api_error_handler
@rate_limit(requests_per_minute=60)
async def execute_query(
    request: QueryRequest,
    background_tasks: BackgroundTasks,
    current_user: Dict = Depends(get_current_user),
    use_case: ExecuteQueryUseCase = Depends(get_query_use_case)
) -> QueryResponse:
    """
    Execute a database query

    Args:
        request: Query request with natural language text
        background_tasks: FastAPI background tasks
        current_user: Authenticated user
        use_case: Query execution use case

    Returns:
        QueryResponse with results and metadata

    Raises:
        HTTPException: On validation or execution errors
    """

    try:
        # Create DTO
        dto = ExecuteQueryDTO(
            query_text=request.query,
            user_id=current_user['id'],
            session_id=request.session_id,
            options={
                'limit': request.limit,
                'timeout_seconds': request.timeout_seconds,
                'use_cache': request.use_cache
            },
            format_options={
                'format': request.response_format,
                'include_metadata': request.include_metadata
            },
            force_refresh=request.force_refresh
        )

        # Execute use case
        result = await use_case.execute(dto)

        # Schedule background analytics
        background_tasks.add_task(
            log_query_analytics,
            query_id=result.query_id,
            user_id=current_user['id'],
            execution_time_ms=result.execution_time_ms
        )

        # Return response
        return QueryResponse(
            query_id=result.query_id,
            results=result.results,
            formatted_response=result.formatted_response,
            metadata={
                'from_cache': result.from_cache,
                'execution_time_ms': result.execution_time_ms,
                'database_used': result.database_used,
                'intent': result.intent,
                'result_count': len(result.results) if result.results else 0
            }
        )

    except ValidationError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except DatabaseError as e:
        raise HTTPException(status_code=500, detail="Database error occurred")
    except Exception as e:
        raise HTTPException(status_code=500, detail="Internal server error")

@router.post(
    "/stream",
    summary="Execute a streaming query",
    description="Execute a query with Server-Sent Events streaming response"
)
@rate_limit(requests_per_minute=30)
async def execute_streaming_query(
    request: QueryRequest,
    current_user: Dict = Depends(get_current_user),
    use_case: ExecuteQueryUseCase = Depends(get_query_use_case)
):
    """
    Execute a streaming query with SSE

    Returns:
        EventSourceResponse with streaming results
    """

    async def generate():
        """Generate streaming events"""

        try:
            # Send initial event
            yield {
                "event": "start",
                "data": json.dumps({
                    "message": "Processing query...",
                    "timestamp": datetime.utcnow().isoformat()
                })
            }

            # Create DTO
            dto = ExecuteQueryDTO(
                query_text=request.query,
                user_id=current_user['id'],
                session_id=request.session_id,
                options={'streaming': True}
            )

            # Execute with streaming
            async for chunk in use_case.execute_streaming(dto):
                yield {
                    "event": "data",
                    "data": json.dumps({
                        "type": chunk.type,
                        "content": chunk.content
                    })
                }

                # Small delay for demonstration
                await asyncio.sleep(0.01)

            # Send completion event
            yield {
                "event": "complete",
                "data": json.dumps({
                    "message": "Query completed",
                    "timestamp": datetime.utcnow().isoformat()
                })
            }

        except Exception as e:
            yield {
                "event": "error",
                "data": json.dumps({
                    "error": str(e),
                    "timestamp": datetime.utcnow().isoformat()
                })
            }

    return EventSourceResponse(generate())

@router.get(
    "/{query_id}",
    response_model=QueryResponse,
    summary="Get query by ID",
    description="Retrieve a previously executed query by its ID"
)
async def get_query(
    query_id: str,
    current_user: Dict = Depends(get_current_user),
    use_case: ExecuteQueryUseCase = Depends(get_query_use_case)
) -> QueryResponse:
    """Get query details by ID"""

    query = await use_case.query_repository.get_by_id(query_id)

    if not query:
        raise HTTPException(status_code=404, detail="Query not found")

    # Check authorization
    if query.user_id != current_user['id']:
        raise HTTPException(status_code=403, detail="Access denied")

    return QueryResponse(
        query_id=query.id,
        results=query.results,
        formatted_response=None,  # Would need to re-format
        metadata={
            'from_cache': query.cache_hit,
            'execution_time_ms': query.execution_time_ms,
            'created_at': query.created_at.isoformat(),
            'processed_at': query.processed_at.isoformat() if query.processed_at else None
        }
    )

@router.get(
    "/",
    response_model=List[QueryResponse],
    summary="List user queries",
    description="Get list of queries executed by the current user"
)
async def list_queries(
    limit: int = QueryParam(10, ge=1, le=100),
    offset: int = QueryParam(0, ge=0),
    current_user: Dict = Depends(get_current_user),
    use_case: ExecuteQueryUseCase = Depends(get_query_use_case)
) -> List[QueryResponse]:
    """List queries for current user"""

    queries = await use_case.query_repository.get_by_user(
        user_id=current_user['id'],
        limit=limit
    )

    return [
        QueryResponse(
            query_id=query.id,
            results=query.results[:10] if query.results else None,  # Truncate
            formatted_response=None,
            metadata={
                'created_at': query.created_at.isoformat(),
                'intent': str(query.intent) if query.intent else None
            }
        )
        for query in queries
    ]

async def log_query_analytics(query_id: str, user_id: str,
                              execution_time_ms: int):
    """Background task to log query analytics"""
    # Implementation for analytics logging
    pass
```

### 2.2 Frontend - React + TypeScript

#### Component Pattern with Hooks

```typescript
// frontend/src/components/features/QueryInterface/QueryInterface.tsx
import React, { memo, useState, useCallback, useEffect } from 'react';
import { useDispatch, useSelector } from 'react-redux';
import { styled } from '@mui/material/styles';
import {
  Box,
  TextField,
  Button,
  CircularProgress,
  Alert,
  Chip,
  Autocomplete
} from '@mui/material';
import SendIcon from '@mui/icons-material/Send';
import HistoryIcon from '@mui/icons-material/History';

import { useQuery } from '../../../hooks/useQuery';
import { useWebSocket } from '../../../hooks/useWebSocket';
import { useDebounce } from '../../../hooks/useDebounce';
import { QuerySuggestions } from './QuerySuggestions';
import { QueryHistory } from './QueryHistory';
import { ResultsDisplay } from '../ResultsDisplay';
import { queryActions, selectQueryState } from '../../../store/slices/querySlice';
import { QueryRequest, QueryResponse } from '../../../types';

// Styled Components
const Container = styled(Box)(({ theme }) => ({
  display: 'flex',
  flexDirection: 'column',
  gap: theme.spacing(2),
  padding: theme.spacing(3),
  maxWidth: '1200px',
  margin: '0 auto'
}));

const QueryInput = styled(Box)(({ theme }) => ({
  display: 'flex',
  gap: theme.spacing(2),
  alignItems: 'flex-start'
}));

const StyledTextField = styled(TextField)(({ theme }) => ({
  flexGrow: 1,
  '& .MuiOutlinedInput-root': {
    borderRadius: theme.spacing(2),
    backgroundColor: theme.palette.background.paper
  }
}));

const SubmitButton = styled(Button)(({ theme }) => ({
  borderRadius: theme.spacing(2),
  padding: theme.spacing(1.5, 3),
  minWidth: '120px'
}));

// Component Props
interface QueryInterfaceProps {
  onQuerySubmit?: (query: string) => void;
  initialQuery?: string;
  enableStreaming?: boolean;
  showHistory?: boolean;
  maxHistoryItems?: number;
}

// Main Component
export const QueryInterface: React.FC<QueryInterfaceProps> = memo(({
  onQuerySubmit,
  initialQuery = '',
  enableStreaming = true,
  showHistory = true,
  maxHistoryItems = 10
}) => {
  // State
  const [query, setQuery] = useState(initialQuery);
  const [isStreaming, setIsStreaming] = useState(false);
  const [streamedContent, setStreamedContent] = useState('');

  // Redux
  const dispatch = useDispatch();
  const {
    isLoading,
    results,
    error,
    history
  } = useSelector(selectQueryState);

  // Custom Hooks
  const debouncedQuery = useDebounce(query, 300);
  const { executeQuery, cancelQuery } = useQuery();

  // WebSocket for streaming
  const {
    sendMessage,
    lastMessage,
    readyState
  } = useWebSocket('/ws/query', {
    enabled: enableStreaming,
    reconnectInterval: 3000
  });

  // Callbacks
  const handleQueryChange = useCallback((
    event: React.ChangeEvent<HTMLInputElement>
  ) => {
    setQuery(event.target.value);
  }, []);

  const handleSubmit = useCallback(async (
    event?: React.FormEvent
  ) => {
    if (event) {
      event.preventDefault();
    }

    if (!query.trim()) {
      return;
    }

    // Callback to parent
    onQuerySubmit?.(query);

    // Add to history
    dispatch(queryActions.addToHistory(query));

    if (enableStreaming && readyState === WebSocket.OPEN) {
      // Use WebSocket for streaming
      setIsStreaming(true);
      setStreamedContent('');

      sendMessage({
        type: 'query',
        payload: { query }
      });
    } else {
      // Use regular HTTP request
      const request: QueryRequest = {
        query,
        useCache: true,
        responseFormat: 'markdown',
        includeMetadata: true
      };

      await executeQuery(request);
    }
  }, [query, enableStreaming, readyState, sendMessage, executeQuery, dispatch, onQuerySubmit]);

  const handleHistorySelect = useCallback((historicalQuery: string) => {
    setQuery(historicalQuery);
  }, []);

  const handleSuggestionSelect = useCallback((suggestion: string) => {
    setQuery(suggestion);
    // Auto-submit on suggestion select
    setTimeout(() => handleSubmit(), 100);
  }, [handleSubmit]);

  // Effects
  useEffect(() => {
    // Handle streaming messages
    if (lastMessage && isStreaming) {
      const data = JSON.parse(lastMessage.data);

      switch (data.event) {
        case 'data':
          setStreamedContent(prev => prev + data.content);
          break;
        case 'complete':
          setIsStreaming(false);
          dispatch(queryActions.setResults({
            results: [],
            formattedResponse: streamedContent
          }));
          break;
        case 'error':
          setIsStreaming(false);
          dispatch(queryActions.setError(data.error));
          break;
      }
    }
  }, [lastMessage, isStreaming, streamedContent, dispatch]);

  // Render helpers
  const renderQueryExamples = () => {
    const examples = [
      '¿Cuáles son los 10 productos más vendidos?',
      'GMV de Glovo esta semana',
      '¿Cuántas farmacias activas tenemos?',
      'Productos en grupo de riesgo 3'
    ];

    return (
      <Box sx={{ display: 'flex', gap: 1, flexWrap: 'wrap', mb: 2 }}>
        {examples.map((example, index) => (
          <Chip
            key={index}
            label={example}
            variant="outlined"
            onClick={() => setQuery(example)}
            sx={{ cursor: 'pointer' }}
          />
        ))}
      </Box>
    );
  };

  // Main render
  return (
    <Container>
      {/* Query Examples */}
      {!query && renderQueryExamples()}

      {/* Query Input */}
      <form onSubmit={handleSubmit}>
        <QueryInput>
          <StyledTextField
            fullWidth
            multiline
            maxRows={4}
            value={query}
            onChange={handleQueryChange}
            placeholder="Escribe tu consulta en lenguaje natural..."
            disabled={isLoading || isStreaming}
            InputProps={{
              endAdornment: query.length > 0 && (
                <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                  <Chip
                    size="small"
                    label={`${query.length}/1000`}
                    color={query.length > 900 ? 'warning' : 'default'}
                  />
                </Box>
              )
            }}
          />

          <SubmitButton
            type="submit"
            variant="contained"
            disabled={!query.trim() || isLoading || isStreaming}
            startIcon={
              isLoading || isStreaming ?
              <CircularProgress size={20} /> :
              <SendIcon />
            }
          >
            {isLoading || isStreaming ? 'Procesando...' : 'Consultar'}
          </SubmitButton>
        </QueryInput>
      </form>

      {/* Query Suggestions */}
      {debouncedQuery.length > 2 && (
        <QuerySuggestions
          query={debouncedQuery}
          onSelect={handleSuggestionSelect}
        />
      )}

      {/* Error Display */}
      {error && (
        <Alert severity="error" onClose={() => dispatch(queryActions.clearError())}>
          {error}
        </Alert>
      )}

      {/* Results Display */}
      {(results || streamedContent) && (
        <ResultsDisplay
          results={results}
          formattedResponse={streamedContent || undefined}
          isStreaming={isStreaming}
        />
      )}

      {/* Query History */}
      {showHistory && history.length > 0 && (
        <QueryHistory
          queries={history.slice(0, maxHistoryItems)}
          onSelect={handleHistorySelect}
        />
      )}
    </Container>
  );
});

QueryInterface.displayName = 'QueryInterface';
```

#### Custom Hook Pattern

```typescript
// frontend/src/hooks/useQuery.ts
import { useState, useCallback, useRef } from 'react';
import { useDispatch } from 'react-redux';
import { queryAPI } from '../services/api';
import { queryActions } from '../store/slices/querySlice';
import {
  QueryRequest,
  QueryResponse,
  QueryError
} from '../types';
import { useCache } from './useCache';
import { useRetry } from './useRetry';

interface UseQueryOptions {
  cacheKey?: string;
  cacheTTL?: number;
  retryAttempts?: number;
  retryDelay?: number;
  onSuccess?: (response: QueryResponse) => void;
  onError?: (error: QueryError) => void;
}

export const useQuery = (options: UseQueryOptions = {}) => {
  const {
    cacheKey,
    cacheTTL = 3600000, // 1 hour
    retryAttempts = 3,
    retryDelay = 1000,
    onSuccess,
    onError
  } = options;

  const dispatch = useDispatch();
  const abortControllerRef = useRef<AbortController | null>(null);

  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<QueryError | null>(null);
  const [data, setData] = useState<QueryResponse | null>(null);

  const { get: getFromCache, set: setInCache } = useCache();
  const { retry } = useRetry({ attempts: retryAttempts, delay: retryDelay });

  const executeQuery = useCallback(async (
    request: QueryRequest
  ): Promise<QueryResponse | null> => {
    // Cancel previous request if exists
    if (abortControllerRef.current) {
      abortControllerRef.current.abort();
    }

    // Create new abort controller
    abortControllerRef.current = new AbortController();

    // Check cache first
    const cacheKeyToUse = cacheKey || `query:${JSON.stringify(request)}`;
    const cachedData = getFromCache<QueryResponse>(cacheKeyToUse);

    if (cachedData && request.useCache !== false) {
      setData(cachedData);
      dispatch(queryActions.setResults(cachedData));
      onSuccess?.(cachedData);
      return cachedData;
    }

    setIsLoading(true);
    setError(null);
    dispatch(queryActions.setLoading(true));

    try {
      const response = await retry(async () => {
        return await queryAPI.execute(request, {
          signal: abortControllerRef.current?.signal
        });
      });

      // Cache the response
      if (response && request.useCache !== false) {
        setInCache(cacheKeyToUse, response, cacheTTL);
      }

      setData(response);
      dispatch(queryActions.setResults(response));
      onSuccess?.(response);

      return response;
    } catch (err) {
      const queryError = err as QueryError;

      setError(queryError);
      dispatch(queryActions.setError(queryError.message));
      onError?.(queryError);

      return null;
    } finally {
      setIsLoading(false);
      dispatch(queryActions.setLoading(false));
    }
  }, [cacheKey, cacheTTL, dispatch, getFromCache, setInCache, retry, onSuccess, onError]);

  const cancelQuery = useCallback(() => {
    if (abortControllerRef.current) {
      abortControllerRef.current.abort();
      abortControllerRef.current = null;
      setIsLoading(false);
      dispatch(queryActions.setLoading(false));
    }
  }, [dispatch]);

  const clearCache = useCallback(() => {
    if (cacheKey) {
      localStorage.removeItem(cacheKey);
    }
  }, [cacheKey]);

  return {
    executeQuery,
    cancelQuery,
    clearCache,
    isLoading,
    error,
    data
  };
};

// Specialized hook for streaming queries
export const useStreamingQuery = () => {
  const [chunks, setChunks] = useState<string[]>([]);
  const [isStreaming, setIsStreaming] = useState(false);
  const eventSourceRef = useRef<EventSource | null>(null);

  const startStreaming = useCallback(async (
    request: QueryRequest
  ) => {
    // Close existing connection
    if (eventSourceRef.current) {
      eventSourceRef.current.close();
    }

    setIsStreaming(true);
    setChunks([]);

    const url = `/api/v1/queries/stream`;
    const params = new URLSearchParams({
      query: request.query,
      useCache: String(request.useCache),
      format: request.responseFormat || 'markdown'
    });

    eventSourceRef.current = new EventSource(`${url}?${params}`);

    eventSourceRef.current.addEventListener('data', (event) => {
      const data = JSON.parse(event.data);
      setChunks(prev => [...prev, data.content]);
    });

    eventSourceRef.current.addEventListener('complete', () => {
      setIsStreaming(false);
      eventSourceRef.current?.close();
    });

    eventSourceRef.current.addEventListener('error', (error) => {
      console.error('Streaming error:', error);
      setIsStreaming(false);
      eventSourceRef.current?.close();
    });
  }, []);

  const stopStreaming = useCallback(() => {
    if (eventSourceRef.current) {
      eventSourceRef.current.close();
      eventSourceRef.current = null;
    }
    setIsStreaming(false);
  }, []);

  return {
    startStreaming,
    stopStreaming,
    chunks,
    isStreaming,
    fullContent: chunks.join('')
  };
};
```

#### Redux Slice Pattern (Redux Toolkit)

```typescript
// frontend/src/store/slices/querySlice.ts
import { createSlice, createAsyncThunk, PayloadAction } from '@reduxjs/toolkit';
import { RootState } from '../index';
import { queryAPI } from '../../services/api';
import {
  QueryRequest,
  QueryResponse,
  QueryHistoryItem,
  QueryState
} from '../../types';

// Initial state
const initialState: QueryState = {
  isLoading: false,
  error: null,
  results: null,
  formattedResponse: null,
  metadata: null,
  history: [],
  suggestions: [],
  activeQueryId: null,
  filters: {
    database: 'auto',
    timeRange: 'last7days',
    limit: 100
  }
};

// Async thunks
export const executeQueryAsync = createAsyncThunk(
  'query/execute',
  async (request: QueryRequest, { rejectWithValue }) => {
    try {
      const response = await queryAPI.execute(request);
      return response;
    } catch (error: any) {
      return rejectWithValue(error.message || 'Query execution failed');
    }
  }
);

export const fetchQueryHistory = createAsyncThunk(
  'query/fetchHistory',
  async (userId: string) => {
    const history = await queryAPI.getHistory(userId);
    return history;
  }
);

export const fetchSuggestions = createAsyncThunk(
  'query/fetchSuggestions',
  async (partialQuery: string) => {
    const suggestions = await queryAPI.getSuggestions(partialQuery);
    return suggestions;
  }
);

// Slice
const querySlice = createSlice({
  name: 'query',
  initialState,
  reducers: {
    // Synchronous actions
    setLoading: (state, action: PayloadAction<boolean>) => {
      state.isLoading = action.payload;
    },

    setError: (state, action: PayloadAction<string | null>) => {
      state.error = action.payload;
    },

    clearError: (state) => {
      state.error = null;
    },

    setResults: (state, action: PayloadAction<Partial<QueryResponse>>) => {
      state.results = action.payload.results || null;
      state.formattedResponse = action.payload.formattedResponse || null;
      state.metadata = action.payload.metadata || null;
    },

    clearResults: (state) => {
      state.results = null;
      state.formattedResponse = null;
      state.metadata = null;
    },

    addToHistory: (state, action: PayloadAction<string>) => {
      const historyItem: QueryHistoryItem = {
        id: Date.now().toString(),
        query: action.payload,
        timestamp: new Date().toISOString(),
        success: true
      };

      // Add to beginning and limit to 50 items
      state.history = [historyItem, ...state.history].slice(0, 50);

      // Persist to localStorage
      localStorage.setItem('queryHistory', JSON.stringify(state.history));
    },

    removeFromHistory: (state, action: PayloadAction<string>) => {
      state.history = state.history.filter(item => item.id !== action.payload);
      localStorage.setItem('queryHistory', JSON.stringify(state.history));
    },

    clearHistory: (state) => {
      state.history = [];
      localStorage.removeItem('queryHistory');
    },

    setSuggestions: (state, action: PayloadAction<string[]>) => {
      state.suggestions = action.payload;
    },

    updateFilters: (state, action: PayloadAction<Partial<QueryState['filters']>>) => {
      state.filters = {
        ...state.filters,
        ...action.payload
      };
    },

    setActiveQueryId: (state, action: PayloadAction<string | null>) => {
      state.activeQueryId = action.payload;
    }
  },

  extraReducers: (builder) => {
    builder
      // Execute query
      .addCase(executeQueryAsync.pending, (state) => {
        state.isLoading = true;
        state.error = null;
      })
      .addCase(executeQueryAsync.fulfilled, (state, action) => {
        state.isLoading = false;
        state.results = action.payload.results;
        state.formattedResponse = action.payload.formattedResponse;
        state.metadata = action.payload.metadata;
        state.activeQueryId = action.payload.queryId;
      })
      .addCase(executeQueryAsync.rejected, (state, action) => {
        state.isLoading = false;
        state.error = action.payload as string;
      })

      // Fetch history
      .addCase(fetchQueryHistory.fulfilled, (state, action) => {
        state.history = action.payload;
      })

      // Fetch suggestions
      .addCase(fetchSuggestions.fulfilled, (state, action) => {
        state.suggestions = action.payload;
      });
  }
});

// Export actions
export const queryActions = querySlice.actions;

// Export selectors
export const selectQueryState = (state: RootState) => state.query;
export const selectIsLoading = (state: RootState) => state.query.isLoading;
export const selectQueryResults = (state: RootState) => state.query.results;
export const selectQueryError = (state: RootState) => state.query.error;
export const selectQueryHistory = (state: RootState) => state.query.history;
export const selectQuerySuggestions = (state: RootState) => state.query.suggestions;
export const selectQueryFilters = (state: RootState) => state.query.filters;

// Export reducer
export default querySlice.reducer;
```

## 3. Principios SOLID Aplicados

### S - Single Responsibility Principle

```python
# ❌ BAD: Multiple responsibilities
class QueryService:
    def analyze_intent(self, query):
        # NLP processing
        pass

    def route_to_database(self, query):
        # Database routing
        pass

    def execute_query(self, query):
        # Query execution
        pass

    def format_response(self, results):
        # Response formatting
        pass

    def send_email(self, results):
        # Email notification
        pass

# ✅ GOOD: Single responsibility per class
class IntentAnalyzer:
    """Responsible only for intent analysis"""
    def analyze(self, query: str) -> QueryIntent:
        pass

class DatabaseRouter:
    """Responsible only for database routing"""
    def route(self, query: str, intent: QueryIntent) -> DatabaseRoute:
        pass

class QueryExecutor:
    """Responsible only for query execution"""
    def execute(self, query: str, database: str) -> List[Dict]:
        pass

class ResponseFormatter:
    """Responsible only for response formatting"""
    def format(self, results: List[Dict], intent: QueryIntent) -> str:
        pass

class NotificationService:
    """Responsible only for notifications"""
    def send_email(self, recipient: str, content: str) -> bool:
        pass
```

### O - Open/Closed Principle

```python
# ✅ Open for extension, closed for modification

from abc import ABC, abstractmethod

# Base abstraction
class DataProcessor(ABC):
    """Abstract processor - closed for modification"""

    @abstractmethod
    def process(self, data: Any) -> Any:
        pass

    @abstractmethod
    def validate(self, data: Any) -> bool:
        pass

# Extensions - open for extension
class MySQLProcessor(DataProcessor):
    """MySQL-specific implementation"""

    def process(self, data: Any) -> Any:
        # MySQL-specific processing
        return self._execute_sql(data)

    def validate(self, data: Any) -> bool:
        # SQL validation
        return self._validate_sql(data)

    def _execute_sql(self, sql: str):
        # MySQL execution
        pass

    def _validate_sql(self, sql: str) -> bool:
        # SQL validation logic
        pass

class MongoDBProcessor(DataProcessor):
    """MongoDB-specific implementation"""

    def process(self, data: Any) -> Any:
        # MongoDB-specific processing
        return self._execute_aggregation(data)

    def validate(self, data: Any) -> bool:
        # MongoDB validation
        return self._validate_pipeline(data)

    def _execute_aggregation(self, pipeline: List):
        # MongoDB execution
        pass

    def _validate_pipeline(self, pipeline: List) -> bool:
        # Pipeline validation
        pass

# New processor can be added without modifying existing code
class ElasticsearchProcessor(DataProcessor):
    """Elasticsearch implementation - extending without modifying"""

    def process(self, data: Any) -> Any:
        return self._execute_search(data)

    def validate(self, data: Any) -> bool:
        return self._validate_query(data)

# Usage - polymorphic
def execute_data_processing(processor: DataProcessor, data: Any):
    """Works with any DataProcessor implementation"""
    if processor.validate(data):
        return processor.process(data)
    raise ValueError("Invalid data for processor")
```

### L - Liskov Substitution Principle

```python
# ✅ Derived classes can substitute base classes

class Repository(ABC):
    """Base repository interface"""

    @abstractmethod
    async def find(self, id: str) -> Optional[Entity]:
        """Find entity by ID"""
        pass

    @abstractmethod
    async def save(self, entity: Entity) -> Entity:
        """Save entity"""
        pass

    @abstractmethod
    async def delete(self, id: str) -> bool:
        """Delete entity"""
        pass

class CachedRepository(Repository):
    """Repository with caching - maintains LSP"""

    def __init__(self, base_repository: Repository, cache: Cache):
        self.base_repository = base_repository
        self.cache = cache

    async def find(self, id: str) -> Optional[Entity]:
        # Check cache first
        cached = await self.cache.get(id)
        if cached:
            return cached

        # Fallback to base repository
        entity = await self.base_repository.find(id)
        if entity:
            await self.cache.set(id, entity)
        return entity

    async def save(self, entity: Entity) -> Entity:
        # Save to base repository
        saved = await self.base_repository.save(entity)
        # Update cache
        await self.cache.set(saved.id, saved)
        return saved

    async def delete(self, id: str) -> bool:
        # Delete from base repository
        deleted = await self.base_repository.delete(id)
        # Invalidate cache
        if deleted:
            await self.cache.delete(id)
        return deleted

# Both can be used interchangeably
async def process_entity(repository: Repository, entity_id: str):
    """Works with any Repository implementation"""
    entity = await repository.find(entity_id)
    if entity:
        entity.process()
        await repository.save(entity)
```

### I - Interface Segregation Principle

```python
# ❌ BAD: Fat interface
class DataService:
    def read(self): pass
    def write(self): pass
    def delete(self): pass
    def backup(self): pass
    def restore(self): pass
    def compress(self): pass
    def encrypt(self): pass
    def analyze(self): pass

# ✅ GOOD: Segregated interfaces
class Readable(ABC):
    @abstractmethod
    async def read(self, key: str) -> Any:
        pass

class Writable(ABC):
    @abstractmethod
    async def write(self, key: str, value: Any) -> bool:
        pass

class Deletable(ABC):
    @abstractmethod
    async def delete(self, key: str) -> bool:
        pass

class Backupable(ABC):
    @abstractmethod
    async def backup(self) -> str:
        pass

    @abstractmethod
    async def restore(self, backup_id: str) -> bool:
        pass

class Compressible(ABC):
    @abstractmethod
    def compress(self, data: bytes) -> bytes:
        pass

    @abstractmethod
    def decompress(self, data: bytes) -> bytes:
        pass

# Implementations use only what they need
class ReadOnlyCache(Readable):
    """Only implements reading"""
    async def read(self, key: str) -> Any:
        return self.cache.get(key)

class ReadWriteCache(Readable, Writable, Deletable):
    """Implements reading, writing, and deleting"""
    async def read(self, key: str) -> Any:
        return self.cache.get(key)

    async def write(self, key: str, value: Any) -> bool:
        return self.cache.set(key, value)

    async def delete(self, key: str) -> bool:
        return self.cache.delete(key)

class BackupableDatabase(Readable, Writable, Deletable, Backupable):
    """Full-featured database with backup"""
    # Implements all necessary interfaces
    pass
```

### D - Dependency Inversion Principle

```python
# ✅ Depend on abstractions, not concretions

# High-level module
class QueryOrchestrator:
    """High-level orchestration - depends on abstractions"""

    def __init__(
        self,
        analyzer: IntentAnalyzerInterface,
        router: DatabaseRouterInterface,
        executor: QueryExecutorInterface,
        formatter: ResponseFormatterInterface
    ):
        # Dependencies are injected as interfaces
        self.analyzer = analyzer
        self.router = router
        self.executor = executor
        self.formatter = formatter

    async def process_query(self, query_text: str) -> str:
        # Works with abstractions
        intent = await self.analyzer.analyze(query_text)
        database = await self.router.route(query_text, intent)
        results = await self.executor.execute(query_text, database)
        response = await self.formatter.format(results, intent)
        return response

# Dependency injection container
from dependency_injector import containers, providers

class Container(containers.DeclarativeContainer):
    """DI Container for dependency management"""

    # Configuration
    config = providers.Configuration()

    # Infrastructure
    mysql_connection = providers.Singleton(
        MySQLConnection,
        url=config.mysql_url
    )

    mongodb_connection = providers.Singleton(
        MongoDBConnection,
        url=config.mongodb_url
    )

    redis_client = providers.Singleton(
        RedisClient,
        url=config.redis_url
    )

    # Services
    intent_analyzer = providers.Singleton(
        OpenAIIntentAnalyzer,
        api_key=config.openai_api_key
    )

    database_router = providers.Singleton(
        SmartDatabaseRouter,
        mysql_keywords=config.mysql_keywords,
        mongodb_keywords=config.mongodb_keywords
    )

    query_executor = providers.Factory(
        UnifiedQueryExecutor,
        mysql_conn=mysql_connection,
        mongodb_conn=mongodb_connection
    )

    response_formatter = providers.Factory(
        MarkdownResponseFormatter
    )

    # Use cases
    query_orchestrator = providers.Factory(
        QueryOrchestrator,
        analyzer=intent_analyzer,
        router=database_router,
        executor=query_executor,
        formatter=response_formatter
    )

# Usage
container = Container()
container.config.from_env()

orchestrator = container.query_orchestrator()
result = await orchestrator.process_query("¿Cuántas farmacias hay?")
```

## 4. Comandos Avanzados de Generación

### 4.1 Generación Completa de Módulos

```bash
# Generar módulo completo con todas las capas
claude generate module Analytics \
  --layers all \
  --entities "Metric,Dashboard,Report" \
  --use-cases "GenerateReport,ExportData,ScheduleReport" \
  --api-prefix "/api/v1/analytics" \
  --with-tests \
  --with-docs \
  --with-migrations

# Output structure:
# src/
#   domain/entities/metric.py, dashboard.py, report.py
#   application/use_cases/generate_report/, export_data/, schedule_report/
#   infrastructure/repositories/analytics_repository.py
#   api/routes/analytics_routes.py
# tests/
#   unit/domain/test_metric.py, test_dashboard.py, test_report.py
#   integration/test_analytics_flow.py
# docs/
#   analytics_module.md
# migrations/
#   001_create_analytics_tables.sql
```

### 4.2 Refactoring Automático

```bash
# Aplicar principios SOLID a código existente
claude refactor apply-solid \
  --path src/ \
  --principles SRP,OCP,DIP \
  --create-interfaces \
  --extract-abstractions \
  --inject-dependencies

# Migrar de arquitectura monolítica a 3 capas
claude refactor to-3-layer \
  --source web/server_unified.py \
  --target src/ \
  --create-entities \
  --create-use-cases \
  --create-repositories \
  --preserve-functionality

# Extraer interfaces de clases concretas
claude refactor extract-interfaces \
  --path src/infrastructure/ \
  --output src/domain/interfaces/ \
  --create-abc \
  --update-imports

# Optimizar imports y estructura
claude refactor optimize \
  --remove-unused-imports \
  --sort-imports \
  --format-code black \
  --type-check mypy
```

### 4.3 Generación de Documentación

```bash
# Generar documentación API (OpenAPI)
claude generate docs api \
  --format openapi \
  --version 3.0 \
  --include-schemas \
  --include-examples \
  --output docs/openapi.yaml

# Generar Architecture Decision Records
claude generate adr \
  --title "Migration to Event-Driven Architecture" \
  --status proposed \
  --context "Current synchronous processing causing bottlenecks" \
  --decision "Implement event bus with RabbitMQ" \
  --consequences "Increased complexity, better scalability"

# Generar diagramas de arquitectura
claude generate diagram \
  --type architecture \
  --format mermaid \
  --include-layers \
  --include-flow \
  --output docs/diagrams/

# Generar documentación de código
claude generate docs code \
  --path src/ \
  --format sphinx \
  --include-examples \
  --include-tests \
  --output docs/api/
```

## 5. CI/CD Pipeline

### 5.1 GitHub Actions Workflow

```yaml
# .github/workflows/ci-cd.yml
name: TrendsPro CI/CD Pipeline

on:
  push:
    branches: [main, develop]
  pull_request:
    branches: [main, develop]
  release:
    types: [created]

env:
  PYTHON_VERSION: '3.11'
  NODE_VERSION: '20'
  DOCKER_REGISTRY: ghcr.io
  IMAGE_NAME: ${{ github.repository }}

jobs:
  # Code Quality Checks
  quality:
    name: Code Quality
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3

      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: ${{ env.PYTHON_VERSION }}

      - name: Install dependencies
        run: |
          pip install poetry
          poetry install

      - name: Run Black
        run: poetry run black --check src/

      - name: Run Flake8
        run: poetry run flake8 src/

      - name: Run MyPy
        run: poetry run mypy src/

      - name: Run Bandit (Security)
        run: poetry run bandit -r src/

      - name: Check imports with isort
        run: poetry run isort --check-only src/

  # Python Tests
  test-backend:
    name: Backend Tests
    runs-on: ubuntu-latest
    needs: quality

    services:
      mysql:
        image: mysql:8.0
        env:
          MYSQL_ROOT_PASSWORD: test
          MYSQL_DATABASE: test_db
        ports:
          - 3306:3306
        options: >-
          --health-cmd="mysqladmin ping"
          --health-interval=10s
          --health-timeout=5s
          --health-retries=3

      mongodb:
        image: mongo:5.0
        ports:
          - 27017:27017
        options: >-
          --health-cmd="mongosh --eval 'db.adminCommand({ping: 1})'"
          --health-interval=10s
          --health-timeout=5s
          --health-retries=3

      redis:
        image: redis:7
        ports:
          - 6379:6379
        options: >-
          --health-cmd="redis-cli ping"
          --health-interval=10s
          --health-timeout=5s
          --health-retries=3

    steps:
      - uses: actions/checkout@v3

      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: ${{ env.PYTHON_VERSION }}

      - name: Install dependencies
        run: |
          pip install poetry
          poetry install

      - name: Run unit tests
        run: |
          poetry run pytest tests/unit/ \
            --cov=src \
            --cov-report=xml \
            --cov-report=html \
            -v

      - name: Run integration tests
        env:
          DATABASE_URL: mysql://root:test@localhost:3306/test_db
          MONGODB_URL: mongodb://localhost:27017/test_db
          REDIS_URL: redis://localhost:6379
        run: |
          poetry run pytest tests/integration/ -v

      - name: Upload coverage to Codecov
        uses: codecov/codecov-action@v3
        with:
          files: ./coverage.xml
          fail_ci_if_error: true

  # Frontend Tests
  test-frontend:
    name: Frontend Tests
    runs-on: ubuntu-latest
    needs: quality

    steps:
      - uses: actions/checkout@v3

      - name: Set up Node.js
        uses: actions/setup-node@v3
        with:
          node-version: ${{ env.NODE_VERSION }}
          cache: 'npm'
          cache-dependency-path: frontend/package-lock.json

      - name: Install dependencies
        working-directory: ./frontend
        run: npm ci

      - name: Run ESLint
        working-directory: ./frontend
        run: npm run lint

      - name: Run TypeScript check
        working-directory: ./frontend
        run: npm run type-check

      - name: Run unit tests
        working-directory: ./frontend
        run: npm run test:unit -- --coverage

      - name: Run component tests
        working-directory: ./frontend
        run: npm run test:components

  # E2E Tests
  test-e2e:
    name: E2E Tests
    runs-on: ubuntu-latest
    needs: [test-backend, test-frontend]

    steps:
      - uses: actions/checkout@v3

      - name: Set up Node.js
        uses: actions/setup-node@v3
        with:
          node-version: ${{ env.NODE_VERSION }}

      - name: Install Playwright
        run: npx playwright install --with-deps

      - name: Start services with Docker Compose
        run: |
          docker-compose -f docker/docker-compose.test.yml up -d
          sleep 10

      - name: Run E2E tests
        run: npx playwright test

      - name: Upload Playwright Report
        uses: actions/upload-artifact@v3
        if: always()
        with:
          name: playwright-report
          path: playwright-report/
          retention-days: 30

  # Build Docker Images
  build:
    name: Build Docker Images
    runs-on: ubuntu-latest
    needs: [test-e2e]
    if: github.event_name == 'push' || github.event_name == 'release'

    steps:
      - uses: actions/checkout@v3

      - name: Set up Docker Buildx
        uses: docker/setup-buildx-action@v2

      - name: Log in to GitHub Container Registry
        uses: docker/login-action@v2
        with:
          registry: ${{ env.DOCKER_REGISTRY }}
          username: ${{ github.actor }}
          password: ${{ secrets.GITHUB_TOKEN }}

      - name: Extract metadata
        id: meta
        uses: docker/metadata-action@v4
        with:
          images: ${{ env.DOCKER_REGISTRY }}/${{ env.IMAGE_NAME }}
          tags: |
            type=ref,event=branch
            type=ref,event=pr
            type=semver,pattern={{version}}
            type=semver,pattern={{major}}.{{minor}}
            type=sha

      - name: Build and push Backend
        uses: docker/build-push-action@v4
        with:
          context: .
          file: docker/Dockerfile.backend
          push: true
          tags: ${{ steps.meta.outputs.tags }}-backend
          labels: ${{ steps.meta.outputs.labels }}
          cache-from: type=gha
          cache-to: type=gha,mode=max

      - name: Build and push Frontend
        uses: docker/build-push-action@v4
        with:
          context: ./frontend
          file: docker/Dockerfile.frontend
          push: true
          tags: ${{ steps.meta.outputs.tags }}-frontend
          labels: ${{ steps.meta.outputs.labels }}
          cache-from: type=gha
          cache-to: type=gha,mode=max

  # Deploy to Staging
  deploy-staging:
    name: Deploy to Staging
    runs-on: ubuntu-latest
    needs: [build]
    if: github.ref == 'refs/heads/develop'
    environment:
      name: staging
      url: https://staging.trendspro.com

    steps:
      - uses: actions/checkout@v3

      - name: Deploy to Kubernetes (Staging)
        run: |
          # Install kubectl
          curl -LO "https://dl.k8s.io/release/$(curl -L -s https://dl.k8s.io/release/stable.txt)/bin/linux/amd64/kubectl"
          chmod +x kubectl

          # Configure kubectl
          echo "${{ secrets.KUBE_CONFIG_STAGING }}" | base64 -d > kubeconfig
          export KUBECONFIG=kubeconfig

          # Apply manifests
          kubectl apply -f kubernetes/staging/

          # Update image
          kubectl set image deployment/trendspro-backend \
            backend=${{ env.DOCKER_REGISTRY }}/${{ env.IMAGE_NAME }}:${{ github.sha }}-backend \
            -n staging

          kubectl set image deployment/trendspro-frontend \
            frontend=${{ env.DOCKER_REGISTRY }}/${{ env.IMAGE_NAME }}:${{ github.sha }}-frontend \
            -n staging

          # Wait for rollout
          kubectl rollout status deployment/trendspro-backend -n staging
          kubectl rollout status deployment/trendspro-frontend -n staging

  # Deploy to Production
  deploy-production:
    name: Deploy to Production
    runs-on: ubuntu-latest
    needs: [build]
    if: github.event_name == 'release'
    environment:
      name: production
      url: https://trendspro.com

    steps:
      - uses: actions/checkout@v3

      - name: Deploy to Kubernetes (Production)
        run: |
          # Similar to staging but with production namespace
          echo "${{ secrets.KUBE_CONFIG_PRODUCTION }}" | base64 -d > kubeconfig
          export KUBECONFIG=kubeconfig

          kubectl apply -f kubernetes/production/

          kubectl set image deployment/trendspro-backend \
            backend=${{ env.DOCKER_REGISTRY }}/${{ env.IMAGE_NAME }}:${{ github.ref_name }}-backend \
            -n production

          kubectl set image deployment/trendspro-frontend \
            frontend=${{ env.DOCKER_REGISTRY }}/${{ env.IMAGE_NAME }}:${{ github.ref_name }}-frontend \
            -n production

          kubectl rollout status deployment/trendspro-backend -n production
          kubectl rollout status deployment/trendspro-frontend -n production

      - name: Run smoke tests
        run: |
          npm install -g newman
          newman run tests/postman/smoke-tests.json \
            --environment tests/postman/production.json

  # Security Scanning
  security:
    name: Security Scanning
    runs-on: ubuntu-latest
    needs: [quality]

    steps:
      - uses: actions/checkout@v3

      - name: Run Trivy vulnerability scanner
        uses: aquasecurity/trivy-action@master
        with:
          scan-type: 'fs'
          scan-ref: '.'
          format: 'sarif'
          output: 'trivy-results.sarif'

      - name: Upload Trivy results to GitHub Security
        uses: github/codeql-action/upload-sarif@v2
        with:
          sarif_file: 'trivy-results.sarif'

      - name: Run Snyk Security Scan
        uses: snyk/actions/python@master
        env:
          SNYK_TOKEN: ${{ secrets.SNYK_TOKEN }}
        with:
          args: --severity-threshold=high

  # Performance Testing
  performance:
    name: Performance Testing
    runs-on: ubuntu-latest
    needs: [deploy-staging]
    if: github.ref == 'refs/heads/develop'

    steps:
      - uses: actions/checkout@v3

      - name: Run k6 performance tests
        run: |
          docker run --rm \
            -v $PWD/tests/k6:/scripts \
            grafana/k6 run /scripts/load-test.js \
            --env API_URL=https://staging.trendspro.com/api/v1

      - name: Upload performance results
        uses: actions/upload-artifact@v3
        with:
          name: k6-results
          path: tests/k6/results/
```

## 6. Monitoreo y Observabilidad

### 6.1 Configuración de Logging

```python
# src/infrastructure/monitoring/logging_config.py
import structlog
from pythonjsonlogger import jsonlogger
import logging
import sys
from typing import Any, Dict

def configure_logging(
    level: str = "INFO",
    json_output: bool = True,
    correlation_id_extractor: callable = None
):
    """Configure structured logging for the application"""

    # Configure structlog
    structlog.configure(
        processors=[
            structlog.stdlib.filter_by_level,
            structlog.stdlib.add_logger_name,
            structlog.stdlib.add_log_level,
            structlog.stdlib.PositionalArgumentsFormatter(),
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.StackInfoRenderer(),
            structlog.processors.format_exc_info,
            structlog.processors.UnicodeDecoder(),
            add_correlation_id,
            add_service_context,
            structlog.processors.dict_tracebacks,
            structlog.processors.JSONRenderer() if json_output else structlog.dev.ConsoleRenderer()
        ],
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        cache_logger_on_first_use=True,
    )

    # Configure Python logging
    if json_output:
        handler = logging.StreamHandler(sys.stdout)
        formatter = jsonlogger.JsonFormatter(
            '%(timestamp)s %(level)s %(name)s %(message)s',
            rename_fields={'timestamp': '@timestamp', 'level': 'level.name'}
        )
        handler.setFormatter(formatter)
    else:
        handler = logging.StreamHandler(sys.stdout)
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        handler.setFormatter(formatter)

    logging.root.handlers = [handler]
    logging.root.setLevel(getattr(logging, level))

    # Suppress noisy loggers
    logging.getLogger("urllib3").setLevel(logging.WARNING)
    logging.getLogger("asyncio").setLevel(logging.WARNING)

def add_correlation_id(logger, log_method, event_dict):
    """Add correlation ID to log entries"""
    import contextvars
    correlation_id = contextvars.ContextVar('correlation_id', default=None)

    if correlation_id.get():
        event_dict['correlation_id'] = correlation_id.get()

    return event_dict

def add_service_context(logger, log_method, event_dict):
    """Add service context to log entries"""
    event_dict['service'] = 'trendspro'
    event_dict['environment'] = os.getenv('ENVIRONMENT', 'development')
    event_dict['version'] = os.getenv('APP_VERSION', 'unknown')
    event_dict['host'] = socket.gethostname()

    return event_dict

# Usage
logger = structlog.get_logger()

logger.info(
    "query_executed",
    query_id="123",
    user_id="456",
    database="mysql",
    execution_time_ms=1234,
    cache_hit=False
)
```

### 6.2 Métricas con Prometheus

```python
# src/infrastructure/monitoring/prometheus_metrics.py
from prometheus_client import Counter, Histogram, Gauge, Info, CollectorRegistry
from prometheus_client import make_asgi_app
import time
from functools import wraps

# Create registry
registry = CollectorRegistry()

# Define metrics
query_counter = Counter(
    'trendspro_queries_total',
    'Total number of queries executed',
    ['database', 'intent', 'cache_hit'],
    registry=registry
)

query_duration = Histogram(
    'trendspro_query_duration_seconds',
    'Query execution duration in seconds',
    ['database', 'operation'],
    buckets=[0.1, 0.5, 1.0, 2.0, 5.0, 10.0],
    registry=registry
)

active_queries = Gauge(
    'trendspro_active_queries',
    'Number of currently active queries',
    ['database'],
    registry=registry
)

cache_hits = Counter(
    'trendspro_cache_hits_total',
    'Total number of cache hits',
    ['cache_level'],
    registry=registry
)

cache_misses = Counter(
    'trendspro_cache_misses_total',
    'Total number of cache misses',
    ['cache_level'],
    registry=registry
)

error_counter = Counter(
    'trendspro_errors_total',
    'Total number of errors',
    ['error_type', 'component'],
    registry=registry
)

app_info = Info(
    'trendspro_app',
    'Application information',
    registry=registry
)

# Set app info
app_info.info({
    'version': '2.1.0',
    'environment': os.getenv('ENVIRONMENT', 'development'),
    'python_version': sys.version
})

# Decorator for timing
def track_time(metric: Histogram, labels: Dict[str, str] = None):
    """Decorator to track execution time"""
    def decorator(func):
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            start_time = time.time()
            try:
                result = await func(*args, **kwargs)
                return result
            finally:
                duration = time.time() - start_time
                if labels:
                    metric.labels(**labels).observe(duration)
                else:
                    metric.observe(duration)

        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            start_time = time.time()
            try:
                result = func(*args, **kwargs)
                return result
            finally:
                duration = time.time() - start_time
                if labels:
                    metric.labels(**labels).observe(duration)
                else:
                    metric.observe(duration)

        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper
    return decorator

# Create ASGI app for metrics endpoint
metrics_app = make_asgi_app(registry=registry)

# Usage in FastAPI
from fastapi import FastAPI

app = FastAPI()
app.mount("/metrics", metrics_app)

# Example usage in use case
class ExecuteQueryUseCase:
    @track_time(query_duration, {'database': 'unified', 'operation': 'execute'})
    async def execute(self, dto: ExecuteQueryDTO):
        active_queries.labels(database='unified').inc()
        try:
            # Query execution logic
            result = await self._execute_query(dto)

            # Track metrics
            query_counter.labels(
                database=result.database_used,
                intent=result.intent,
                cache_hit=str(result.from_cache)
            ).inc()

            if result.from_cache:
                cache_hits.labels(cache_level='redis').inc()
            else:
                cache_misses.labels(cache_level='redis').inc()

            return result
        except Exception as e:
            error_counter.labels(
                error_type=type(e).__name__,
                component='query_execution'
            ).inc()
            raise
        finally:
            active_queries.labels(database='unified').dec()
```

## 7. Performance Optimizations

### 7.1 Backend Optimizations

```python
# Connection pooling
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.pool import NullPool, QueuePool

# Optimized connection pool
engine = create_async_engine(
    DATABASE_URL,
    poolclass=QueuePool,
    pool_size=20,
    max_overflow=40,
    pool_timeout=30,
    pool_recycle=3600,
    pool_pre_ping=True,
    echo=False
)

# Query optimization with indexes
from sqlalchemy import Index

class QueryModel(Base):
    __tablename__ = 'queries'

    id = Column(String(36), primary_key=True)
    user_id = Column(String(36), nullable=False)
    text = Column(Text, nullable=False)
    created_at = Column(DateTime, nullable=False)

    __table_args__ = (
        Index('idx_user_created', 'user_id', 'created_at'),
        Index('idx_created_at', 'created_at'),
        Index('idx_text_fulltext', 'text', mysql_prefix='FULLTEXT')
    )

# Batch processing
async def batch_process_queries(queries: List[str], batch_size: int = 100):
    """Process queries in batches for better performance"""
    results = []

    for i in range(0, len(queries), batch_size):
        batch = queries[i:i + batch_size]

        # Process batch in parallel
        tasks = [process_single_query(q) for q in batch]
        batch_results = await asyncio.gather(*tasks)
        results.extend(batch_results)

    return results

# Caching strategy
from functools import lru_cache
import hashlib

class SmartCache:
    """Multi-level caching with TTL and size limits"""

    def __init__(self):
        self.memory_cache = {}  # L1 cache
        self.redis_client = redis.Redis()  # L2 cache

    async def get(self, key: str) -> Optional[Any]:
        # Check L1 (memory)
        if key in self.memory_cache:
            return self.memory_cache[key]

        # Check L2 (Redis)
        value = await self.redis_client.get(key)
        if value:
            # Promote to L1
            self.memory_cache[key] = value
            return value

        return None

    async def set(self, key: str, value: Any, ttl: int = 3600):
        # Set in both levels
        self.memory_cache[key] = value
        await self.redis_client.setex(key, ttl, value)

    @staticmethod
    def generate_key(query: str, params: Dict) -> str:
        """Generate cache key from query and parameters"""
        content = f"{query}:{json.dumps(params, sort_keys=True)}"
        return hashlib.sha256(content.encode()).hexdigest()
```

### 7.2 Frontend Optimizations

```typescript
// Code splitting and lazy loading
import { lazy, Suspense } from 'react';

const Analytics = lazy(() => import('./features/Analytics'));
const Admin = lazy(() => import('./features/Admin'));

// Route-based code splitting
const routes = [
  {
    path: '/analytics',
    element: (
      <Suspense fallback={<Loading />}>
        <Analytics />
      </Suspense>
    )
  },
  {
    path: '/admin',
    element: (
      <Suspense fallback={<Loading />}>
        <Admin />
      </Suspense>
    )
  }
];

// Memoization for expensive computations
import { useMemo, memo } from 'react';

const ExpensiveComponent = memo(({ data }) => {
  const processedData = useMemo(() => {
    // Expensive computation
    return data.map(item => ({
      ...item,
      computed: heavyComputation(item)
    }));
  }, [data]);

  return <DataDisplay data={processedData} />;
});

// Virtual scrolling for large lists
import { FixedSizeList } from 'react-window';

const VirtualList = ({ items }) => (
  <FixedSizeList
    height={600}
    itemCount={items.length}
    itemSize={50}
    width="100%"
  >
    {({ index, style }) => (
      <div style={style}>
        {items[index].name}
      </div>
    )}
  </FixedSizeList>
);

// Service Worker for caching
// sw.js
self.addEventListener('install', (event) => {
  event.waitUntil(
    caches.open('v1').then((cache) => {
      return cache.addAll([
        '/',
        '/static/js/bundle.js',
        '/static/css/main.css'
      ]);
    })
  );
});

self.addEventListener('fetch', (event) => {
  event.respondWith(
    caches.match(event.request).then((response) => {
      return response || fetch(event.request);
    })
  );
});
```

## 8. Makefile

```makefile
# Makefile for TrendsPro
.PHONY: help install test build deploy clean

# Variables
PYTHON := python3.11
POETRY := poetry
NPM := npm
DOCKER := docker
KUBECTL := kubectl
BLACK := $(POETRY) run black
FLAKE8 := $(POETRY) run flake8
MYPY := $(POETRY) run mypy
PYTEST := $(POETRY) run pytest

# Colors
RED := \033[0;31m
GREEN := \033[0;32m
YELLOW := \033[0;33m
NC := \033[0m

help: ## Show this help message
	@echo "$(GREEN)TrendsPro - Enterprise Architecture Makefile$(NC)"
	@echo "$(YELLOW)Usage:$(NC) make [target]"
	@echo ""
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "$(GREEN)%-20s$(NC) %s\n", $$1, $$2}'

# Installation
install: ## Install all dependencies
	@echo "$(YELLOW)Installing Python dependencies...$(NC)"
	$(POETRY) install
	@echo "$(YELLOW)Installing Node.js dependencies...$(NC)"
	cd frontend && $(NPM) ci
	@echo "$(GREEN)Dependencies installed successfully!$(NC)"

install-dev: ## Install development dependencies
	$(POETRY) install --with dev
	cd frontend && $(NPM) ci
	pre-commit install

# Code Quality
format: ## Format code with Black
	$(BLACK) src/ tests/
	cd frontend && $(NPM) run format

lint: ## Run linting checks
	@echo "$(YELLOW)Running Python linters...$(NC)"
	$(BLACK) --check src/ tests/
	$(FLAKE8) src/ tests/
	$(MYPY) src/
	@echo "$(YELLOW)Running JavaScript linters...$(NC)"
	cd frontend && $(NPM) run lint

security: ## Run security checks
	$(POETRY) run bandit -r src/
	$(POETRY) run safety check
	cd frontend && $(NPM) audit

# Testing
test: ## Run all tests
	@echo "$(YELLOW)Running Python tests...$(NC)"
	$(PYTEST) tests/ -v --cov=src --cov-report=term-missing
	@echo "$(YELLOW)Running JavaScript tests...$(NC)"
	cd frontend && $(NPM) test

test-unit: ## Run unit tests only
	$(PYTEST) tests/unit/ -v

test-integration: ## Run integration tests
	$(PYTEST) tests/integration/ -v

test-e2e: ## Run E2E tests
	npx playwright test

test-coverage: ## Generate coverage report
	$(PYTEST) tests/ --cov=src --cov-report=html
	@echo "$(GREEN)Coverage report generated in htmlcov/$(NC)"

# Database
db-migrate: ## Run database migrations
	alembic upgrade head

db-rollback: ## Rollback last migration
	alembic downgrade -1

db-reset: ## Reset database
	alembic downgrade base
	alembic upgrade head

db-seed: ## Seed database with test data
	$(PYTHON) scripts/seed_database.py

# Build
build: ## Build Docker images
	@echo "$(YELLOW)Building backend image...$(NC)"
	$(DOCKER) build -f docker/Dockerfile.backend -t trendspro-backend:latest .
	@echo "$(YELLOW)Building frontend image...$(NC)"
	$(DOCKER) build -f docker/Dockerfile.frontend -t trendspro-frontend:latest frontend/
	@echo "$(GREEN)Images built successfully!$(NC)"

build-prod: ## Build production Docker images
	$(DOCKER) build -f docker/Dockerfile.backend --target production -t trendspro-backend:prod .
	$(DOCKER) build -f docker/Dockerfile.frontend --target production -t trendspro-frontend:prod frontend/

# Development
dev: ## Start development environment
	docker-compose -f docker/docker-compose.dev.yml up

dev-backend: ## Start backend in development mode
	$(POETRY) run uvicorn src.main:app --reload --port 8000

dev-frontend: ## Start frontend in development mode
	cd frontend && $(NPM) run dev

dev-stop: ## Stop development environment
	docker-compose -f docker/docker-compose.dev.yml down

# Deployment
deploy-staging: ## Deploy to staging
	$(KUBECTL) apply -f kubernetes/staging/
	$(KUBECTL) rollout status deployment/trendspro -n staging

deploy-production: ## Deploy to production
	@echo "$(RED)Warning: Deploying to production!$(NC)"
	@read -p "Are you sure? [y/N] " -n 1 -r; \
	if [[ $$REPLY =~ ^[Yy]$$ ]]; then \
		$(KUBECTL) apply -f kubernetes/production/; \
		$(KUBECTL) rollout status deployment/trendspro -n production; \
	fi

rollback: ## Rollback deployment
	$(KUBECTL) rollout undo deployment/trendspro

# Monitoring
logs: ## Show application logs
	$(KUBECTL) logs -f deployment/trendspro

metrics: ## Show Prometheus metrics
	@echo "$(YELLOW)Opening Prometheus dashboard...$(NC)"
	open http://localhost:9090

grafana: ## Open Grafana dashboard
	@echo "$(YELLOW)Opening Grafana dashboard...$(NC)"
	open http://localhost:3000

# Generation Commands
generate-entity: ## Generate a new entity
	$(PYTHON) scripts/generate/generate_entity.py $(name)

generate-usecase: ## Generate a new use case
	$(PYTHON) scripts/generate/generate_use_case.py $(name)

generate-component: ## Generate a React component
	cd frontend && $(NPM) run generate:component $(name)

# Documentation
docs: ## Generate documentation
	$(POETRY) run sphinx-build -b html docs/ docs/_build/

docs-serve: ## Serve documentation locally
	$(PYTHON) -m http.server --directory docs/_build 8080

# Cleanup
clean: ## Clean build artifacts
	@echo "$(YELLOW)Cleaning build artifacts...$(NC)"
	rm -rf dist/ build/ *.egg-info
	rm -rf frontend/build frontend/dist
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete
	@echo "$(GREEN)Cleanup complete!$(NC)"

clean-docker: ## Clean Docker resources
	$(DOCKER) system prune -f
	$(DOCKER) volume prune -f

# Utilities
shell: ## Open Python shell with app context
	$(POETRY) run python -i scripts/shell.py

check: format lint test ## Run all checks

version: ## Show version
	@echo "TrendsPro v2.1.0"

.DEFAULT_GOAL := help
```

## 9. Conclusión

Este archivo **Claude.md** proporciona una guía completa para la integración y modernización del proyecto TrendsPro con:

### ✅ Arquitectura Implementada
- **3 Capas Estrictas**: Presentation, Domain, Infrastructure
- **Patrones DDD**: Entities, Value Objects, Repositories
- **SOLID Principles**: Aplicados consistentemente
- **Clean Architecture**: Dependencias invertidas

### ✅ Stack Tecnológico
- **Backend**: FastAPI + SQLAlchemy + Pydantic
- **Frontend**: React + TypeScript + Redux Toolkit
- **Databases**: MySQL + MongoDB con routing inteligente
- **Testing**: Pytest + Vitest + Playwright
- **CI/CD**: GitHub Actions + Docker + Kubernetes

### ✅ Características Avanzadas
- Multi-agent system architecture
- Real-time streaming con SSE/WebSocket
- Multi-level caching strategy
- Comprehensive monitoring y observability
- Security-first approach

### ✅ Herramientas de Productividad
- Comandos de generación automatizados
- Refactoring tools
- Documentation generation
- Performance optimization helpers

### 📈 Métricas de Calidad
- **Test Coverage**: Target 80%+
- **Code Quality**: Black + Flake8 + MyPy + ESLint
- **Performance**: <2s P95 latency
- **Availability**: 99.9% SLO

### 🚀 Próximos Pasos
1. Ejecutar migración a 3 capas: `make refactor-to-3-layer`
2. Implementar agentes: `make generate-agents`
3. Setup CI/CD: `make setup-ci`
4. Deploy staging: `make deploy-staging`

---

*Documento generado por: CTO Senior Architecture Expert*
*Versión: 1.0.0*
*Fecha: 2025-01-13*
*Proyecto: TrendsPro Enterprise Architecture*