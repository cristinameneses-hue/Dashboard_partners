"""
Repository Interfaces

Abstract base classes for repository pattern following DDD principles.
These interfaces define contracts that infrastructure layer must implement.
"""

from abc import ABC, abstractmethod
from datetime import datetime
from typing import Any, Dict, List, Optional

from ..entities.conversation import Conversation
from ..entities.query import Query
from ..entities.user import User
from ..value_objects.database_type import DatabaseType
from ..value_objects.query_result import QueryResult


class ConversationRepository(ABC):
    """
    Repository interface for Conversation entities.

    This interface defines the contract for persisting and retrieving
    conversation data, regardless of the actual storage mechanism.
    """

    @abstractmethod
    async def save(self, conversation: Conversation) -> Conversation:
        """
        Save a conversation (create or update).

        Args:
            conversation: Conversation entity to save

        Returns:
            Saved conversation entity
        """
        pass

    @abstractmethod
    async def get_by_id(self, conversation_id: str) -> Optional[Conversation]:
        """
        Retrieve a conversation by its ID.

        Args:
            conversation_id: Unique conversation identifier

        Returns:
            Conversation if found, None otherwise
        """
        pass

    @abstractmethod
    async def get_by_user(
        self,
        user_id: str,
        limit: int = 20,
        offset: int = 0,
        only_active: bool = True
    ) -> List[Conversation]:
        """
        Get conversations for a specific user.

        Args:
            user_id: User identifier
            limit: Maximum number of conversations to return
            offset: Number of conversations to skip
            only_active: Whether to return only active conversations

        Returns:
            List of conversation entities
        """
        pass

    @abstractmethod
    async def get_recent(
        self,
        since: datetime,
        limit: int = 50
    ) -> List[Conversation]:
        """
        Get recent conversations within a time window.

        Args:
            since: Datetime to search from
            limit: Maximum number of conversations to return

        Returns:
            List of recent conversation entities
        """
        pass

    @abstractmethod
    async def delete(self, conversation_id: str) -> bool:
        """
        Delete a conversation.

        Args:
            conversation_id: Conversation identifier

        Returns:
            True if successful, False otherwise
        """
        pass

    @abstractmethod
    async def search(
        self,
        query: str,
        user_id: Optional[str] = None,
        limit: int = 20
    ) -> List[Conversation]:
        """
        Search conversations by content.

        Args:
            query: Search query
            user_id: Optional user filter
            limit: Maximum results

        Returns:
            List of matching conversations
        """
        pass


class QueryRepository(ABC):
    """
    Repository interface for Query entities.

    This interface defines the contract for persisting and retrieving
    query data and execution history.
    """

    @abstractmethod
    async def save(self, query: Query) -> Query:
        """
        Save a query (create or update).

        Args:
            query: Query entity to save

        Returns:
            Saved query entity
        """
        pass

    @abstractmethod
    async def get_by_id(self, query_id: str) -> Optional[Query]:
        """
        Retrieve a query by its ID.

        Args:
            query_id: Unique query identifier

        Returns:
            Query if found, None otherwise
        """
        pass

    @abstractmethod
    async def get_by_user(
        self,
        user_id: str,
        limit: int = 20,
        offset: int = 0
    ) -> List[Query]:
        """
        Get queries executed by a specific user.

        Args:
            user_id: User identifier
            limit: Maximum number of queries to return
            offset: Number of queries to skip

        Returns:
            List of query entities
        """
        pass

    @abstractmethod
    async def get_recent(
        self,
        since: datetime,
        limit: int = 100
    ) -> List[Query]:
        """
        Get recent queries within a time window.

        Args:
            since: Datetime to search from
            limit: Maximum number of queries to return

        Returns:
            List of recent query entities
        """
        pass

    @abstractmethod
    async def search(
        self,
        text_pattern: str,
        database_type: Optional[DatabaseType] = None,
        user_id: Optional[str] = None,
        limit: int = 50
    ) -> List[Query]:
        """
        Search queries by pattern.

        Args:
            text_pattern: Text pattern to search for
            database_type: Optional database type filter
            user_id: Optional user filter
            limit: Maximum results

        Returns:
            List of matching queries
        """
        pass


class DatabaseRepository(ABC):
    """
    Repository interface for database queries.

    This interface defines the contract for executing queries
    against different database types (MySQL, MongoDB).
    """

    @abstractmethod
    async def execute_query(
        self,
        query: str,
        database_name: Optional[str] = None,
        options: Optional[Dict[str, Any]] = None
    ) -> QueryResult:
        """
        Execute a query against a database.

        Args:
            query: Query string (SQL or MongoDB query)
            database_name: Optional database name
            options: Optional query options

        Returns:
            QueryResult with execution results
        """
        pass

    @abstractmethod
    async def test_connection(self) -> bool:
        """
        Test database connection.

        Returns:
            True if connection is successful, False otherwise
        """
        pass

    @abstractmethod
    async def get_schema_info(
        self,
        database_name: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Get schema information for a database.

        Args:
            database_name: Optional database name

        Returns:
            Dictionary with schema information
        """
        pass

    @abstractmethod
    def get_database_type(self) -> DatabaseType:
        """
        Get the type of database this repository connects to.

        Returns:
            DatabaseType enum value
        """
        pass


class LLMRepository(ABC):
    """
    Repository interface for Language Model interactions.

    This interface defines the contract for interacting with
    LLM services (OpenAI, ChatGPT, etc.).
    """

    @abstractmethod
    async def generate(
        self,
        prompt: str,
        max_tokens: int = 1000,
        temperature: float = 0.7,
        system_prompt: Optional[str] = None,
        stop_sequences: Optional[List[str]] = None
    ) -> 'LLMResponse':
        """
        Generate text using the LLM.

        Args:
            prompt: User prompt
            max_tokens: Maximum tokens to generate
            temperature: Sampling temperature (0-1)
            system_prompt: Optional system prompt
            stop_sequences: Optional stop sequences

        Returns:
            LLMResponse with generated text and metadata
        """
        pass

    @abstractmethod
    async def generate_streaming(
        self,
        prompt: str,
        max_tokens: int = 1000,
        temperature: float = 0.7,
        system_prompt: Optional[str] = None
    ):
        """
        Generate text using the LLM with streaming.

        Args:
            prompt: User prompt
            max_tokens: Maximum tokens to generate
            temperature: Sampling temperature (0-1)
            system_prompt: Optional system prompt

        Yields:
            Text chunks as they are generated
        """
        pass

    @abstractmethod
    async def analyze_query(
        self,
        query: str,
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Analyze a query for intent and metadata.

        Args:
            query: Query text to analyze
            context: Optional context information

        Returns:
            Dictionary with analysis results
        """
        pass

    @abstractmethod
    def get_model_info(self) -> Dict[str, Any]:
        """
        Get information about the LLM model.

        Returns:
            Dictionary with model information
        """
        pass


class UserRepository(ABC):
    """
    Repository interface for User entities.

    This interface defines the contract for user management
    and authentication.
    """

    @abstractmethod
    async def save(self, user: User) -> User:
        """
        Save a user (create or update).

        Args:
            user: User entity to save

        Returns:
            Saved user entity
        """
        pass

    @abstractmethod
    async def get_by_id(self, user_id: str) -> Optional[User]:
        """
        Retrieve a user by ID.

        Args:
            user_id: User identifier

        Returns:
            User if found, None otherwise
        """
        pass

    @abstractmethod
    async def get_by_username(self, username: str) -> Optional[User]:
        """
        Retrieve a user by username.

        Args:
            username: Username

        Returns:
            User if found, None otherwise
        """
        pass

    @abstractmethod
    async def get_by_email(self, email: str) -> Optional[User]:
        """
        Retrieve a user by email.

        Args:
            email: Email address

        Returns:
            User if found, None otherwise
        """
        pass

    @abstractmethod
    async def authenticate(
        self,
        username: str,
        password: str
    ) -> Optional[User]:
        """
        Authenticate a user.

        Args:
            username: Username or email
            password: Password

        Returns:
            User if authentication successful, None otherwise
        """
        pass

    @abstractmethod
    async def delete(self, user_id: str) -> bool:
        """
        Delete a user.

        Args:
            user_id: User identifier

        Returns:
            True if successful, False otherwise
        """
        pass


# Additional response types

class LLMResponse:
    """Response from LLM generation."""

    def __init__(
        self,
        content: str,
        tokens_used: int,
        cost_usd: float,
        model: str,
        finish_reason: str = "stop",
        metadata: Optional[Dict[str, Any]] = None
    ):
        self.content = content
        self.tokens_used = tokens_used
        self.cost_usd = cost_usd
        self.model = model
        self.finish_reason = finish_reason
        self.metadata = metadata or {}