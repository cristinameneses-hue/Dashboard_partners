"""
Conversation Schemas

Pydantic models for conversation-related request and response validation.
"""

from pydantic import BaseModel, Field, ConfigDict, field_validator
from typing import Optional, List, Dict, Any, Literal
from datetime import datetime
from enum import Enum


class MessageRole(str, Enum):
    """Message role enumeration."""
    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"


class ConversationMessageRequest(BaseModel):
    """Request model for adding a message to conversation."""

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "content": "¿Cuántas farmacias tenemos activas?",
                "metadata": {"source": "web"}
            }
        }
    )

    content: str = Field(
        ...,
        min_length=1,
        max_length=5000,
        description="Message content"
    )

    metadata: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Optional message metadata"
    )

    @field_validator('content')
    @classmethod
    def validate_content(cls, v: str) -> str:
        """Validate message content."""
        v = v.strip()
        if not v:
            raise ValueError("Message content cannot be empty")
        return v


class ConversationMessage(BaseModel):
    """Model for a conversation message."""

    role: MessageRole = Field(
        ...,
        description="Role of the message sender"
    )

    content: str = Field(
        ...,
        description="Message content"
    )

    timestamp: datetime = Field(
        ...,
        description="Message timestamp"
    )

    metadata: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Message metadata"
    )

    token_count: Optional[int] = Field(
        default=None,
        description="Token count for the message"
    )

    cost_usd: Optional[float] = Field(
        default=None,
        description="Cost in USD for generating this message"
    )


class CreateConversationRequest(BaseModel):
    """Request model for creating a new conversation."""

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "title": "Product Analysis Session",
                "initial_message": "I need help analyzing sales data",
                "metadata": {"purpose": "analysis"}
            }
        }
    )

    title: Optional[str] = Field(
        default=None,
        max_length=200,
        description="Conversation title"
    )

    initial_message: Optional[str] = Field(
        default=None,
        max_length=5000,
        description="Optional initial message"
    )

    metadata: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Conversation metadata"
    )

    system_prompt: Optional[str] = Field(
        default=None,
        description="Custom system prompt for this conversation"
    )


class ConversationResponse(BaseModel):
    """Response model for conversation details."""

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "id": "conv_550e8400-e29b-41d4-a716-446655440000",
                "title": "Product Analysis Session",
                "messages": [
                    {
                        "role": "user",
                        "content": "I need help analyzing sales data",
                        "timestamp": "2024-01-17T10:30:00Z"
                    },
                    {
                        "role": "assistant",
                        "content": "I'll help you analyze the sales data...",
                        "timestamp": "2024-01-17T10:30:05Z"
                    }
                ],
                "created_at": "2024-01-17T10:30:00Z",
                "updated_at": "2024-01-17T10:30:05Z",
                "message_count": 2,
                "is_active": True,
                "token_count": 150,
                "total_cost_usd": 0.003
            }
        }
    )

    id: str = Field(
        ...,
        description="Conversation unique identifier"
    )

    title: Optional[str] = Field(
        default=None,
        description="Conversation title"
    )

    messages: List[ConversationMessage] = Field(
        default_factory=list,
        description="List of conversation messages"
    )

    created_at: datetime = Field(
        ...,
        description="Conversation creation timestamp"
    )

    updated_at: datetime = Field(
        ...,
        description="Last update timestamp"
    )

    message_count: int = Field(
        default=0,
        description="Total number of messages"
    )

    is_active: bool = Field(
        default=True,
        description="Whether conversation is active"
    )

    token_count: int = Field(
        default=0,
        description="Total tokens used"
    )

    total_cost_usd: float = Field(
        default=0.0,
        description="Total cost in USD"
    )

    metadata: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Conversation metadata"
    )

    summary: Optional[str] = Field(
        default=None,
        description="Conversation summary if available"
    )

    user_id: Optional[str] = Field(
        default=None,
        description="Owner user ID"
    )


class ConversationListResponse(BaseModel):
    """Response model for listing conversations."""

    conversations: List[ConversationResponse] = Field(
        ...,
        description="List of conversations"
    )

    total_count: int = Field(
        ...,
        description="Total number of conversations"
    )

    page: int = Field(
        default=1,
        description="Current page number"
    )

    page_size: int = Field(
        default=20,
        description="Items per page"
    )

    has_next: bool = Field(
        default=False,
        description="Whether there's a next page"
    )

    has_previous: bool = Field(
        default=False,
        description="Whether there's a previous page"
    )


class UpdateConversationRequest(BaseModel):
    """Request model for updating a conversation."""

    title: Optional[str] = Field(
        default=None,
        max_length=200,
        description="New title for the conversation"
    )

    is_active: Optional[bool] = Field(
        default=None,
        description="Update active status"
    )

    metadata: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Update metadata"
    )


class ConversationContextRequest(BaseModel):
    """Request model for getting conversation context."""

    max_messages: int = Field(
        default=50,
        ge=1,
        le=200,
        description="Maximum number of messages to include"
    )

    include_system: bool = Field(
        default=True,
        description="Include system messages"
    )

    include_summary: bool = Field(
        default=True,
        description="Include conversation summary if available"
    )


class ConversationContextResponse(BaseModel):
    """Response model for conversation context."""

    context: List[Dict[str, str]] = Field(
        ...,
        description="Formatted context for LLM"
    )

    message_count: int = Field(
        ...,
        description="Number of messages in context"
    )

    has_summary: bool = Field(
        default=False,
        description="Whether context includes summary"
    )

    token_estimate: Optional[int] = Field(
        default=None,
        description="Estimated token count"
    )


class GenerateTitleRequest(BaseModel):
    """Request model for generating conversation title."""

    use_full_context: bool = Field(
        default=False,
        description="Use full conversation context"
    )

    max_length: int = Field(
        default=50,
        ge=10,
        le=200,
        description="Maximum title length"
    )


class GenerateTitleResponse(BaseModel):
    """Response model for generated title."""

    title: str = Field(
        ...,
        description="Generated title"
    )

    confidence: float = Field(
        ...,
        ge=0,
        le=1,
        description="Confidence in generated title"
    )


class ExportConversationRequest(BaseModel):
    """Request model for exporting conversation."""

    format: Literal["json", "markdown", "text", "csv"] = Field(
        default="json",
        description="Export format"
    )

    include_metadata: bool = Field(
        default=True,
        description="Include metadata in export"
    )

    include_system_messages: bool = Field(
        default=False,
        description="Include system messages"
    )


class ConversationStatistics(BaseModel):
    """Model for conversation statistics."""

    total_conversations: int = Field(
        ...,
        description="Total number of conversations"
    )

    active_conversations: int = Field(
        ...,
        description="Number of active conversations"
    )

    total_messages: int = Field(
        ...,
        description="Total number of messages"
    )

    average_messages_per_conversation: float = Field(
        ...,
        description="Average messages per conversation"
    )

    total_tokens: int = Field(
        ...,
        description="Total tokens used"
    )

    total_cost_usd: float = Field(
        ...,
        description="Total cost in USD"
    )

    average_conversation_duration_seconds: float = Field(
        ...,
        description="Average conversation duration"
    )

    period: Dict[str, datetime] = Field(
        ...,
        description="Time period for statistics"
    )