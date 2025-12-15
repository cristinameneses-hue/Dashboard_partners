"""
Domain Services Package

Domain services contain business logic that doesn't naturally fit
within a single entity or value object. They typically coordinate
between multiple entities or provide specialized business operations.

Following DDD principles:
- Domain services are stateless
- Domain services contain core business logic
- Domain services are independent of infrastructure
"""

from .query_router import QueryRouterService, RoutingStrategy

__all__ = [
    'QueryRouterService',
    'RoutingStrategy'
]