"""
Database Entity

Represents a database configuration in the system.
This entity manages database connection information and metadata.
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional
from uuid import uuid4

from ..value_objects import DatabaseType


@dataclass
class Database:
    """
    Entity representing a database configuration.

    This entity encapsulates database connection information,
    permissions, and operational metadata.
    """

    # Identity
    id: str = field(default_factory=lambda: str(uuid4()))
    name: str = ""  # Unique database name (e.g., 'trends', 'ludafarma')

    # Configuration
    type: DatabaseType = DatabaseType.MYSQL
    connection_string: str = ""  # Connection URL
    host: str = ""
    port: int = 3306
    database_name: str = ""  # Actual database name in the server
    username: Optional[str] = None

    # Permissions (following principle of least privilege)
    can_read: bool = True
    can_insert: bool = False
    can_update: bool = False
    can_delete: bool = False
    can_execute_ddl: bool = False  # CREATE, ALTER, DROP

    # Operational settings
    is_default: bool = False  # Is this the default database for its type?
    is_active: bool = True  # Is this database currently active?
    max_connections: int = 20  # Maximum connection pool size
    connection_timeout: int = 30  # Timeout in seconds
    query_timeout: int = 60  # Default query timeout in seconds

    # Metadata
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    last_connected_at: Optional[datetime] = None
    last_error_at: Optional[datetime] = None
    last_error_message: Optional[str] = None

    # Statistics
    total_queries_executed: int = 0
    total_errors: int = 0
    average_query_time_ms: float = 0.0

    # Schema information (cached)
    tables_or_collections: List[str] = field(default_factory=list)
    size_mb: Optional[float] = None
    version: Optional[str] = None

    def __post_init__(self):
        """Initialize and validate the database entity."""
        self.validate()
        self._parse_connection_string()

    def validate(self):
        """
        Validate the database entity.

        Raises:
            ValueError: If validation fails
        """
        if not self.name:
            raise ValueError("Database name cannot be empty")

        if not self.connection_string:
            raise ValueError("Connection string cannot be empty")

        if self.port <= 0 or self.port > 65535:
            raise ValueError(f"Invalid port number: {self.port}")

        if self.max_connections <= 0:
            raise ValueError("Maximum connections must be positive")

        if self.connection_timeout <= 0:
            raise ValueError("Connection timeout must be positive")

    def _parse_connection_string(self):
        """Parse connection string to extract components if not already set."""
        if not self.host and self.connection_string:
            # Simple parsing for MySQL and MongoDB URLs
            if self.type == DatabaseType.MYSQL:
                # mysql://user:pass@host:port/database
                try:
                    from urllib.parse import urlparse
                    parsed = urlparse(self.connection_string)
                    if not self.host:
                        self.host = parsed.hostname or "localhost"
                    if not self.port:
                        self.port = parsed.port or 3306
                    if not self.database_name:
                        self.database_name = parsed.path.lstrip('/') if parsed.path else ""
                    if not self.username:
                        self.username = parsed.username
                except Exception:
                    pass  # Keep manually set values

            elif self.type == DatabaseType.MONGODB:
                # mongodb://user:pass@host:port/database
                try:
                    from urllib.parse import urlparse
                    parsed = urlparse(self.connection_string)
                    if not self.host:
                        self.host = parsed.hostname or "localhost"
                    if not self.port:
                        self.port = parsed.port or 27017
                    if not self.database_name:
                        # MongoDB connection strings can have the database in the path
                        path = parsed.path.lstrip('/')
                        if path:
                            self.database_name = path.split('?')[0]
                    if not self.username:
                        self.username = parsed.username
                except Exception:
                    pass  # Keep manually set values

    # Business methods

    def activate(self):
        """Activate the database."""
        self.is_active = True
        self.updated_at = datetime.now()

    def deactivate(self):
        """Deactivate the database."""
        self.is_active = False
        self.updated_at = datetime.now()

    def set_as_default(self):
        """Set this database as the default for its type."""
        self.is_default = True
        self.updated_at = datetime.now()

    def unset_as_default(self):
        """Unset this database as the default."""
        self.is_default = False
        self.updated_at = datetime.now()

    def record_connection_success(self):
        """Record a successful connection."""
        self.last_connected_at = datetime.now()
        self.last_error_at = None
        self.last_error_message = None

    def record_connection_error(self, error_message: str):
        """
        Record a connection error.

        Args:
            error_message: The error message
        """
        self.last_error_at = datetime.now()
        self.last_error_message = error_message
        self.total_errors += 1

    def record_query_execution(self, execution_time_ms: float, success: bool = True):
        """
        Record query execution statistics.

        Args:
            execution_time_ms: Query execution time in milliseconds
            success: Whether the query was successful
        """
        self.total_queries_executed += 1

        if not success:
            self.total_errors += 1

        # Update average query time (simple moving average)
        if self.total_queries_executed == 1:
            self.average_query_time_ms = execution_time_ms
        else:
            # Weighted average giving more weight to recent queries
            self.average_query_time_ms = (
                (self.average_query_time_ms * 0.9) + (execution_time_ms * 0.1)
            )

        self.updated_at = datetime.now()

    def update_schema_info(self, tables_or_collections: List[str],
                          size_mb: Optional[float] = None,
                          version: Optional[str] = None):
        """
        Update cached schema information.

        Args:
            tables_or_collections: List of table/collection names
            size_mb: Database size in MB
            version: Database version
        """
        self.tables_or_collections = tables_or_collections
        self.size_mb = size_mb
        self.version = version
        self.updated_at = datetime.now()

    def grant_permission(self, permission: str):
        """
        Grant a permission to this database.

        Args:
            permission: Permission to grant (read, insert, update, delete, execute_ddl)
        """
        permission_map = {
            'read': 'can_read',
            'insert': 'can_insert',
            'update': 'can_update',
            'delete': 'can_delete',
            'execute_ddl': 'can_execute_ddl'
        }

        if permission in permission_map:
            setattr(self, permission_map[permission], True)
            self.updated_at = datetime.now()
        else:
            raise ValueError(f"Invalid permission: {permission}")

    def revoke_permission(self, permission: str):
        """
        Revoke a permission from this database.

        Args:
            permission: Permission to revoke
        """
        permission_map = {
            'read': 'can_read',
            'insert': 'can_insert',
            'update': 'can_update',
            'delete': 'can_delete',
            'execute_ddl': 'can_execute_ddl'
        }

        if permission in permission_map:
            setattr(self, permission_map[permission], False)
            self.updated_at = datetime.now()
        else:
            raise ValueError(f"Invalid permission: {permission}")

    # Query methods

    @property
    def is_read_only(self) -> bool:
        """Check if this database is read-only."""
        return (
            self.can_read and
            not self.can_insert and
            not self.can_update and
            not self.can_delete and
            not self.can_execute_ddl
        )

    @property
    def has_write_permissions(self) -> bool:
        """Check if this database has any write permissions."""
        return self.can_insert or self.can_update or self.can_delete

    @property
    def is_healthy(self) -> bool:
        """Check if the database is considered healthy."""
        if not self.is_active:
            return False

        # Consider unhealthy if last connection was an error
        if self.last_error_at and self.last_connected_at:
            return self.last_error_at < self.last_connected_at

        # Consider healthy if we've ever connected successfully
        return self.last_connected_at is not None

    @property
    def error_rate(self) -> float:
        """Calculate the error rate."""
        if self.total_queries_executed == 0:
            return 0.0
        return self.total_errors / self.total_queries_executed

    def get_connection_info(self) -> Dict[str, Any]:
        """
        Get connection information (without sensitive data).

        Returns:
            Dictionary with connection info
        """
        return {
            'host': self.host,
            'port': self.port,
            'database': self.database_name,
            'type': self.type.value,
            'username': self.username,
            'max_connections': self.max_connections,
            'connection_timeout': self.connection_timeout,
            'query_timeout': self.query_timeout
        }

    def to_dict(self) -> Dict[str, Any]:
        """
        Convert to dictionary for serialization.

        Returns:
            Dictionary representation
        """
        return {
            'id': self.id,
            'name': self.name,
            'type': self.type.value,
            'host': self.host,
            'port': self.port,
            'database_name': self.database_name,
            'username': self.username,
            'permissions': {
                'can_read': self.can_read,
                'can_insert': self.can_insert,
                'can_update': self.can_update,
                'can_delete': self.can_delete,
                'can_execute_ddl': self.can_execute_ddl
            },
            'is_default': self.is_default,
            'is_active': self.is_active,
            'is_healthy': self.is_healthy,
            'is_read_only': self.is_read_only,
            'max_connections': self.max_connections,
            'connection_timeout': self.connection_timeout,
            'query_timeout': self.query_timeout,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat(),
            'last_connected_at': self.last_connected_at.isoformat() if self.last_connected_at else None,
            'last_error_at': self.last_error_at.isoformat() if self.last_error_at else None,
            'last_error_message': self.last_error_message,
            'statistics': {
                'total_queries': self.total_queries_executed,
                'total_errors': self.total_errors,
                'error_rate': self.error_rate,
                'average_query_time_ms': self.average_query_time_ms
            },
            'schema': {
                'tables_or_collections': self.tables_or_collections,
                'size_mb': self.size_mb,
                'version': self.version
            }
        }

    def __str__(self) -> str:
        """String representation."""
        return f"{self.name} ({self.type.value}) - {self.host}:{self.port}/{self.database_name}"

    def __repr__(self) -> str:
        """Developer representation."""
        status = "active" if self.is_active else "inactive"
        return f"Database(name='{self.name}', type={self.type.value}, status={status})"

    def __eq__(self, other) -> bool:
        """Equality based on identity."""
        if not isinstance(other, Database):
            return False
        return self.id == other.id

    def __hash__(self) -> int:
        """Hash based on identity."""
        return hash(self.id)