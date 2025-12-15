"""
Conversation Entity

Represents a conversation session between a user and the system.
This entity manages the entire conversation lifecycle and maintains context.
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, List, Optional, Any
from uuid import uuid4

from .query import Query
from .user import User


@dataclass
class ConversationMessage:
    """
    Represents a single message in a conversation.

    This is a nested value object within the Conversation entity.
    """

    role: str  # "user", "assistant", "system"
    content: str
    timestamp: datetime = field(default_factory=datetime.now)
    metadata: Optional[Dict[str, Any]] = None
    token_count: Optional[int] = None
    cost_usd: Optional[float] = None


@dataclass
class Conversation:
    """
    Entity representing a conversation session.

    This entity tracks the complete interaction history between
    a user and the system, including all queries and responses.

    Identity is maintained through the `id` field.
    """

    # Identity
    id: str = field(default_factory=lambda: str(uuid4()))

    # Core properties
    user_id: Optional[str] = None  # Reference to User entity
    session_id: Optional[str] = None  # External session identifier
    title: Optional[str] = None  # Conversation title (auto-generated or user-defined)

    # Conversation state
    messages: List[ConversationMessage] = field(default_factory=list)
    queries: List[str] = field(default_factory=list)  # Query IDs for reference
    context: Dict[str, Any] = field(default_factory=dict)  # Conversation context

    # Configuration
    model: str = "gpt-4o-mini"  # LLM model used
    temperature: float = 0.1  # Temperature setting
    max_tokens: int = 2000  # Maximum tokens per response
    system_prompt: Optional[str] = None  # Custom system prompt

    # Status
    status: str = "active"  # active, paused, completed, archived
    is_public: bool = False  # Whether conversation is shareable

    # Metadata
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    last_activity_at: datetime = field(default_factory=datetime.now)
    completed_at: Optional[datetime] = None

    # Statistics
    total_messages: int = 0
    total_queries: int = 0
    total_tokens_used: int = 0
    total_cost_usd: float = 0.0
    average_response_time_ms: float = 0.0

    # Tags and categorization
    tags: List[str] = field(default_factory=list)
    category: Optional[str] = None

    def __post_init__(self):
        """Initialize and validate the conversation entity."""
        self.validate()
        self.update_statistics()

    def validate(self):
        """
        Validate the conversation entity.

        Raises:
            ValueError: If validation fails
        """
        valid_statuses = ["active", "paused", "completed", "archived"]
        if self.status not in valid_statuses:
            raise ValueError(f"Invalid status: {self.status}")

        if self.temperature < 0 or self.temperature > 2:
            raise ValueError(f"Temperature must be between 0 and 2, got {self.temperature}")

        if self.max_tokens <= 0:
            raise ValueError("Max tokens must be positive")

        valid_roles = ["user", "assistant", "system"]
        for msg in self.messages:
            if msg.role not in valid_roles:
                raise ValueError(f"Invalid message role: {msg.role}")

    # Business methods

    def add_message(self, role: str, content: str,
                   metadata: Optional[Dict[str, Any]] = None,
                   token_count: Optional[int] = None,
                   cost_usd: Optional[float] = None):
        """
        Add a message to the conversation.

        Args:
            role: Message role (user, assistant, system)
            content: Message content
            metadata: Optional metadata
            token_count: Optional token count
            cost_usd: Optional cost in USD
        """
        message = ConversationMessage(
            role=role,
            content=content,
            metadata=metadata,
            token_count=token_count,
            cost_usd=cost_usd
        )

        self.messages.append(message)
        self.total_messages += 1

        if token_count:
            self.total_tokens_used += token_count

        if cost_usd:
            self.total_cost_usd += cost_usd

        self.last_activity_at = datetime.now()
        self.updated_at = datetime.now()

    def add_query(self, query_id: str):
        """
        Add a query reference to the conversation.

        Args:
            query_id: The ID of the Query entity
        """
        self.queries.append(query_id)
        self.total_queries += 1
        self.updated_at = datetime.now()

    def update_context(self, key: str, value: Any):
        """
        Update the conversation context.

        Args:
            key: Context key
            value: Context value
        """
        self.context[key] = value
        self.updated_at = datetime.now()

    def pause(self):
        """Pause the conversation."""
        self.status = "paused"
        self.updated_at = datetime.now()

    def resume(self):
        """Resume a paused conversation."""
        if self.status == "paused":
            self.status = "active"
            self.last_activity_at = datetime.now()
            self.updated_at = datetime.now()

    def complete(self):
        """Mark the conversation as completed."""
        self.status = "completed"
        self.completed_at = datetime.now()
        self.updated_at = datetime.now()

    def archive(self):
        """Archive the conversation."""
        self.status = "archived"
        self.updated_at = datetime.now()

    def set_title(self, title: str):
        """
        Set or update the conversation title.

        Args:
            title: The new title
        """
        self.title = title
        self.updated_at = datetime.now()

    def add_tag(self, tag: str):
        """
        Add a tag to the conversation.

        Args:
            tag: Tag to add
        """
        if tag not in self.tags:
            self.tags.append(tag)
            self.updated_at = datetime.now()

    def remove_tag(self, tag: str):
        """
        Remove a tag from the conversation.

        Args:
            tag: Tag to remove
        """
        if tag in self.tags:
            self.tags.remove(tag)
            self.updated_at = datetime.now()

    def make_public(self):
        """Make the conversation publicly shareable."""
        self.is_public = True
        self.updated_at = datetime.now()

    def make_private(self):
        """Make the conversation private."""
        self.is_public = False
        self.updated_at = datetime.now()

    def update_statistics(self):
        """Update conversation statistics."""
        self.total_messages = len(self.messages)
        self.total_queries = len(self.queries)

        # Update token count and cost
        self.total_tokens_used = sum(
            msg.token_count for msg in self.messages
            if msg.token_count is not None
        )

        self.total_cost_usd = sum(
            msg.cost_usd for msg in self.messages
            if msg.cost_usd is not None
        )

    def get_messages_for_llm(self, max_messages: Optional[int] = None) -> List[Dict[str, str]]:
        """
        Get messages formatted for LLM API.

        Args:
            max_messages: Optional limit on number of messages

        Returns:
            List of message dictionaries
        """
        messages = []

        # Add system prompt if configured
        if self.system_prompt:
            messages.append({
                "role": "system",
                "content": self.system_prompt
            })

        # Add conversation messages
        conversation_messages = self.messages[-max_messages:] if max_messages else self.messages

        for msg in conversation_messages:
            messages.append({
                "role": msg.role,
                "content": msg.content
            })

        return messages

    def get_summary(self) -> str:
        """
        Get a summary of the conversation.

        Returns:
            Conversation summary
        """
        if not self.messages:
            return "Empty conversation"

        # Get first user message as summary if no title
        if not self.title:
            for msg in self.messages:
                if msg.role == "user":
                    return msg.content[:100] + ("..." if len(msg.content) > 100 else "")

        return self.title or f"Conversation {self.id[:8]}"

    # Query methods

    @property
    def is_active(self) -> bool:
        """Check if the conversation is active."""
        return self.status == "active"

    @property
    def is_completed(self) -> bool:
        """Check if the conversation is completed."""
        return self.status == "completed"

    @property
    def is_archived(self) -> bool:
        """Check if the conversation is archived."""
        return self.status == "archived"

    @property
    def duration_minutes(self) -> float:
        """
        Get the conversation duration in minutes.

        Returns:
            Duration in minutes
        """
        if self.completed_at:
            duration = self.completed_at - self.created_at
        else:
            duration = self.last_activity_at - self.created_at

        return duration.total_seconds() / 60

    @property
    def message_count_by_role(self) -> Dict[str, int]:
        """
        Get message count by role.

        Returns:
            Dictionary with counts per role
        """
        counts = {"user": 0, "assistant": 0, "system": 0}
        for msg in self.messages:
            counts[msg.role] = counts.get(msg.role, 0) + 1
        return counts

    @property
    def average_message_length(self) -> float:
        """
        Get average message length.

        Returns:
            Average length in characters
        """
        if not self.messages:
            return 0.0

        total_length = sum(len(msg.content) for msg in self.messages)
        return total_length / len(self.messages)

    @property
    def cost_per_message(self) -> float:
        """
        Get average cost per message.

        Returns:
            Average cost in USD
        """
        if self.total_messages == 0:
            return 0.0

        return self.total_cost_usd / self.total_messages

    def to_dict(self) -> Dict[str, Any]:
        """
        Convert to dictionary for serialization.

        Returns:
            Dictionary representation
        """
        return {
            'id': self.id,
            'user_id': self.user_id,
            'session_id': self.session_id,
            'title': self.title or self.get_summary(),
            'status': self.status,
            'is_public': self.is_public,
            'model': self.model,
            'temperature': self.temperature,
            'max_tokens': self.max_tokens,
            'messages': [
                {
                    'role': msg.role,
                    'content': msg.content,
                    'timestamp': msg.timestamp.isoformat(),
                    'token_count': msg.token_count,
                    'cost_usd': msg.cost_usd
                }
                for msg in self.messages
            ],
            'queries': self.queries,
            'context': self.context,
            'tags': self.tags,
            'category': self.category,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat(),
            'last_activity_at': self.last_activity_at.isoformat(),
            'completed_at': self.completed_at.isoformat() if self.completed_at else None,
            'statistics': {
                'total_messages': self.total_messages,
                'total_queries': self.total_queries,
                'total_tokens_used': self.total_tokens_used,
                'total_cost_usd': self.total_cost_usd,
                'average_response_time_ms': self.average_response_time_ms,
                'duration_minutes': self.duration_minutes,
                'message_count_by_role': self.message_count_by_role,
                'average_message_length': self.average_message_length,
                'cost_per_message': self.cost_per_message
            }
        }

    def __str__(self) -> str:
        """String representation."""
        return f"Conversation: {self.get_summary()} ({self.status})"

    def __repr__(self) -> str:
        """Developer representation."""
        return (
            f"Conversation(id='{self.id[:8]}...', "
            f"messages={self.total_messages}, "
            f"status='{self.status}')"
        )

    def __eq__(self, other) -> bool:
        """
        Equality based on identity (id field).

        Args:
            other: Another Conversation object

        Returns:
            True if same identity
        """
        if not isinstance(other, Conversation):
            return False
        return self.id == other.id

    def __hash__(self) -> int:
        """Hash based on identity."""
        return hash(self.id)