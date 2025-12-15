"""
User Entity

Represents a user in the system.
This entity manages user information, preferences, and access control.
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, List, Optional, Any, Set
from uuid import uuid4
from enum import Enum


class UserRole(str, Enum):
    """User roles for access control."""
    ADMIN = "admin"
    ANALYST = "analyst"
    BUSINESS = "business"
    VIEWER = "viewer"
    DEVELOPER = "developer"
    GUEST = "guest"


class SubscriptionTier(str, Enum):
    """Subscription tiers for usage limits."""
    FREE = "free"
    BASIC = "basic"
    PROFESSIONAL = "professional"
    ENTERPRISE = "enterprise"


@dataclass
class UserPreferences:
    """
    Value object representing user preferences.

    Nested within the User entity.
    """

    # Interface preferences
    language: str = "es"  # Default to Spanish
    timezone: str = "Europe/Madrid"
    theme: str = "light"  # light, dark, auto

    # Query preferences
    default_database: Optional[str] = None  # Preferred database
    default_model: str = "gpt-4o-mini"
    default_temperature: float = 0.1
    max_tokens: int = 2000
    streaming_enabled: bool = True

    # Notification preferences
    email_notifications: bool = True
    query_result_notifications: bool = False
    error_notifications: bool = True

    # Display preferences
    results_per_page: int = 20
    show_query_cost: bool = True
    show_execution_time: bool = True
    date_format: str = "DD/MM/YYYY"
    number_format: str = "es-ES"  # Locale for number formatting


@dataclass
class UserQuota:
    """
    Value object representing user usage quotas.

    Nested within the User entity.
    """

    # Query limits
    max_queries_per_day: int = 100
    max_queries_per_month: int = 3000
    max_tokens_per_query: int = 4000
    max_cost_per_month_usd: float = 50.0

    # Database access limits
    max_databases: int = 5
    max_concurrent_queries: int = 3
    max_result_rows: int = 1000

    # Current usage (reset periodically)
    queries_today: int = 0
    queries_this_month: int = 0
    tokens_this_month: int = 0
    cost_this_month_usd: float = 0.0

    # Reset timestamps
    daily_reset_at: datetime = field(default_factory=datetime.now)
    monthly_reset_at: datetime = field(default_factory=datetime.now)


@dataclass
class User:
    """
    Entity representing a user.

    This entity encapsulates user information, authentication,
    preferences, and usage tracking.

    Identity is maintained through the `id` field.
    """

    # Identity
    id: str = field(default_factory=lambda: str(uuid4()))
    username: str = ""  # Unique username
    email: str = ""  # Unique email

    # Profile information
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    display_name: Optional[str] = None
    avatar_url: Optional[str] = None
    bio: Optional[str] = None
    company: Optional[str] = None
    department: Optional[str] = None

    # Authentication
    hashed_password: Optional[str] = None  # Bcrypt hashed
    api_key: Optional[str] = None  # For API access
    oauth_provider: Optional[str] = None  # google, microsoft, etc.
    oauth_id: Optional[str] = None

    # Access control
    role: UserRole = UserRole.VIEWER
    subscription_tier: SubscriptionTier = SubscriptionTier.FREE
    permissions: Set[str] = field(default_factory=set)  # Granular permissions
    allowed_databases: List[str] = field(default_factory=list)  # Specific database access

    # Preferences and quotas
    preferences: UserPreferences = field(default_factory=UserPreferences)
    quota: UserQuota = field(default_factory=UserQuota)

    # Status
    is_active: bool = True
    is_verified: bool = False  # Email verified
    is_locked: bool = False  # Account locked
    lock_reason: Optional[str] = None

    # Metadata
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    last_login_at: Optional[datetime] = None
    last_activity_at: Optional[datetime] = None
    email_verified_at: Optional[datetime] = None
    password_changed_at: Optional[datetime] = None

    # Statistics
    total_queries: int = 0
    total_conversations: int = 0
    total_tokens_used: int = 0
    total_cost_usd: float = 0.0
    favorite_queries: List[str] = field(default_factory=list)  # Query IDs
    saved_queries: List[Dict[str, Any]] = field(default_factory=list)  # Query templates

    # Session management
    active_sessions: List[str] = field(default_factory=list)  # Session IDs
    last_ip_address: Optional[str] = None
    last_user_agent: Optional[str] = None

    def __post_init__(self):
        """Initialize and validate the user entity."""
        self.validate()
        self._set_default_permissions()
        self._set_quota_by_tier()

    def validate(self):
        """
        Validate the user entity.

        Raises:
            ValueError: If validation fails
        """
        if not self.username:
            raise ValueError("Username cannot be empty")

        if not self.email:
            raise ValueError("Email cannot be empty")

        # Basic email validation
        if '@' not in self.email or '.' not in self.email.split('@')[1]:
            raise ValueError(f"Invalid email format: {self.email}")

        # Username validation (alphanumeric, underscore, dash)
        import re
        if not re.match(r'^[a-zA-Z0-9_-]+$', self.username):
            raise ValueError(f"Invalid username format: {self.username}")

        if len(self.username) < 3 or len(self.username) > 50:
            raise ValueError("Username must be between 3 and 50 characters")

    def _set_default_permissions(self):
        """Set default permissions based on role."""
        role_permissions = {
            UserRole.ADMIN: {
                'query.execute', 'query.view_all', 'database.manage',
                'user.manage', 'system.configure', 'logs.view'
            },
            UserRole.ANALYST: {
                'query.execute', 'query.view_own', 'database.read',
                'export.data', 'report.create'
            },
            UserRole.BUSINESS: {
                'query.execute', 'query.view_own', 'database.read',
                'report.view'
            },
            UserRole.VIEWER: {
                'query.view_own', 'database.list'
            },
            UserRole.DEVELOPER: {
                'query.execute', 'query.view_own', 'database.read',
                'api.access', 'logs.view_own'
            },
            UserRole.GUEST: {
                'query.view_public'
            }
        }

        if self.role in role_permissions:
            self.permissions.update(role_permissions[self.role])

    def _set_quota_by_tier(self):
        """Set quota limits based on subscription tier."""
        tier_quotas = {
            SubscriptionTier.FREE: {
                'max_queries_per_day': 10,
                'max_queries_per_month': 100,
                'max_tokens_per_query': 2000,
                'max_cost_per_month_usd': 1.0,
                'max_databases': 1,
                'max_concurrent_queries': 1,
                'max_result_rows': 100
            },
            SubscriptionTier.BASIC: {
                'max_queries_per_day': 50,
                'max_queries_per_month': 1000,
                'max_tokens_per_query': 4000,
                'max_cost_per_month_usd': 10.0,
                'max_databases': 3,
                'max_concurrent_queries': 2,
                'max_result_rows': 500
            },
            SubscriptionTier.PROFESSIONAL: {
                'max_queries_per_day': 200,
                'max_queries_per_month': 5000,
                'max_tokens_per_query': 8000,
                'max_cost_per_month_usd': 50.0,
                'max_databases': 10,
                'max_concurrent_queries': 5,
                'max_result_rows': 2000
            },
            SubscriptionTier.ENTERPRISE: {
                'max_queries_per_day': 1000,
                'max_queries_per_month': 50000,
                'max_tokens_per_query': 16000,
                'max_cost_per_month_usd': 500.0,
                'max_databases': -1,  # Unlimited
                'max_concurrent_queries': 20,
                'max_result_rows': 10000
            }
        }

        if self.subscription_tier in tier_quotas:
            tier_config = tier_quotas[self.subscription_tier]
            for key, value in tier_config.items():
                setattr(self.quota, key, value)

    # Business methods

    def authenticate(self, password_hash: str) -> bool:
        """
        Authenticate user with password hash.

        Args:
            password_hash: Hashed password to compare

        Returns:
            True if authentication successful
        """
        if not self.is_active:
            return False

        if self.is_locked:
            return False

        return self.hashed_password == password_hash

    def login(self, session_id: str, ip_address: Optional[str] = None,
             user_agent: Optional[str] = None):
        """
        Record user login.

        Args:
            session_id: Session identifier
            ip_address: Client IP address
            user_agent: Client user agent
        """
        self.last_login_at = datetime.now()
        self.last_activity_at = datetime.now()

        if session_id not in self.active_sessions:
            self.active_sessions.append(session_id)

        if ip_address:
            self.last_ip_address = ip_address

        if user_agent:
            self.last_user_agent = user_agent

        self.updated_at = datetime.now()

    def logout(self, session_id: str):
        """
        Record user logout.

        Args:
            session_id: Session to logout
        """
        if session_id in self.active_sessions:
            self.active_sessions.remove(session_id)
            self.updated_at = datetime.now()

    def verify_email(self):
        """Mark email as verified."""
        self.is_verified = True
        self.email_verified_at = datetime.now()
        self.updated_at = datetime.now()

    def lock_account(self, reason: str):
        """
        Lock the user account.

        Args:
            reason: Reason for locking
        """
        self.is_locked = True
        self.lock_reason = reason
        self.updated_at = datetime.now()

    def unlock_account(self):
        """Unlock the user account."""
        self.is_locked = False
        self.lock_reason = None
        self.updated_at = datetime.now()

    def change_password(self, new_password_hash: str):
        """
        Change user password.

        Args:
            new_password_hash: New password hash
        """
        self.hashed_password = new_password_hash
        self.password_changed_at = datetime.now()
        self.updated_at = datetime.now()

    def update_role(self, new_role: UserRole):
        """
        Update user role.

        Args:
            new_role: New role to assign
        """
        self.role = new_role
        self.permissions.clear()
        self._set_default_permissions()
        self.updated_at = datetime.now()

    def upgrade_subscription(self, new_tier: SubscriptionTier):
        """
        Upgrade subscription tier.

        Args:
            new_tier: New subscription tier
        """
        self.subscription_tier = new_tier
        self._set_quota_by_tier()
        self.updated_at = datetime.now()

    def grant_permission(self, permission: str):
        """
        Grant a specific permission.

        Args:
            permission: Permission to grant
        """
        self.permissions.add(permission)
        self.updated_at = datetime.now()

    def revoke_permission(self, permission: str):
        """
        Revoke a specific permission.

        Args:
            permission: Permission to revoke
        """
        self.permissions.discard(permission)
        self.updated_at = datetime.now()

    def grant_database_access(self, database_name: str):
        """
        Grant access to a specific database.

        Args:
            database_name: Database to grant access to
        """
        if database_name not in self.allowed_databases:
            self.allowed_databases.append(database_name)
            self.updated_at = datetime.now()

    def revoke_database_access(self, database_name: str):
        """
        Revoke access to a specific database.

        Args:
            database_name: Database to revoke access from
        """
        if database_name in self.allowed_databases:
            self.allowed_databases.remove(database_name)
            self.updated_at = datetime.now()

    def record_query(self, tokens_used: int = 0, cost_usd: float = 0.0):
        """
        Record a query execution.

        Args:
            tokens_used: Tokens consumed
            cost_usd: Cost in USD
        """
        self.total_queries += 1
        self.total_tokens_used += tokens_used
        self.total_cost_usd += cost_usd

        self.quota.queries_today += 1
        self.quota.queries_this_month += 1
        self.quota.tokens_this_month += tokens_used
        self.quota.cost_this_month_usd += cost_usd

        self.last_activity_at = datetime.now()
        self.updated_at = datetime.now()

    def reset_daily_quota(self):
        """Reset daily usage quota."""
        self.quota.queries_today = 0
        self.quota.daily_reset_at = datetime.now()
        self.updated_at = datetime.now()

    def reset_monthly_quota(self):
        """Reset monthly usage quota."""
        self.quota.queries_this_month = 0
        self.quota.tokens_this_month = 0
        self.quota.cost_this_month_usd = 0.0
        self.quota.monthly_reset_at = datetime.now()
        self.updated_at = datetime.now()

    def add_favorite_query(self, query_id: str):
        """
        Add a query to favorites.

        Args:
            query_id: Query ID to favorite
        """
        if query_id not in self.favorite_queries:
            self.favorite_queries.append(query_id)
            self.updated_at = datetime.now()

    def remove_favorite_query(self, query_id: str):
        """
        Remove a query from favorites.

        Args:
            query_id: Query ID to unfavorite
        """
        if query_id in self.favorite_queries:
            self.favorite_queries.remove(query_id)
            self.updated_at = datetime.now()

    def save_query_template(self, name: str, template: str, description: str = ""):
        """
        Save a query template.

        Args:
            name: Template name
            template: Query template
            description: Template description
        """
        self.saved_queries.append({
            'id': str(uuid4()),
            'name': name,
            'template': template,
            'description': description,
            'created_at': datetime.now().isoformat()
        })
        self.updated_at = datetime.now()

    # Query methods

    @property
    def full_name(self) -> str:
        """Get user's full name."""
        if self.first_name and self.last_name:
            return f"{self.first_name} {self.last_name}"
        return self.display_name or self.username

    @property
    def can_query(self) -> bool:
        """Check if user can execute queries."""
        return 'query.execute' in self.permissions

    @property
    def is_admin(self) -> bool:
        """Check if user is an admin."""
        return self.role == UserRole.ADMIN

    @property
    def has_api_access(self) -> bool:
        """Check if user has API access."""
        return 'api.access' in self.permissions or self.api_key is not None

    @property
    def quota_exceeded(self) -> bool:
        """Check if any quota is exceeded."""
        if self.subscription_tier == SubscriptionTier.ENTERPRISE:
            return False  # No limits for enterprise

        return (
            self.quota.queries_today >= self.quota.max_queries_per_day or
            self.quota.queries_this_month >= self.quota.max_queries_per_month or
            self.quota.cost_this_month_usd >= self.quota.max_cost_per_month_usd
        )

    @property
    def days_since_registration(self) -> int:
        """Get days since registration."""
        return (datetime.now() - self.created_at).days

    def has_permission(self, permission: str) -> bool:
        """
        Check if user has a specific permission.

        Args:
            permission: Permission to check

        Returns:
            True if user has permission
        """
        return permission in self.permissions or self.is_admin

    def can_access_database(self, database_name: str) -> bool:
        """
        Check if user can access a database.

        Args:
            database_name: Database to check

        Returns:
            True if access allowed
        """
        if self.is_admin:
            return True

        if not self.allowed_databases:  # Empty means all databases
            return True

        return database_name in self.allowed_databases

    def to_dict(self) -> Dict[str, Any]:
        """
        Convert to dictionary for serialization.

        Returns:
            Dictionary representation
        """
        return {
            'id': self.id,
            'username': self.username,
            'email': self.email,
            'full_name': self.full_name,
            'display_name': self.display_name,
            'avatar_url': self.avatar_url,
            'role': self.role.value,
            'subscription_tier': self.subscription_tier.value,
            'is_active': self.is_active,
            'is_verified': self.is_verified,
            'is_locked': self.is_locked,
            'profile': {
                'first_name': self.first_name,
                'last_name': self.last_name,
                'bio': self.bio,
                'company': self.company,
                'department': self.department
            },
            'preferences': {
                'language': self.preferences.language,
                'timezone': self.preferences.timezone,
                'theme': self.preferences.theme,
                'default_model': self.preferences.default_model,
                'streaming_enabled': self.preferences.streaming_enabled
            },
            'quota': {
                'limits': {
                    'queries_per_day': self.quota.max_queries_per_day,
                    'queries_per_month': self.quota.max_queries_per_month,
                    'cost_per_month_usd': self.quota.max_cost_per_month_usd
                },
                'usage': {
                    'queries_today': self.quota.queries_today,
                    'queries_this_month': self.quota.queries_this_month,
                    'cost_this_month_usd': self.quota.cost_this_month_usd
                }
            },
            'statistics': {
                'total_queries': self.total_queries,
                'total_conversations': self.total_conversations,
                'total_tokens_used': self.total_tokens_used,
                'total_cost_usd': self.total_cost_usd,
                'days_since_registration': self.days_since_registration
            },
            'timestamps': {
                'created_at': self.created_at.isoformat(),
                'updated_at': self.updated_at.isoformat(),
                'last_login_at': self.last_login_at.isoformat() if self.last_login_at else None,
                'last_activity_at': self.last_activity_at.isoformat() if self.last_activity_at else None
            },
            'permissions': list(self.permissions),
            'allowed_databases': self.allowed_databases
        }

    def __str__(self) -> str:
        """String representation."""
        return f"{self.full_name} ({self.username}) - {self.role.value}"

    def __repr__(self) -> str:
        """Developer representation."""
        status = "active" if self.is_active else "inactive"
        return f"User(username='{self.username}', role={self.role.value}, status={status})"

    def __eq__(self, other) -> bool:
        """
        Equality based on identity (id field).

        Args:
            other: Another User object

        Returns:
            True if same identity
        """
        if not isinstance(other, User):
            return False
        return self.id == other.id

    def __hash__(self) -> int:
        """Hash based on identity."""
        return hash(self.id)