"""
Domain Value Objects Package

Value Objects are immutable objects that represent domain concepts.
They have no identity and are compared by their values.

Following DDD principles:
- Immutability: Once created, their state cannot change
- Value Equality: Two value objects with the same values are considered equal
- Self-Validation: They validate their own state upon creation
"""

from .database_type import DatabaseType
from .query_result import QueryResult
from .routing_decision import RoutingDecision
from .time_range import TimeRange
from .query_intent import QueryIntent

__all__ = [
    'DatabaseType',
    'QueryResult',
    'RoutingDecision',
    'TimeRange',
    'QueryIntent'
]