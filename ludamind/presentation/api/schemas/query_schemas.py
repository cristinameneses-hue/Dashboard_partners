"""
Query Schemas

Pydantic models for query-related request and response validation.
"""

from pydantic import BaseModel, Field, ConfigDict, field_validator
from typing import Optional, List, Dict, Any, Literal
from datetime import datetime
from enum import Enum


class DatabaseType(str, Enum):
    """Database type enumeration."""
    MYSQL = "mysql"
    MONGODB = "mongodb"
    AUTO = "auto"


class QueryRequest(BaseModel):
    """Request model for executing a query."""

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "query": "¿Cuáles son los 10 productos más vendidos?",
                "use_cache": True,
                "timeout_seconds": 30,
                "use_chatgpt": False
            }
        }
    )

    query: str = Field(
        ...,
        min_length=1,
        max_length=1000,
        description="Natural language query to execute"
    )

    use_cache: bool = Field(
        default=True,
        description="Whether to use cached results if available"
    )

    timeout_seconds: int = Field(
        default=30,
        ge=1,
        le=300,
        description="Query execution timeout in seconds"
    )

    use_chatgpt: bool = Field(
        default=False,
        description="Use ChatGPT instead of OpenAI for processing"
    )

    force_database: Optional[DatabaseType] = Field(
        default=None,
        description="Force query to specific database"
    )

    session_id: Optional[str] = Field(
        default=None,
        description="Session identifier for context"
    )

    include_explanation: bool = Field(
        default=False,
        description="Include explanation of query routing"
    )

    @field_validator('query')
    @classmethod
    def validate_query(cls, v: str) -> str:
        """Validate and clean query text."""
        v = v.strip()
        if not v:
            raise ValueError("Query cannot be empty")
        if len(v) < 3:
            raise ValueError("Query too short (minimum 3 characters)")
        return v


class QueryStreamRequest(QueryRequest):
    """Request model for streaming query execution."""

    stream_format: Literal["sse", "websocket"] = Field(
        default="sse",
        description="Streaming format to use"
    )

    chunk_size: int = Field(
        default=100,
        ge=10,
        le=1000,
        description="Size of streaming chunks"
    )


class QueryResponse(BaseModel):
    """Response model for query execution."""

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "query_id": "550e8400-e29b-41d4-a716-446655440000",
                "query": "¿Cuáles son los 10 productos más vendidos?",
                "results": [
                    {"product": "Paracetamol", "sales": 1500},
                    {"product": "Ibuprofeno", "sales": 1200}
                ],
                "formatted_response": "Los 10 productos más vendidos son...",
                "database_used": "mysql",
                "execution_time_ms": 245,
                "from_cache": False,
                "metadata": {
                    "routing_confidence": 0.95,
                    "matched_keywords": ["productos", "vendidos"],
                    "result_count": 10
                }
            }
        }
    )

    query_id: str = Field(
        ...,
        description="Unique identifier for the query"
    )

    query: str = Field(
        ...,
        description="Original query text"
    )

    results: Optional[List[Dict[str, Any]]] = Field(
        default=None,
        description="Raw query results"
    )

    formatted_response: Optional[str] = Field(
        default=None,
        description="Formatted response for display"
    )

    database_used: Optional[str] = Field(
        default=None,
        description="Database that handled the query"
    )

    execution_time_ms: int = Field(
        ...,
        description="Query execution time in milliseconds"
    )

    from_cache: bool = Field(
        default=False,
        description="Whether results came from cache"
    )

    metadata: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Additional metadata about the query"
    )

    error: Optional[str] = Field(
        default=None,
        description="Error message if query failed"
    )

    timestamp: datetime = Field(
        default_factory=datetime.utcnow,
        description="Response timestamp"
    )


class QueryAnalysisResponse(BaseModel):
    """Response model for query analysis."""

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "query": "GMV de Glovo esta semana",
                "routing": {
                    "database": "mongodb",
                    "confidence": 0.92,
                    "reasoning": "Partner GMV queries use MongoDB bookings collection",
                    "matched_keywords": ["gmv", "glovo"],
                    "needs_confirmation": False
                },
                "complexity": {
                    "estimated_difficulty": "medium",
                    "requires_aggregation": True,
                    "has_temporal_component": True,
                    "is_complex": False
                },
                "explanation": "Query will be routed to MongoDB...",
                "estimated_execution_time_ms": 500
            }
        }
    )

    query: str = Field(
        ...,
        description="Analyzed query text"
    )

    routing: Dict[str, Any] = Field(
        ...,
        description="Routing decision details"
    )

    complexity: Dict[str, Any] = Field(
        ...,
        description="Query complexity analysis"
    )

    explanation: str = Field(
        ...,
        description="Human-readable explanation"
    )

    estimated_execution_time_ms: int = Field(
        ...,
        description="Estimated execution time"
    )

    suggestions: Optional[List[str]] = Field(
        default=None,
        description="Suggested query improvements"
    )


class QueryHistoryItem(BaseModel):
    """Model for query history item."""

    query_id: str
    query: str
    database_used: Optional[str]
    execution_time_ms: int
    from_cache: bool
    created_at: datetime
    result_count: Optional[int] = None
    error: Optional[str] = None


class QueryHistoryResponse(BaseModel):
    """Response model for query history."""

    items: List[QueryHistoryItem]
    total_count: int
    page: int = 1
    page_size: int = 20
    has_next: bool = False
    has_previous: bool = False


class QueryMetrics(BaseModel):
    """Model for query metrics."""

    total_queries: int = Field(
        ...,
        description="Total number of queries executed"
    )

    successful_queries: int = Field(
        ...,
        description="Number of successful queries"
    )

    failed_queries: int = Field(
        ...,
        description="Number of failed queries"
    )

    average_execution_time_ms: float = Field(
        ...,
        description="Average execution time"
    )

    cache_hit_rate: float = Field(
        ...,
        ge=0,
        le=1,
        description="Cache hit rate (0-1)"
    )

    database_distribution: Dict[str, int] = Field(
        default_factory=dict,
        description="Query distribution by database"
    )

    period: Dict[str, datetime] = Field(
        ...,
        description="Time period for metrics"
    )