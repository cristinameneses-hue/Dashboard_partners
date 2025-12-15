"""
Database Connection Factory Service

Factory pattern implementation for creating database connections.
Follows Open/Closed Principle - open for extension, closed for modification.
"""

import logging
from typing import Dict, Optional, Any
from urllib.parse import urlparse
import os

from domain.repositories import DatabaseRepository
from domain.value_objects import DatabaseType
from infrastructure.repositories import MySQLRepository, MongoDBRepository


logger = logging.getLogger(__name__)


class DatabaseConnectionFactory:
    """
    Factory for creating database repository instances.

    This class implements the Factory pattern to create appropriate
    database repository instances based on configuration.
    """

    # Registry of database types to repository classes
    _repository_registry: Dict[DatabaseType, type] = {
        DatabaseType.MYSQL: MySQLRepository,
        DatabaseType.MONGODB: MongoDBRepository
    }

    def __init__(self):
        """Initialize the factory."""
        self._connections: Dict[str, DatabaseRepository] = {}
        self._configurations: Dict[str, Dict[str, Any]] = {}

    @classmethod
    def register_repository(cls, database_type: DatabaseType, repository_class: type):
        """
        Register a new repository type.

        Allows extending the factory with new database types without
        modifying existing code (Open/Closed Principle).

        Args:
            database_type: Type of database
            repository_class: Repository class to register
        """
        cls._repository_registry[database_type] = repository_class
        logger.info(f"Registered repository {repository_class.__name__} for {database_type.value}")

    def create_connection(self,
                         name: str,
                         connection_string: str,
                         database_type: Optional[DatabaseType] = None,
                         **kwargs) -> DatabaseRepository:
        """
        Create a database connection.

        Args:
            name: Connection name/identifier
            connection_string: Database connection string
            database_type: Type of database (auto-detected if not provided)
            **kwargs: Additional connection parameters

        Returns:
            DatabaseRepository instance

        Raises:
            ValueError: If database type cannot be determined or is unsupported
        """
        # Auto-detect database type from connection string
        if not database_type:
            database_type = self._detect_database_type(connection_string)

        if database_type not in self._repository_registry:
            raise ValueError(f"Unsupported database type: {database_type}")

        # Parse connection string
        config = self._parse_connection_string(connection_string, database_type)
        config.update(kwargs)

        # Store configuration
        self._configurations[name] = {
            'type': database_type,
            'connection_string': connection_string,
            'config': config
        }

        # Create repository instance
        repository_class = self._repository_registry[database_type]

        try:
            if database_type == DatabaseType.MYSQL:
                repository = repository_class(
                    host=config.get('host', 'localhost'),
                    port=config.get('port', 3306),
                    database=config.get('database', ''),
                    username=config.get('username', ''),
                    password=config.get('password', ''),
                    **{k: v for k, v in config.items()
                       if k not in ['host', 'port', 'database', 'username', 'password']}
                )
            elif database_type == DatabaseType.MONGODB:
                repository = repository_class(
                    connection_string=connection_string,
                    database_name=config.get('database', ''),
                    **{k: v for k, v in config.items()
                       if k not in ['connection_string', 'database']}
                )
            else:
                # Generic fallback for future database types
                repository = repository_class(**config)

            # Store connection
            self._connections[name] = repository
            logger.info(f"Created {database_type.value} connection: {name}")

            return repository

        except Exception as e:
            logger.error(f"Failed to create connection {name}: {str(e)}")
            raise RuntimeError(f"Connection creation failed: {str(e)}")

    def create_from_env(self, prefix: str = "") -> Dict[str, DatabaseRepository]:
        """
        Create connections from environment variables.

        Looks for patterns:
        - DB_<NAME>_URL for MySQL
        - MONGO_<NAME>_URL for MongoDB

        Args:
            prefix: Optional prefix for environment variables

        Returns:
            Dictionary of connection name to repository
        """
        connections = {}

        # Scan environment for database URLs
        for key, value in os.environ.items():
            if not value:
                continue

            # MySQL pattern
            if key.startswith(f"{prefix}DB_") and key.endswith("_URL"):
                name = key[len(f"{prefix}DB_"):-4].lower()

                # Load additional settings
                settings = self._load_env_settings(key.replace("_URL", ""))

                try:
                    repo = self.create_connection(
                        name=name,
                        connection_string=value,
                        database_type=DatabaseType.MYSQL,
                        **settings
                    )
                    connections[name] = repo
                except Exception as e:
                    logger.error(f"Failed to create MySQL connection {name}: {e}")

            # MongoDB pattern
            elif key.startswith(f"{prefix}MONGO_") and key.endswith("_URL"):
                name = key[len(f"{prefix}MONGO_"):-4].lower()

                # Load additional settings
                settings = self._load_env_settings(key.replace("_URL", ""))

                try:
                    repo = self.create_connection(
                        name=name,
                        connection_string=value,
                        database_type=DatabaseType.MONGODB,
                        **settings
                    )
                    connections[name] = repo
                except Exception as e:
                    logger.error(f"Failed to create MongoDB connection {name}: {e}")

        logger.info(f"Created {len(connections)} connections from environment")
        return connections

    def _load_env_settings(self, base_key: str) -> Dict[str, Any]:
        """
        Load additional settings from environment.

        Args:
            base_key: Base environment variable key

        Returns:
            Dictionary of settings
        """
        settings = {}

        # Permission settings
        for perm in ['CAN_INSERT', 'CAN_UPDATE', 'CAN_DELETE', 'CAN_EXECUTE_DDL']:
            env_key = f"{base_key}_{perm}"
            if env_key in os.environ:
                settings[perm.lower()] = os.environ[env_key].lower() == 'true'

        # Connection settings
        for setting in ['MAX_CONNECTIONS', 'CONNECTION_TIMEOUT', 'QUERY_TIMEOUT']:
            env_key = f"{base_key}_{setting}"
            if env_key in os.environ:
                try:
                    settings[setting.lower()] = int(os.environ[env_key])
                except ValueError:
                    pass

        # Read-only mode
        if all(not settings.get(f"can_{op}", False) for op in ['insert', 'update', 'delete']):
            settings['read_only'] = True

        # Default database flag
        if f"{base_key}_IS_DEFAULT" in os.environ:
            settings['is_default'] = os.environ[f"{base_key}_IS_DEFAULT"].lower() == 'true'

        return settings

    def get_connection(self, name: str) -> Optional[DatabaseRepository]:
        """
        Get an existing connection.

        Args:
            name: Connection name

        Returns:
            DatabaseRepository instance or None
        """
        return self._connections.get(name)

    def get_default_connection(self, database_type: DatabaseType) -> Optional[DatabaseRepository]:
        """
        Get the default connection for a database type.

        Args:
            database_type: Type of database

        Returns:
            Default DatabaseRepository instance or None
        """
        for name, config in self._configurations.items():
            if (config['type'] == database_type and
                config['config'].get('is_default', False)):
                return self._connections.get(name)

        # Return first connection of type if no default
        for name, config in self._configurations.items():
            if config['type'] == database_type:
                return self._connections.get(name)

        return None

    def list_connections(self) -> Dict[str, Dict[str, Any]]:
        """
        List all connections.

        Returns:
            Dictionary of connection information
        """
        return {
            name: {
                'type': config['type'].value,
                'is_default': config['config'].get('is_default', False),
                'read_only': config['config'].get('read_only', True),
                'connected': name in self._connections
            }
            for name, config in self._configurations.items()
        }

    async def close_all(self):
        """Close all database connections."""
        for name, connection in self._connections.items():
            try:
                await connection.disconnect()
                logger.info(f"Closed connection: {name}")
            except Exception as e:
                logger.error(f"Error closing connection {name}: {e}")

        self._connections.clear()

    def _detect_database_type(self, connection_string: str) -> DatabaseType:
        """
        Detect database type from connection string.

        Args:
            connection_string: Database connection string

        Returns:
            Detected database type

        Raises:
            ValueError: If type cannot be detected
        """
        if connection_string.startswith('mysql://'):
            return DatabaseType.MYSQL
        elif connection_string.startswith('mongodb://'):
            return DatabaseType.MONGODB
        elif connection_string.startswith('mongodb+srv://'):
            return DatabaseType.MONGODB
        else:
            raise ValueError(f"Cannot detect database type from: {connection_string}")

    def _parse_connection_string(self,
                                connection_string: str,
                                database_type: DatabaseType) -> Dict[str, Any]:
        """
        Parse connection string into configuration.

        Args:
            connection_string: Database connection string
            database_type: Type of database

        Returns:
            Configuration dictionary
        """
        parsed = urlparse(connection_string)
        config = {}

        if database_type == DatabaseType.MYSQL:
            config['host'] = parsed.hostname or 'localhost'
            config['port'] = parsed.port or 3306
            config['username'] = parsed.username or ''
            config['password'] = parsed.password or ''
            config['database'] = parsed.path.lstrip('/') if parsed.path else ''

        elif database_type == DatabaseType.MONGODB:
            # MongoDB connection strings can be complex
            # Extract database from path if present
            if parsed.path and len(parsed.path) > 1:
                config['database'] = parsed.path.lstrip('/').split('?')[0]

        return config

    def __repr__(self) -> str:
        """String representation."""
        return (f"DatabaseConnectionFactory("
                f"connections={len(self._connections)}, "
                f"types={list(set(c['type'].value for c in self._configurations.values()))}"
                f")")


# Singleton instance
_factory_instance = None


def get_factory() -> DatabaseConnectionFactory:
    """
    Get singleton factory instance.

    Returns:
        DatabaseConnectionFactory singleton
    """
    global _factory_instance
    if _factory_instance is None:
        _factory_instance = DatabaseConnectionFactory()
    return _factory_instance