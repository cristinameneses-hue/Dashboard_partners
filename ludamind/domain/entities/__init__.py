"""
Domain Entities Package

Entities are objects that have a distinct identity that runs through time and
different representations. Unlike value objects, entities can be modified.

Following DDD principles:
- Identity: Each entity has a unique identifier
- Lifecycle: Entities have a lifecycle (created, modified, deleted)
- Business Logic: Entities contain business rules and behaviors
"""

from .query import Query
from .database import Database
from .conversation import Conversation, ConversationMessage
from .user import User, UserRole, SubscriptionTier, UserPreferences, UserQuota

__all__ = [
    'Query',
    'Database',
    'Conversation',
    'ConversationMessage',
    'User',
    'UserRole',
    'SubscriptionTier',
    'UserPreferences',
    'UserQuota'
]