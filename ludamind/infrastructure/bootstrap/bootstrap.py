"""
Bootstrap Module

Handles application initialization, configuration, and startup.
"""

import asyncio
import logging
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Optional, Dict, Any, List
from datetime import datetime

from ..di.container import Container, ContainerConfig
from .environment import load_environment, validate_environment
from .logging import setup_logging
from .health_check import HealthChecker, HealthCheckResult

logger = logging.getLogger(__name__)


@dataclass
class BootstrapConfig:
    """Bootstrap configuration"""

    # Application
    app_name: str = "TrendsPro"
    app_version: str = "3.0.0"
    environment: str = "development"

    # Paths
    root_path: Path = Path(__file__).parent.parent.parent
    config_path: Optional[Path] = None
    log_path: Optional[Path] = None

    # Logging
    log_level: str = "INFO"
    log_format: str = "json"
    enable_file_logging: bool = True

    # Features
    enable_health_checks: bool = True
    enable_migrations: bool = True
    enable_cache_warming: bool = False
    enable_metrics: bool = True

    # Timeouts
    startup_timeout: int = 30  # seconds
    shutdown_timeout: int = 10  # seconds

    # Container
    container_config: Optional[ContainerConfig] = None


class Bootstrap:
    """
    Application bootstrap manager

    Handles initialization sequence:
    1. Load environment variables
    2. Setup logging
    3. Validate configuration
    4. Initialize DI container
    5. Run health checks
    6. Run migrations
    7. Warm caches
    8. Start application
    """

    def __init__(self, config: Optional[BootstrapConfig] = None):
        """Initialize bootstrap manager"""
        self.config = config or BootstrapConfig()
        self.container: Optional[Container] = None
        self.health_checker: Optional[HealthChecker] = None
        self.start_time: Optional[datetime] = None
        self._is_initialized = False
        self._is_running = False

    async def initialize(self) -> None:
        """
        Initialize application

        Raises:
            RuntimeError: If initialization fails
        """
        if self._is_initialized:
            logger.warning("Application already initialized")
            return

        try:
            logger.info(f"Starting {self.config.app_name} v{self.config.app_version}")
            logger.info(f"Environment: {self.config.environment}")
            self.start_time = datetime.utcnow()

            # Step 1: Load environment
            logger.info("Loading environment variables...")
            env_vars = await self._load_environment()

            # Step 2: Setup logging
            logger.info("Setting up logging...")
            self._setup_logging()

            # Step 3: Validate configuration
            logger.info("Validating configuration...")
            await self._validate_configuration(env_vars)

            # Step 4: Initialize container
            logger.info("Initializing dependency injection container...")
            await self._initialize_container(env_vars)

            # Step 5: Run health checks
            if self.config.enable_health_checks:
                logger.info("Running health checks...")
                health_results = await self._run_health_checks()
                self._log_health_results(health_results)

            # Step 6: Run migrations
            if self.config.enable_migrations:
                logger.info("Running database migrations...")
                await self._run_migrations()

            # Step 7: Warm caches
            if self.config.enable_cache_warming:
                logger.info("Warming caches...")
                await self._warm_caches()

            # Step 8: Initialize metrics
            if self.config.enable_metrics:
                logger.info("Initializing metrics...")
                await self._initialize_metrics()

            self._is_initialized = True
            elapsed = (datetime.utcnow() - self.start_time).total_seconds()
            logger.info(f"Application initialized successfully in {elapsed:.2f} seconds")

        except Exception as e:
            logger.error(f"Failed to initialize application: {str(e)}", exc_info=True)
            await self.cleanup()
            raise RuntimeError(f"Bootstrap failed: {str(e)}") from e

    async def start(self) -> None:
        """
        Start application

        Raises:
            RuntimeError: If application not initialized or start fails
        """
        if not self._is_initialized:
            raise RuntimeError("Application not initialized. Call initialize() first.")

        if self._is_running:
            logger.warning("Application already running")
            return

        try:
            logger.info("Starting application...")

            # Start background tasks
            await self._start_background_tasks()

            # Mark as running
            self._is_running = True
            logger.info("Application started successfully")

        except Exception as e:
            logger.error(f"Failed to start application: {str(e)}", exc_info=True)
            raise RuntimeError(f"Start failed: {str(e)}") from e

    async def stop(self) -> None:
        """Stop application gracefully"""
        if not self._is_running:
            logger.warning("Application not running")
            return

        try:
            logger.info("Stopping application...")

            # Stop background tasks
            await self._stop_background_tasks()

            # Mark as stopped
            self._is_running = False
            logger.info("Application stopped successfully")

        except Exception as e:
            logger.error(f"Error during stop: {str(e)}", exc_info=True)

    async def cleanup(self) -> None:
        """Cleanup resources"""
        try:
            logger.info("Cleaning up resources...")

            # Stop if running
            if self._is_running:
                await self.stop()

            # Cleanup container
            if self.container:
                await self.container.cleanup()
                self.container = None

            # Reset state
            self._is_initialized = False
            logger.info("Cleanup completed")

        except Exception as e:
            logger.error(f"Error during cleanup: {str(e)}", exc_info=True)

    async def _load_environment(self) -> Dict[str, Any]:
        """Load environment variables"""
        env_path = self.config.root_path / ".env"

        if self.config.environment == "testing":
            env_path = self.config.root_path / ".env.test"
        elif self.config.environment == "production":
            env_path = self.config.root_path / ".env.production"

        return load_environment(env_path)

    def _setup_logging(self) -> None:
        """Setup logging configuration"""
        log_config = {
            'level': self.config.log_level,
            'format': self.config.log_format,
            'app_name': self.config.app_name,
            'environment': self.config.environment
        }

        if self.config.enable_file_logging and self.config.log_path:
            log_config['log_file'] = self.config.log_path / f"{self.config.app_name.lower()}.log"

        setup_logging(**log_config)

    async def _validate_configuration(self, env_vars: Dict[str, Any]) -> None:
        """Validate configuration"""
        required_vars = [
            'DB_TRENDS_URL',
            'MONGO_LUDAFARMA_URL',
            'OPENAI_API_KEY'
        ]

        # Check for production environment
        if self.config.environment == "production":
            required_vars.extend([
                'SECRET_KEY',
                'JWT_SECRET',
                'REDIS_URL'
            ])

        errors = validate_environment(env_vars, required_vars)
        if errors:
            raise RuntimeError(f"Configuration validation failed: {', '.join(errors)}")

    async def _initialize_container(self, env_vars: Dict[str, Any]) -> None:
        """Initialize DI container"""
        # Create container config
        container_config = self.config.container_config or ContainerConfig(
            environment=self.config.environment,
            mysql_urls={
                'trends': env_vars.get('DB_TRENDS_URL')
            },
            mongodb_urls={
                'ludafarma': env_vars.get('MONGO_LUDAFARMA_URL')
            },
            openai_config={
                'api_key': env_vars.get('OPENAI_API_KEY'),
                'model': env_vars.get('OPENAI_MODEL', 'gpt-4o-mini'),
                'temperature': float(env_vars.get('OPENAI_TEMPERATURE', '0.1')),
                'max_tokens': int(env_vars.get('OPENAI_MAX_TOKENS', '2000'))
            },
            chatgpt_config={
                'api_key': env_vars.get('CHATGPT_API_KEY', env_vars.get('OPENAI_API_KEY')),
                'model': env_vars.get('CHATGPT_MODEL', 'gpt-4'),
                'system_prompt_path': self.config.root_path / 'docs' / 'SYSTEM_PROMPT_EQUIPO_NEGOCIO.txt'
            },
            redis_url=env_vars.get('REDIS_URL'),
            jwt_secret=env_vars.get('JWT_SECRET', 'dev-secret'),
            enable_cache=env_vars.get('ENABLE_CACHE', 'true').lower() == 'true',
            cache_ttl=int(env_vars.get('CACHE_TTL', '3600')),
            max_connections=int(env_vars.get('MAX_CONNECTIONS', '10'))
        )

        # Create and initialize container
        self.container = Container(container_config)
        await self.container.initialize()

        # Create health checker
        self.health_checker = HealthChecker(self.container)

    async def _run_health_checks(self) -> List[HealthCheckResult]:
        """Run health checks"""
        if not self.health_checker:
            return []

        return await self.health_checker.check_all()

    def _log_health_results(self, results: List[HealthCheckResult]) -> None:
        """Log health check results"""
        for result in results:
            if result.healthy:
                logger.info(f"✓ {result.component}: {result.message}")
            else:
                logger.error(f"✗ {result.component}: {result.message}")
                if result.details:
                    logger.error(f"  Details: {result.details}")

    async def _run_migrations(self) -> None:
        """Run database migrations"""
        # TODO: Implement when migration system is ready
        logger.info("Skipping migrations (not implemented yet)")

    async def _warm_caches(self) -> None:
        """Warm up caches with common data"""
        try:
            # Get repositories from container
            query_repo = await self.container.get_query_repository()

            # Warm common queries
            common_queries = [
                "¿Cuáles son los 10 productos más vendidos?",
                "¿Cuántas farmacias activas tenemos?",
                "Productos en grupo de riesgo 3"
            ]

            for query_text in common_queries:
                try:
                    # This would execute and cache the query
                    logger.debug(f"Warming cache for: {query_text}")
                except Exception as e:
                    logger.warning(f"Failed to warm cache for query: {e}")

        except Exception as e:
            logger.error(f"Cache warming failed: {str(e)}")

    async def _initialize_metrics(self) -> None:
        """Initialize metrics collection"""
        # TODO: Implement Prometheus metrics
        logger.info("Metrics initialized (placeholder)")

    async def _start_background_tasks(self) -> None:
        """Start background tasks"""
        # TODO: Implement background task management
        logger.info("Background tasks started (placeholder)")

    async def _stop_background_tasks(self) -> None:
        """Stop background tasks"""
        # TODO: Implement background task management
        logger.info("Background tasks stopped (placeholder)")

    # Context manager support
    async def __aenter__(self):
        """Enter context manager"""
        await self.initialize()
        await self.start()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Exit context manager"""
        await self.cleanup()

    # Factory methods for FastAPI integration
    async def get_app(self):
        """
        Get FastAPI application instance

        Returns:
            FastAPI: Configured FastAPI application
        """
        if not self._is_initialized:
            await self.initialize()

        from ...presentation.api.main import create_app

        return create_app(self.container)

    async def get_container(self) -> Container:
        """
        Get DI container

        Returns:
            Container: Initialized container
        """
        if not self._is_initialized:
            await self.initialize()

        return self.container


# Singleton instance for global access
_bootstrap_instance: Optional[Bootstrap] = None


def get_bootstrap(config: Optional[BootstrapConfig] = None) -> Bootstrap:
    """
    Get bootstrap singleton instance

    Args:
        config: Optional bootstrap configuration

    Returns:
        Bootstrap: Bootstrap instance
    """
    global _bootstrap_instance

    if _bootstrap_instance is None:
        _bootstrap_instance = Bootstrap(config)

    return _bootstrap_instance


async def run_application(config: Optional[BootstrapConfig] = None):
    """
    Run application with bootstrap

    Args:
        config: Optional bootstrap configuration
    """
    bootstrap = get_bootstrap(config)

    try:
        async with bootstrap:
            # Get FastAPI app
            app = await bootstrap.get_app()

            # Run with uvicorn
            import uvicorn

            config = uvicorn.Config(
                app=app,
                host="0.0.0.0",
                port=8000,
                log_level=bootstrap.config.log_level.lower()
            )

            server = uvicorn.Server(config)
            await server.serve()

    except KeyboardInterrupt:
        logger.info("Received interrupt signal")
    except Exception as e:
        logger.error(f"Application crashed: {str(e)}", exc_info=True)
        raise
    finally:
        logger.info("Application shutdown complete")