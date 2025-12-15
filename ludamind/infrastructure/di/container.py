"""
Dependency Injection Container

Comprehensive DI container for managing application dependencies
following Clean Architecture principles.
"""

import os
import logging
from typing import Dict, Any, Optional, Type
from functools import lru_cache
import asyncio
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)


class Environment(Enum):
    """Application environments."""
    DEVELOPMENT = "development"
    TESTING = "testing"
    STAGING = "staging"
    PRODUCTION = "production"


@dataclass
class ContainerConfig:
    """Container configuration."""
    environment: Environment
    config_file: Optional[str] = None
    auto_initialize: bool = True
    enable_monitoring: bool = True


class Container:
    """
    Dependency injection container for application components.

    This container manages the lifecycle of all application dependencies
    and provides factory methods for creating use cases with properly
    injected dependencies.
    """

    def __init__(self, config: Optional[ContainerConfig] = None):
        """
        Initialize the container.

        Args:
            config: Optional container configuration
        """
        self.config = config or self._get_default_config()
        self._instances = {}
        self._factories = {}
        self._is_initialized = False
        self._environment_config = self._load_environment_config()

        # Register factories
        self._register_factories()

        # Auto-initialize if configured
        if self.config.auto_initialize:
            asyncio.create_task(self.init_resources())

    def _get_default_config(self) -> ContainerConfig:
        """Get default container configuration."""
        env_str = os.getenv("ENVIRONMENT", "development")
        try:
            environment = Environment(env_str)
        except ValueError:
            environment = Environment.DEVELOPMENT

        return ContainerConfig(
            environment=environment,
            auto_initialize=True,
            enable_monitoring=environment == Environment.PRODUCTION
        )

    def _load_environment_config(self) -> Dict[str, Any]:
        """Load configuration from environment variables."""
        return {
            'mysql': {
                'host': os.getenv('MYSQL_HOST', '127.0.0.1'),
                'port': int(os.getenv('MYSQL_PORT', 3307)),
                'database': os.getenv('MYSQL_DATABASE', os.getenv('MYSQL_DB')),
                'username': os.getenv('MYSQL_USER', 'root'),
                'password': os.getenv('MYSQL_PASSWORD', ''),
                'pool_size': int(os.getenv('MYSQL_POOL_SIZE', 10)),
                'pool_recycle': int(os.getenv('MYSQL_POOL_RECYCLE', 3600)),
                'pool_timeout': int(os.getenv('MYSQL_POOL_TIMEOUT', 30)),
                'read_only': os.getenv('MYSQL_READ_ONLY', 'true').lower() == 'true'
            },
            'mongodb': {
                'connection_string': os.getenv('MONGO_LUDAFARMA_URL', 'mongodb://localhost:27017'),
                # Use environment variable or extract from URI dynamically at connection time
                'database_name': os.getenv('MONGO_DATABASE', None),  # Will be extracted from URI
                'max_pool_size': int(os.getenv('MONGO_POOL_SIZE', 100)),
                'min_pool_size': int(os.getenv('MONGO_MIN_POOL_SIZE', 10)),
                'max_idle_time_ms': int(os.getenv('MONGO_MAX_IDLE_TIME', 60000)),
                'read_only': os.getenv('MONGO_READ_ONLY', 'true').lower() == 'true'
            },
            'openai': {
                'api_key': os.getenv('OPENAI_API_KEY', ''),
                'model': os.getenv('OPENAI_MODEL', 'gpt-4o-mini'),
                'temperature': float(os.getenv('OPENAI_TEMPERATURE', 0.1)),
                'max_tokens': int(os.getenv('OPENAI_MAX_TOKENS', 2000)),
                'timeout': int(os.getenv('OPENAI_TIMEOUT', 30))
            },
            'redis': {
                'url': os.getenv('REDIS_URL', 'redis://localhost:6379'),
                'max_connections': int(os.getenv('REDIS_MAX_CONNECTIONS', 50)),
                'decode_responses': True
            },
            'application': {
                'name': os.getenv('APP_NAME', 'TrendsPro'),
                'version': os.getenv('APP_VERSION', '2.1.0'),
                'debug': os.getenv('DEBUG', 'false').lower() == 'true',
                'log_level': os.getenv('LOG_LEVEL', 'INFO'),
                'jwt_secret': os.getenv('JWT_SECRET_KEY', 'change-me-in-production'),
                'jwt_algorithm': os.getenv('JWT_ALGORITHM', 'HS256'),
                'jwt_expiration_minutes': int(os.getenv('JWT_EXPIRATION_MINUTES', 30))
            }
        }

    def _register_factories(self):
        """Register factory methods for creating instances."""
        # Repository factories
        self._factories['mysql_repository'] = self._create_mysql_repository
        self._factories['mongodb_repository'] = self._create_mongodb_repository
        self._factories['openai_llm_repository'] = self._create_openai_repository
        self._factories['chatgpt_llm_repository'] = self._create_chatgpt_repository
        self._factories['conversation_repository'] = self._create_conversation_repository
        self._factories['query_repository'] = self._create_query_repository
        self._factories['user_repository'] = self._create_user_repository

        # Service factories
        self._factories['database_connection_factory'] = self._create_db_connection_factory
        self._factories['prompt_manager'] = self._create_prompt_manager
        self._factories['query_router_service'] = self._create_query_router_service

        # Use case factories
        self._factories['execute_query_use_case'] = self._create_execute_query_use_case
        self._factories['streaming_query_use_case'] = self._create_streaming_query_use_case
        self._factories['conversation_manager_use_case'] = self._create_conversation_manager_use_case

    # Repository factory methods

    def _create_mysql_repository(self):
        """Create MySQL repository instance."""
        from ...infrastructure.repositories.mysql_repository import MySQLRepository

        config = self._environment_config['mysql']
        return MySQLRepository(
            host=config['host'],
            port=config['port'],
            database=config['database'],
            username=config['username'],
            password=config['password'],
            pool_size=config['pool_size'],
            pool_recycle=config['pool_recycle'],
            pool_timeout=config['pool_timeout'],
            read_only=config['read_only']
        )

    def _create_mongodb_repository(self):
        """Create MongoDB repository instance."""
        from ...infrastructure.repositories.mongodb_repository import MongoDBRepository

        config = self._environment_config['mongodb']
        return MongoDBRepository(
            connection_string=config['connection_string'],
            database_name=config['database_name'],
            max_pool_size=config['max_pool_size'],
            min_pool_size=config['min_pool_size'],
            max_idle_time_ms=config['max_idle_time_ms'],
            read_only=config['read_only']
        )

    def _create_openai_repository(self):
        """Create OpenAI LLM repository instance."""
        from ...infrastructure.repositories.openai_llm_repository import OpenAILLMRepository

        config = self._environment_config['openai']
        if not config['api_key']:
            raise ValueError("OpenAI API key not configured")

        return OpenAILLMRepository(
            api_key=config['api_key'],
            model=config['model'],
            temperature=config['temperature'],
            max_tokens=config['max_tokens'],
            timeout=config['timeout']
        )

    def _create_chatgpt_repository(self):
        """Create ChatGPT LLM repository instance."""
        from ...infrastructure.repositories.chatgpt_llm_repository import ChatGPTLLMRepository

        config = self._environment_config['openai']
        if not config['api_key']:
            raise ValueError("OpenAI API key not configured for ChatGPT")

        return ChatGPTLLMRepository(
            api_key=config['api_key'],
            model='gpt-4',  # ChatGPT uses GPT-4
            temperature=config['temperature'],
            max_tokens=config['max_tokens'],
            timeout=config['timeout']
        )

    def _create_conversation_repository(self):
        """Create conversation repository instance."""
        # For now, we'll use MongoDB for conversation storage
        # In production, this could be a separate database
        mongodb_repo = self.mongodb_repository()

        # Create a wrapper that implements ConversationRepository
        from ...infrastructure.repositories.conversation_repository import MongoConversationRepository

        return MongoConversationRepository(
            mongodb_client=mongodb_repo,
            collection_name='conversations'
        )

    def _create_query_repository(self):
        """Create query repository instance."""
        # Use MySQL for query history
        mysql_repo = self.mysql_repository()

        from ...infrastructure.repositories.query_repository import MySQLQueryRepository

        return MySQLQueryRepository(
            mysql_client=mysql_repo,
            table_name='query_history'
        )

    def _create_user_repository(self):
        """Create user repository instance."""
        # Use MongoDB for user management
        mongodb_repo = self.mongodb_repository()

        from ...infrastructure.repositories.user_repository import MongoUserRepository

        return MongoUserRepository(
            mongodb_client=mongodb_repo,
            collection_name='users'
        )

    # Service factory methods

    def _create_db_connection_factory(self):
        """Create database connection factory."""
        from ...infrastructure.services.database_connection_factory import DatabaseConnectionFactory

        return DatabaseConnectionFactory()

    def _create_prompt_manager(self):
        """Create prompt manager service."""
        from ...infrastructure.services.prompt_manager import PromptManager

        return PromptManager()

    def _create_query_router_service(self):
        """Create query router service."""
        from ...domain.services.query_router import QueryRouterService, RoutingStrategy

        strategy = RoutingStrategy.HYBRID  # Use hybrid strategy by default

        return QueryRouterService(
            routing_strategy=strategy,
            confidence_threshold=0.6
        )

    # Use case factory methods

    def _create_execute_query_use_case(self):
        """Create execute query use case."""
        from ...domain.use_cases.execute_query import ExecuteQueryUseCase

        return ExecuteQueryUseCase(
            query_repository=self.query_repository(),
            mysql_repository=self.mysql_repository(),
            mongodb_repository=self.mongodb_repository(),
            llm_repository=self.openai_llm_repository(),
            query_router=self.query_router_service(),
            prompt_manager=self.prompt_manager()
        )

    def _create_streaming_query_use_case(self):
        """Create streaming query use case."""
        from ...domain.use_cases.streaming_query import StreamingQueryUseCase

        return StreamingQueryUseCase(
            query_repository=self.query_repository(),
            mysql_repository=self.mysql_repository(),
            mongodb_repository=self.mongodb_repository(),
            llm_repository=self.openai_llm_repository(),
            query_router=self.query_router_service(),
            prompt_manager=self.prompt_manager()
        )

    def _create_conversation_manager_use_case(self):
        """Create conversation manager use case."""
        from ...domain.use_cases.conversation_manager import ConversationManagerUseCase

        return ConversationManagerUseCase(
            conversation_repository=self.conversation_repository(),
            llm_repository=self.openai_llm_repository(),
            prompt_manager=self.prompt_manager()
        )

    # Public accessor methods with caching

    @lru_cache(maxsize=1)
    def mysql_repository(self):
        """Get MySQL repository instance (cached)."""
        if 'mysql_repository' not in self._instances:
            self._instances['mysql_repository'] = self._factories['mysql_repository']()
        return self._instances['mysql_repository']

    @lru_cache(maxsize=1)
    def mongodb_repository(self):
        """Get MongoDB repository instance (cached)."""
        if 'mongodb_repository' not in self._instances:
            self._instances['mongodb_repository'] = self._factories['mongodb_repository']()
        return self._instances['mongodb_repository']

    @lru_cache(maxsize=1)
    def openai_llm_repository(self):
        """Get OpenAI LLM repository instance (cached)."""
        if 'openai_llm_repository' not in self._instances:
            self._instances['openai_llm_repository'] = self._factories['openai_llm_repository']()
        return self._instances['openai_llm_repository']

    @lru_cache(maxsize=1)
    def chatgpt_llm_repository(self):
        """Get ChatGPT LLM repository instance (cached)."""
        if 'chatgpt_llm_repository' not in self._instances:
            self._instances['chatgpt_llm_repository'] = self._factories['chatgpt_llm_repository']()
        return self._instances['chatgpt_llm_repository']

    @lru_cache(maxsize=1)
    def conversation_repository(self):
        """Get conversation repository instance (cached)."""
        if 'conversation_repository' not in self._instances:
            self._instances['conversation_repository'] = self._factories['conversation_repository']()
        return self._instances['conversation_repository']

    @lru_cache(maxsize=1)
    def query_repository(self):
        """Get query repository instance (cached)."""
        if 'query_repository' not in self._instances:
            self._instances['query_repository'] = self._factories['query_repository']()
        return self._instances['query_repository']

    @lru_cache(maxsize=1)
    def user_repository(self):
        """Get user repository instance (cached)."""
        if 'user_repository' not in self._instances:
            self._instances['user_repository'] = self._factories['user_repository']()
        return self._instances['user_repository']

    @lru_cache(maxsize=1)
    def database_connection_factory(self):
        """Get database connection factory instance (cached)."""
        if 'database_connection_factory' not in self._instances:
            self._instances['database_connection_factory'] = self._factories['database_connection_factory']()
        return self._instances['database_connection_factory']

    @lru_cache(maxsize=1)
    def prompt_manager(self):
        """Get prompt manager instance (cached)."""
        if 'prompt_manager' not in self._instances:
            self._instances['prompt_manager'] = self._factories['prompt_manager']()
        return self._instances['prompt_manager']

    @lru_cache(maxsize=1)
    def query_router_service(self):
        """Get query router service instance (cached)."""
        if 'query_router_service' not in self._instances:
            self._instances['query_router_service'] = self._factories['query_router_service']()
        return self._instances['query_router_service']

    # Use case accessors (not cached as they may have different configurations)

    def execute_query_use_case(self, use_chatgpt: bool = False):
        """
        Get execute query use case.

        Args:
            use_chatgpt: Whether to use ChatGPT instead of OpenAI

        Returns:
            ExecuteQueryUseCase instance
        """
        from ...domain.use_cases.execute_query import ExecuteQueryUseCase

        llm_repo = self.chatgpt_llm_repository() if use_chatgpt else self.openai_llm_repository()

        return ExecuteQueryUseCase(
            query_repository=self.query_repository(),
            mysql_repository=self.mysql_repository(),
            mongodb_repository=self.mongodb_repository(),
            llm_repository=llm_repo,
            query_router=self.query_router_service(),
            prompt_manager=self.prompt_manager()
        )

    def streaming_query_use_case(self, use_chatgpt: bool = False):
        """
        Get streaming query use case.

        Args:
            use_chatgpt: Whether to use ChatGPT instead of OpenAI

        Returns:
            StreamingQueryUseCase instance
        """
        from ...domain.use_cases.streaming_query import StreamingQueryUseCase

        llm_repo = self.chatgpt_llm_repository() if use_chatgpt else self.openai_llm_repository()

        return StreamingQueryUseCase(
            query_repository=self.query_repository(),
            mysql_repository=self.mysql_repository(),
            mongodb_repository=self.mongodb_repository(),
            llm_repository=llm_repo,
            query_router=self.query_router_service(),
            prompt_manager=self.prompt_manager()
        )

    def conversation_manager_use_case(self):
        """Get conversation manager use case."""
        return self._factories['conversation_manager_use_case']()

    # Lifecycle management

    async def init_resources(self):
        """
        Initialize all resources.

        This method should be called on application startup to
        initialize connections and verify configurations.
        """
        if self._is_initialized:
            return

        logger.info(f"Initializing container resources for environment: {self.config.environment.value}")

        try:
            # Initialize database connections
            mysql_repo = self.mysql_repository()
            if hasattr(mysql_repo, 'connect'):
                await mysql_repo.connect()
                logger.info("MySQL repository connected")

            mongodb_repo = self.mongodb_repository()
            if hasattr(mongodb_repo, 'connect'):
                await mongodb_repo.connect()
                logger.info("MongoDB repository connected")

            # Test connections
            if hasattr(mysql_repo, 'test_connection'):
                mysql_ok = await mysql_repo.test_connection()
                if not mysql_ok:
                    logger.warning("MySQL connection test failed")

            if hasattr(mongodb_repo, 'test_connection'):
                mongodb_ok = await mongodb_repo.test_connection()
                if not mongodb_ok:
                    logger.warning("MongoDB connection test failed")

            # Initialize other resources if needed
            # ...

            self._is_initialized = True
            logger.info("Container resources initialized successfully")

        except Exception as e:
            logger.error(f"Failed to initialize container resources: {e}")
            raise

    async def cleanup_resources(self):
        """
        Clean up all resources.

        This method should be called on application shutdown to
        properly close connections and clean up resources.
        """
        logger.info("Cleaning up container resources")

        try:
            # Close database connections
            if 'mysql_repository' in self._instances:
                mysql_repo = self._instances['mysql_repository']
                if hasattr(mysql_repo, 'disconnect'):
                    await mysql_repo.disconnect()
                    logger.info("MySQL repository disconnected")

            if 'mongodb_repository' in self._instances:
                mongodb_repo = self._instances['mongodb_repository']
                if hasattr(mongodb_repo, 'disconnect'):
                    await mongodb_repo.disconnect()
                    logger.info("MongoDB repository disconnected")

            # Clear caches
            self.mysql_repository.cache_clear()
            self.mongodb_repository.cache_clear()
            self.openai_llm_repository.cache_clear()
            self.chatgpt_llm_repository.cache_clear()
            self.conversation_repository.cache_clear()
            self.query_repository.cache_clear()
            self.user_repository.cache_clear()

            # Clear instances
            self._instances.clear()
            self._is_initialized = False

            logger.info("Container resources cleaned up successfully")

        except Exception as e:
            logger.error(f"Error during container cleanup: {e}")

    # Context manager support

    async def __aenter__(self):
        """Async context manager entry."""
        await self.init_resources()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.cleanup_resources()

    # Testing helpers

    def get_test_container(self) -> 'Container':
        """
        Get a container configured for testing.

        Returns:
            Container configured for testing environment
        """
        test_config = ContainerConfig(
            environment=Environment.TESTING,
            auto_initialize=False,
            enable_monitoring=False
        )
        return Container(config=test_config)

    def override_instance(self, name: str, instance: Any):
        """
        Override an instance in the container (for testing).

        Args:
            name: Instance name
            instance: Instance to use
        """
        self._instances[name] = instance

    def reset(self):
        """Reset the container to initial state."""
        self._instances.clear()
        self._is_initialized = False

        # Clear all caches
        for attr_name in dir(self):
            attr = getattr(self, attr_name)
            if hasattr(attr, 'cache_clear'):
                attr.cache_clear()


# Singleton instance management

_container_instance: Optional[Container] = None


def get_container(config: Optional[ContainerConfig] = None) -> Container:
    """
    Get the singleton container instance.

    Args:
        config: Optional container configuration

    Returns:
        Container instance
    """
    global _container_instance

    if _container_instance is None:
        _container_instance = Container(config)

    return _container_instance


def reset_container():
    """Reset the singleton container instance."""
    global _container_instance

    if _container_instance:
        asyncio.run(_container_instance.cleanup_resources())
        _container_instance = None