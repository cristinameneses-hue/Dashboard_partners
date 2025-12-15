"""
Common Schemas

Shared Pydantic models for API validation.
"""

from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, List, Dict, Any, Generic, TypeVar
from datetime import datetime
from enum import Enum


T = TypeVar('T')


class ErrorCode(str, Enum):
    """Error code enumeration."""
    VALIDATION_ERROR = "validation_error"
    AUTHENTICATION_ERROR = "authentication_error"
    AUTHORIZATION_ERROR = "authorization_error"
    NOT_FOUND = "not_found"
    CONFLICT = "conflict"
    INTERNAL_ERROR = "internal_error"
    TIMEOUT = "timeout"
    RATE_LIMIT = "rate_limit"
    DATABASE_ERROR = "database_error"
    EXTERNAL_SERVICE_ERROR = "external_service_error"


class ErrorResponse(BaseModel):
    """Standard error response model."""

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "error": "validation_error",
                "message": "Query text is required",
                "details": {"field": "query", "reason": "missing"},
                "request_id": "req_550e8400",
                "timestamp": "2024-01-17T10:30:00Z"
            }
        }
    )

    error: ErrorCode = Field(
        ...,
        description="Error code"
    )

    message: str = Field(
        ...,
        description="Human-readable error message"
    )

    details: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Additional error details"
    )

    request_id: Optional[str] = Field(
        default=None,
        description="Request identifier for tracking"
    )

    timestamp: datetime = Field(
        default_factory=datetime.utcnow,
        description="Error timestamp"
    )


class HealthStatus(str, Enum):
    """Health status enumeration."""
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"


class HealthCheckResponse(BaseModel):
    """Health check response model."""

    status: HealthStatus = Field(
        ...,
        description="Overall health status"
    )

    version: str = Field(
        ...,
        description="Application version"
    )

    timestamp: datetime = Field(
        default_factory=datetime.utcnow,
        description="Health check timestamp"
    )

    checks: Dict[str, Dict[str, Any]] = Field(
        default_factory=dict,
        description="Individual component health checks"
    )

    uptime_seconds: Optional[int] = Field(
        default=None,
        description="Application uptime in seconds"
    )


class PaginatedResponse(BaseModel, Generic[T]):
    """Generic paginated response model."""

    items: List[T] = Field(
        ...,
        description="List of items"
    )

    total: int = Field(
        ...,
        description="Total number of items"
    )

    page: int = Field(
        default=1,
        ge=1,
        description="Current page number"
    )

    page_size: int = Field(
        default=20,
        ge=1,
        le=100,
        description="Items per page"
    )

    pages: int = Field(
        ...,
        description="Total number of pages"
    )

    has_next: bool = Field(
        ...,
        description="Whether there's a next page"
    )

    has_previous: bool = Field(
        ...,
        description="Whether there's a previous page"
    )


class SuccessResponse(BaseModel):
    """Generic success response model."""

    success: bool = Field(
        default=True,
        description="Operation success indicator"
    )

    message: str = Field(
        ...,
        description="Success message"
    )

    data: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Optional response data"
    )

    timestamp: datetime = Field(
        default_factory=datetime.utcnow,
        description="Response timestamp"
    )


class BatchOperationResult(BaseModel):
    """Result of a batch operation."""

    total: int = Field(
        ...,
        description="Total items processed"
    )

    successful: int = Field(
        ...,
        description="Number of successful operations"
    )

    failed: int = Field(
        ...,
        description="Number of failed operations"
    )

    errors: Optional[List[Dict[str, Any]]] = Field(
        default=None,
        description="List of errors if any"
    )

    duration_ms: int = Field(
        ...,
        description="Total operation duration in milliseconds"
    )


class StreamChunk(BaseModel):
    """Model for streaming response chunk."""

    type: str = Field(
        ...,
        description="Chunk type (token, metadata, error, complete)"
    )

    content: Optional[str] = Field(
        default=None,
        description="Chunk content"
    )

    metadata: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Chunk metadata"
    )

    sequence: int = Field(
        ...,
        description="Chunk sequence number"
    )

    timestamp: datetime = Field(
        default_factory=datetime.utcnow,
        description="Chunk timestamp"
    )


class RequestMetadata(BaseModel):
    """Request metadata model."""

    request_id: str = Field(
        ...,
        description="Unique request identifier"
    )

    client_ip: Optional[str] = Field(
        default=None,
        description="Client IP address"
    )

    user_agent: Optional[str] = Field(
        default=None,
        description="User agent string"
    )

    referer: Optional[str] = Field(
        default=None,
        description="Referer URL"
    )

    timestamp: datetime = Field(
        default_factory=datetime.utcnow,
        description="Request timestamp"
    )


class RateLimitInfo(BaseModel):
    """Rate limit information model."""

    limit: int = Field(
        ...,
        description="Request limit"
    )

    remaining: int = Field(
        ...,
        description="Remaining requests"
    )

    reset_at: datetime = Field(
        ...,
        description="When the limit resets"
    )

    retry_after: Optional[int] = Field(
        default=None,
        description="Seconds to wait before retry"
    )