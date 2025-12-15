"""
Health Check Module

Provides health checking capabilities for the application.
"""

import asyncio
import logging
from dataclasses import dataclass
from datetime import datetime
from typing import List, Dict, Any, Optional
from enum import Enum

logger = logging.getLogger(__name__)


class HealthStatus(Enum):
    """Health status enumeration"""
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"


@dataclass
class HealthCheckResult:
    """Result of a health check"""
    component: str
    status: HealthStatus
    healthy: bool
    message: str
    latency_ms: float
    timestamp: datetime
    details: Optional[Dict[str, Any]] = None

    @property
    def as_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            'component': self.component,
            'status': self.status.value,
            'healthy': self.healthy,
            'message': self.message,
            'latency_ms': self.latency_ms,
            'timestamp': self.timestamp.isoformat(),
            'details': self.details
        }


class HealthChecker:
    """Health checker for application components"""

    def __init__(self, container):
        """
        Initialize health checker

        Args:
            container: DI container for accessing components
        """
        self.container = container

    async def check_all(self) -> List[HealthCheckResult]:
        """
        Run all health checks

        Returns:
            List of health check results
        """
        checks = [
            self.check_mysql(),
            self.check_mongodb(),
            self.check_openai(),
            self.check_redis()
        ]

        results = await asyncio.gather(*checks, return_exceptions=True)

        # Convert exceptions to unhealthy results
        final_results = []
        for result in results:
            if isinstance(result, Exception):
                final_results.append(HealthCheckResult(
                    component="unknown",
                    status=HealthStatus.UNHEALTHY,
                    healthy=False,
                    message=str(result),
                    latency_ms=0,
                    timestamp=datetime.utcnow()
                ))
            else:
                final_results.append(result)

        return final_results

    async def check_mysql(self) -> HealthCheckResult:
        """Check MySQL database health"""
        component = "mysql"
        start_time = datetime.utcnow()

        try:
            # Get MySQL repository
            mysql_repo = await self.container.get_mysql_repository()

            # Execute simple query
            result = await mysql_repo.execute_query("SELECT 1 as health_check")

            latency_ms = (datetime.utcnow() - start_time).total_seconds() * 1000

            if result and result[0].get('health_check') == 1:
                return HealthCheckResult(
                    component=component,
                    status=HealthStatus.HEALTHY,
                    healthy=True,
                    message="MySQL is healthy",
                    latency_ms=latency_ms,
                    timestamp=datetime.utcnow(),
                    details={'database': 'trends'}
                )
            else:
                return HealthCheckResult(
                    component=component,
                    status=HealthStatus.UNHEALTHY,
                    healthy=False,
                    message="MySQL query failed",
                    latency_ms=latency_ms,
                    timestamp=datetime.utcnow()
                )

        except Exception as e:
            latency_ms = (datetime.utcnow() - start_time).total_seconds() * 1000
            return HealthCheckResult(
                component=component,
                status=HealthStatus.UNHEALTHY,
                healthy=False,
                message=f"MySQL error: {str(e)}",
                latency_ms=latency_ms,
                timestamp=datetime.utcnow()
            )

    async def check_mongodb(self) -> HealthCheckResult:
        """Check MongoDB database health"""
        component = "mongodb"
        start_time = datetime.utcnow()

        try:
            # Get MongoDB repository
            mongo_repo = await self.container.get_mongodb_repository()

            # Execute ping command
            result = await mongo_repo.ping()

            latency_ms = (datetime.utcnow() - start_time).total_seconds() * 1000

            if result:
                return HealthCheckResult(
                    component=component,
                    status=HealthStatus.HEALTHY,
                    healthy=True,
                    message="MongoDB is healthy",
                    latency_ms=latency_ms,
                    timestamp=datetime.utcnow(),
                    details={'database': 'ludafarma'}
                )
            else:
                return HealthCheckResult(
                    component=component,
                    status=HealthStatus.UNHEALTHY,
                    healthy=False,
                    message="MongoDB ping failed",
                    latency_ms=latency_ms,
                    timestamp=datetime.utcnow()
                )

        except Exception as e:
            latency_ms = (datetime.utcnow() - start_time).total_seconds() * 1000
            return HealthCheckResult(
                component=component,
                status=HealthStatus.UNHEALTHY,
                healthy=False,
                message=f"MongoDB error: {str(e)}",
                latency_ms=latency_ms,
                timestamp=datetime.utcnow()
            )

    async def check_openai(self) -> HealthCheckResult:
        """Check OpenAI API health"""
        component = "openai"
        start_time = datetime.utcnow()

        try:
            # Get OpenAI repository
            openai_repo = await self.container.get_openai_repository()

            # Check API key is configured
            if not openai_repo.api_key:
                return HealthCheckResult(
                    component=component,
                    status=HealthStatus.UNHEALTHY,
                    healthy=False,
                    message="OpenAI API key not configured",
                    latency_ms=0,
                    timestamp=datetime.utcnow()
                )

            # Try to list models (lightweight API call)
            models = await openai_repo.list_models()

            latency_ms = (datetime.utcnow() - start_time).total_seconds() * 1000

            if models:
                return HealthCheckResult(
                    component=component,
                    status=HealthStatus.HEALTHY,
                    healthy=True,
                    message="OpenAI API is healthy",
                    latency_ms=latency_ms,
                    timestamp=datetime.utcnow(),
                    details={'model': openai_repo.model}
                )
            else:
                return HealthCheckResult(
                    component=component,
                    status=HealthStatus.DEGRADED,
                    healthy=True,
                    message="OpenAI API responded but no models found",
                    latency_ms=latency_ms,
                    timestamp=datetime.utcnow()
                )

        except Exception as e:
            latency_ms = (datetime.utcnow() - start_time).total_seconds() * 1000
            return HealthCheckResult(
                component=component,
                status=HealthStatus.UNHEALTHY,
                healthy=False,
                message=f"OpenAI error: {str(e)}",
                latency_ms=latency_ms,
                timestamp=datetime.utcnow()
            )

    async def check_redis(self) -> HealthCheckResult:
        """Check Redis cache health"""
        component = "redis"
        start_time = datetime.utcnow()

        try:
            # Redis is optional
            if not self.container.config.redis_url:
                return HealthCheckResult(
                    component=component,
                    status=HealthStatus.HEALTHY,
                    healthy=True,
                    message="Redis not configured (optional)",
                    latency_ms=0,
                    timestamp=datetime.utcnow()
                )

            # Get Redis client
            redis_client = await self.container.get_redis_client()

            # Ping Redis
            if await redis_client.ping():
                latency_ms = (datetime.utcnow() - start_time).total_seconds() * 1000
                return HealthCheckResult(
                    component=component,
                    status=HealthStatus.HEALTHY,
                    healthy=True,
                    message="Redis is healthy",
                    latency_ms=latency_ms,
                    timestamp=datetime.utcnow()
                )
            else:
                latency_ms = (datetime.utcnow() - start_time).total_seconds() * 1000
                return HealthCheckResult(
                    component=component,
                    status=HealthStatus.UNHEALTHY,
                    healthy=False,
                    message="Redis ping failed",
                    latency_ms=latency_ms,
                    timestamp=datetime.utcnow()
                )

        except Exception as e:
            latency_ms = (datetime.utcnow() - start_time).total_seconds() * 1000

            # If Redis is configured but not available, mark as degraded
            if self.container.config.redis_url:
                return HealthCheckResult(
                    component=component,
                    status=HealthStatus.DEGRADED,
                    healthy=True,  # App can run without cache
                    message=f"Redis unavailable (cache disabled): {str(e)}",
                    latency_ms=latency_ms,
                    timestamp=datetime.utcnow()
                )
            else:
                return HealthCheckResult(
                    component=component,
                    status=HealthStatus.HEALTHY,
                    healthy=True,
                    message="Redis not configured",
                    latency_ms=latency_ms,
                    timestamp=datetime.utcnow()
                )

    async def get_system_health(self) -> Dict[str, Any]:
        """
        Get overall system health status

        Returns:
            System health summary
        """
        results = await self.check_all()

        # Determine overall status
        unhealthy = [r for r in results if not r.healthy]
        degraded = [r for r in results if r.status == HealthStatus.DEGRADED]

        if unhealthy:
            overall_status = HealthStatus.UNHEALTHY
        elif degraded:
            overall_status = HealthStatus.DEGRADED
        else:
            overall_status = HealthStatus.HEALTHY

        return {
            'status': overall_status.value,
            'healthy': len(unhealthy) == 0,
            'timestamp': datetime.utcnow().isoformat(),
            'checks': [r.as_dict for r in results],
            'summary': {
                'total': len(results),
                'healthy': sum(1 for r in results if r.status == HealthStatus.HEALTHY),
                'degraded': len(degraded),
                'unhealthy': len(unhealthy)
            }
        }

    async def get_readiness(self) -> Dict[str, Any]:
        """
        Get readiness status (for Kubernetes readiness probe)

        Returns:
            Readiness status
        """
        health = await self.get_system_health()

        # Ready if no critical components are unhealthy
        critical_components = ['mysql', 'mongodb', 'openai']
        critical_unhealthy = [
            check for check in health['checks']
            if check['component'] in critical_components and not check['healthy']
        ]

        ready = len(critical_unhealthy) == 0

        return {
            'ready': ready,
            'status': 'ready' if ready else 'not ready',
            'timestamp': health['timestamp'],
            'issues': [
                f"{check['component']}: {check['message']}"
                for check in critical_unhealthy
            ] if critical_unhealthy else []
        }

    async def get_liveness(self) -> Dict[str, Any]:
        """
        Get liveness status (for Kubernetes liveness probe)

        Returns:
            Liveness status
        """
        # Application is alive if this method executes
        return {
            'alive': True,
            'status': 'alive',
            'timestamp': datetime.utcnow().isoformat()
        }