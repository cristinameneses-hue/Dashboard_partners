"""
Domain Service Interfaces

Abstract base classes for domain services following DDD principles.
These interfaces define contracts that can be implemented by
concrete services.
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional


class IPromptManager(ABC):
    """
    Interface for managing system prompts.

    This service manages the prompts used for LLM interactions,
    including system prompts, templates, and context generation.
    """

    @abstractmethod
    async def get_system_prompt(
        self,
        context_type: str = "default"
    ) -> str:
        """
        Get the system prompt for a given context.

        Args:
            context_type: Type of context (default, chat, query, etc.)

        Returns:
            System prompt string
        """
        pass

    @abstractmethod
    async def get_query_prompt(
        self,
        query: str,
        database_type: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Generate a prompt for query execution.

        Args:
            query: User query
            database_type: Optional database type hint
            context: Optional additional context

        Returns:
            Formatted prompt for LLM
        """
        pass

    @abstractmethod
    async def get_routing_prompt(
        self,
        query: str
    ) -> str:
        """
        Generate a prompt for query routing decision.

        Args:
            query: User query

        Returns:
            Formatted prompt for routing decision
        """
        pass

    @abstractmethod
    async def update_prompt(
        self,
        prompt_type: str,
        content: str
    ) -> bool:
        """
        Update a prompt template.

        Args:
            prompt_type: Type of prompt to update
            content: New prompt content

        Returns:
            True if successful, False otherwise
        """
        pass

    @abstractmethod
    def get_available_prompts(self) -> Dict[str, str]:
        """
        Get all available prompt types.

        Returns:
            Dictionary of prompt types and descriptions
        """
        pass