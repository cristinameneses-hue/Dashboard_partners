"""
Conversation Manager Use Case

This use case handles all conversation-related operations including:
- Creating new conversations
- Adding messages to conversations
- Managing conversation context
- Retrieving conversation history
- Summarizing conversations
"""

from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from uuid import uuid4

from ..entities.conversation import Conversation, ConversationMessage
from ..entities.user import User
from ..repositories.interfaces import ConversationRepository, LLMRepository
from ..value_objects.query_result import QueryResult
from ..services.interfaces import IPromptManager


@dataclass
class ConversationManagerUseCase:
    """
    Use case for managing conversation lifecycle and operations.

    This use case orchestrates conversation-related business logic,
    coordinating between repositories and domain services.

    Attributes:
        conversation_repository: Repository for persisting conversations
        llm_repository: Repository for LLM interactions (for summarization)
        prompt_manager: Service for managing prompts
        max_context_messages: Maximum messages to maintain in context
        auto_summarize: Whether to automatically summarize long conversations
    """

    conversation_repository: ConversationRepository
    llm_repository: Optional[LLMRepository] = None
    prompt_manager: Optional[IPromptManager] = None
    max_context_messages: int = 50
    auto_summarize: bool = True

    async def create_conversation(
        self,
        user_id: Optional[str] = None,
        session_id: Optional[str] = None,
        title: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Conversation:
        """
        Create a new conversation.

        Args:
            user_id: Optional user identifier
            session_id: Optional session identifier
            title: Optional conversation title
            metadata: Optional metadata dictionary

        Returns:
            Created conversation entity
        """
        conversation = Conversation(
            id=str(uuid4()),
            user_id=user_id,
            session_id=session_id,
            title=title or "New Conversation",
            messages=[],
            created_at=datetime.now(),
            updated_at=datetime.now(),
            metadata=metadata or {},
            is_active=True,
            token_count=0,
            total_cost_usd=0.0
        )

        # Add initial system message if prompt manager is available
        if self.prompt_manager:
            system_prompt = await self.prompt_manager.get_system_prompt()
            system_message = ConversationMessage(
                role="system",
                content=system_prompt,
                timestamp=datetime.now()
            )
            conversation.add_message(system_message)

        # Persist the conversation
        await self.conversation_repository.save(conversation)

        return conversation

    async def add_user_message(
        self,
        conversation_id: str,
        content: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> ConversationMessage:
        """
        Add a user message to a conversation.

        Args:
            conversation_id: Conversation identifier
            content: Message content
            metadata: Optional message metadata

        Returns:
            Created message

        Raises:
            ValueError: If conversation not found
        """
        conversation = await self.conversation_repository.get_by_id(conversation_id)
        if not conversation:
            raise ValueError(f"Conversation {conversation_id} not found")

        message = ConversationMessage(
            role="user",
            content=content,
            timestamp=datetime.now(),
            metadata=metadata
        )

        conversation.add_message(message)

        # Check if summarization is needed
        if self.auto_summarize and len(conversation.messages) > self.max_context_messages:
            await self._summarize_old_messages(conversation)

        # Update conversation
        conversation.updated_at = datetime.now()
        await self.conversation_repository.save(conversation)

        return message

    async def add_assistant_response(
        self,
        conversation_id: str,
        content: str,
        token_count: Optional[int] = None,
        cost_usd: Optional[float] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> ConversationMessage:
        """
        Add an assistant response to a conversation.

        Args:
            conversation_id: Conversation identifier
            content: Response content
            token_count: Optional token count for the response
            cost_usd: Optional cost in USD for the response
            metadata: Optional message metadata

        Returns:
            Created message

        Raises:
            ValueError: If conversation not found
        """
        conversation = await self.conversation_repository.get_by_id(conversation_id)
        if not conversation:
            raise ValueError(f"Conversation {conversation_id} not found")

        message = ConversationMessage(
            role="assistant",
            content=content,
            timestamp=datetime.now(),
            metadata=metadata,
            token_count=token_count,
            cost_usd=cost_usd
        )

        conversation.add_message(message)

        # Update conversation metrics
        if token_count:
            conversation.token_count += token_count
        if cost_usd:
            conversation.total_cost_usd += cost_usd

        conversation.updated_at = datetime.now()
        await self.conversation_repository.save(conversation)

        return message

    async def get_conversation_context(
        self,
        conversation_id: str,
        max_messages: Optional[int] = None
    ) -> List[Dict[str, str]]:
        """
        Get conversation context for LLM interaction.

        Args:
            conversation_id: Conversation identifier
            max_messages: Maximum number of messages to return

        Returns:
            List of message dictionaries suitable for LLM API

        Raises:
            ValueError: If conversation not found
        """
        conversation = await self.conversation_repository.get_by_id(conversation_id)
        if not conversation:
            raise ValueError(f"Conversation {conversation_id} not found")

        max_messages = max_messages or self.max_context_messages

        # Get recent messages
        messages = conversation.get_recent_messages(max_messages)

        # Convert to LLM format
        context = []
        for msg in messages:
            context.append({
                "role": msg.role,
                "content": msg.content
            })

        # Include summary if available
        if conversation.summary:
            context.insert(0, {
                "role": "system",
                "content": f"Previous conversation summary: {conversation.summary}"
            })

        return context

    async def get_conversation_by_id(
        self,
        conversation_id: str
    ) -> Optional[Conversation]:
        """
        Retrieve a conversation by ID.

        Args:
            conversation_id: Conversation identifier

        Returns:
            Conversation entity if found, None otherwise
        """
        return await self.conversation_repository.get_by_id(conversation_id)

    async def get_user_conversations(
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
        return await self.conversation_repository.get_by_user(
            user_id=user_id,
            limit=limit,
            offset=offset,
            only_active=only_active
        )

    async def get_recent_conversations(
        self,
        hours: int = 24,
        limit: int = 50
    ) -> List[Conversation]:
        """
        Get recent conversations within a time window.

        Args:
            hours: Number of hours to look back
            limit: Maximum number of conversations to return

        Returns:
            List of recent conversation entities
        """
        since = datetime.now() - timedelta(hours=hours)
        return await self.conversation_repository.get_recent(
            since=since,
            limit=limit
        )

    async def archive_conversation(
        self,
        conversation_id: str
    ) -> bool:
        """
        Archive a conversation.

        Args:
            conversation_id: Conversation identifier

        Returns:
            True if successful, False otherwise

        Raises:
            ValueError: If conversation not found
        """
        conversation = await self.conversation_repository.get_by_id(conversation_id)
        if not conversation:
            raise ValueError(f"Conversation {conversation_id} not found")

        conversation.archive()
        await self.conversation_repository.save(conversation)

        return True

    async def delete_conversation(
        self,
        conversation_id: str
    ) -> bool:
        """
        Delete a conversation.

        Args:
            conversation_id: Conversation identifier

        Returns:
            True if successful, False otherwise
        """
        return await self.conversation_repository.delete(conversation_id)

    async def generate_title(
        self,
        conversation_id: str
    ) -> str:
        """
        Generate a title for a conversation based on its content.

        Args:
            conversation_id: Conversation identifier

        Returns:
            Generated title

        Raises:
            ValueError: If conversation not found or LLM not available
        """
        if not self.llm_repository:
            raise ValueError("LLM repository required for title generation")

        conversation = await self.conversation_repository.get_by_id(conversation_id)
        if not conversation:
            raise ValueError(f"Conversation {conversation_id} not found")

        # Get first few messages for context
        messages = conversation.get_recent_messages(5)

        # Create prompt for title generation
        prompt = "Generate a short, descriptive title (max 50 chars) for this conversation:\n\n"
        for msg in messages:
            if msg.role in ["user", "assistant"]:
                prompt += f"{msg.role}: {msg.content[:200]}...\n"

        # Generate title using LLM
        response = await self.llm_repository.generate(
            prompt=prompt,
            max_tokens=20,
            temperature=0.7
        )

        # Extract and clean title
        title = response.content.strip()
        if len(title) > 50:
            title = title[:47] + "..."

        # Update conversation
        conversation.title = title
        await self.conversation_repository.save(conversation)

        return title

    async def _summarize_old_messages(
        self,
        conversation: Conversation
    ) -> None:
        """
        Summarize older messages in a conversation.

        This private method is called automatically when conversation
        exceeds max_context_messages.

        Args:
            conversation: Conversation entity to summarize
        """
        if not self.llm_repository:
            return  # Cannot summarize without LLM

        # Get messages to summarize (older than max_context_messages)
        all_messages = conversation.messages
        if len(all_messages) <= self.max_context_messages:
            return

        messages_to_summarize = all_messages[:-self.max_context_messages]

        # Create summarization prompt
        prompt = "Summarize the following conversation concisely:\n\n"
        for msg in messages_to_summarize:
            if msg.role in ["user", "assistant"]:
                prompt += f"{msg.role}: {msg.content}\n"

        # Generate summary
        response = await self.llm_repository.generate(
            prompt=prompt,
            max_tokens=500,
            temperature=0.3
        )

        # Update conversation summary
        conversation.summary = response.content
        conversation.summarized_at = datetime.now()

        # Optionally remove old messages to save space
        # conversation.messages = all_messages[-self.max_context_messages:]

    async def get_conversation_statistics(
        self,
        conversation_id: str
    ) -> Dict[str, Any]:
        """
        Get statistics for a conversation.

        Args:
            conversation_id: Conversation identifier

        Returns:
            Dictionary with conversation statistics

        Raises:
            ValueError: If conversation not found
        """
        conversation = await self.conversation_repository.get_by_id(conversation_id)
        if not conversation:
            raise ValueError(f"Conversation {conversation_id} not found")

        return {
            "id": conversation.id,
            "message_count": len(conversation.messages),
            "user_message_count": conversation.get_message_count_by_role("user"),
            "assistant_message_count": conversation.get_message_count_by_role("assistant"),
            "total_tokens": conversation.token_count,
            "total_cost_usd": conversation.total_cost_usd,
            "duration_seconds": conversation.get_duration().total_seconds() if conversation.get_duration() else 0,
            "created_at": conversation.created_at.isoformat(),
            "updated_at": conversation.updated_at.isoformat(),
            "is_active": conversation.is_active,
            "has_summary": conversation.summary is not None
        }

    async def export_conversation(
        self,
        conversation_id: str,
        format: str = "json"
    ) -> str:
        """
        Export a conversation in various formats.

        Args:
            conversation_id: Conversation identifier
            format: Export format (json, markdown, text)

        Returns:
            Exported conversation as string

        Raises:
            ValueError: If conversation not found or format not supported
        """
        conversation = await self.conversation_repository.get_by_id(conversation_id)
        if not conversation:
            raise ValueError(f"Conversation {conversation_id} not found")

        if format == "json":
            return conversation.to_json()
        elif format == "markdown":
            return conversation.to_markdown()
        elif format == "text":
            return conversation.to_text()
        else:
            raise ValueError(f"Unsupported export format: {format}")