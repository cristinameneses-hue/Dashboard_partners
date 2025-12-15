"""
Domain Repositories Package

This package contains the repository interfaces (abstractions) that define
the contracts for data access. These interfaces follow the Dependency Inversion
Principle (DIP) - the domain layer depends on abstractions, not concrete implementations.

Repository Pattern Benefits:
- Decoupling: Domain doesn't know about database implementation details
- Testability: Easy to mock repositories for testing
- Flexibility: Can swap implementations without changing domain logic
"""

from .database_repository import DatabaseRepository
from .llm_repository import LLMRepository

__all__ = [
    'DatabaseRepository',
    'LLMRepository'
]