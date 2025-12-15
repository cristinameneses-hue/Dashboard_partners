"""
API Schemas Package

Pydantic models for request and response validation.
"""

from .query_schemas import (
    QueryRequest,
    QueryResponse,
    QueryStreamRequest,
    QueryAnalysisResponse,
    QueryHistoryItem,
    QueryHistoryResponse,
    QueryMetrics,
    DatabaseType
)

from .conversation_schemas import (
    ConversationMessageRequest,
    ConversationMessage,
    CreateConversationRequest,
    ConversationResponse,
    ConversationListResponse,
    UpdateConversationRequest,
    ConversationContextRequest,
    ConversationContextResponse,
    GenerateTitleRequest,
    GenerateTitleResponse,
    ExportConversationRequest,
    ConversationStatistics,
    MessageRole
)

from .common_schemas import (
    ErrorResponse,
    ErrorCode,
    HealthCheckResponse,
    HealthStatus,
    PaginatedResponse,
    SuccessResponse,
    BatchOperationResult,
    StreamChunk,
    RequestMetadata,
    RateLimitInfo
)

__all__ = [
    # Query schemas
    'QueryRequest',
    'QueryResponse',
    'QueryStreamRequest',
    'QueryAnalysisResponse',
    'QueryHistoryItem',
    'QueryHistoryResponse',
    'QueryMetrics',
    'DatabaseType',

    # Conversation schemas
    'ConversationMessageRequest',
    'ConversationMessage',
    'CreateConversationRequest',
    'ConversationResponse',
    'ConversationListResponse',
    'UpdateConversationRequest',
    'ConversationContextRequest',
    'ConversationContextResponse',
    'GenerateTitleRequest',
    'GenerateTitleResponse',
    'ExportConversationRequest',
    'ConversationStatistics',
    'MessageRole',

    # Common schemas
    'ErrorResponse',
    'ErrorCode',
    'HealthCheckResponse',
    'HealthStatus',
    'PaginatedResponse',
    'SuccessResponse',
    'BatchOperationResult',
    'StreamChunk',
    'RequestMetadata',
    'RateLimitInfo'
]