"""
Health Router

API endpoints for health checks and monitoring.
"""

from fastapi import APIRouter, Depends, HTTPException
from typing import Dict, Any
import asyncio
import psutil
import time
from datetime import datetime, timedelta

from ..dependencies import get_container
from ..schemas.common_schemas import HealthCheckResponse, HealthStatus
from ....infrastructure.di.container import Container

router = APIRouter()

# Application start time for uptime calculation
APP_START_TIME = time.time()


@router.get("/health", response_model=HealthCheckResponse)
async def health_check(
    container: Container = Depends(get_container)
) -> HealthCheckResponse:
    """
    Health check endpoint.

    Performs comprehensive health check on all system components.

    Args:
        container: Dependency injection container

    Returns:
        HealthCheckResponse with overall health status

    Raises:
        HTTPException: On critical health check failures
    """
    checks = {}
    overall_status = HealthStatus.HEALTHY

    # Check database connections
    db_checks = await _check_databases(container)
    checks.update(db_checks)

    # Check cache
    cache_check = await _check_cache(container)
    checks["cache"] = cache_check

    # Check external services
    llm_check = await _check_llm_service(container)
    checks["llm_service"] = llm_check

    # Check system resources
    system_check = _check_system_resources()
    checks["system"] = system_check

    # Determine overall status
    for check_name, check_result in checks.items():
        if check_result["status"] == "unhealthy":
            overall_status = HealthStatus.UNHEALTHY
            break
        elif check_result["status"] == "degraded" and overall_status == HealthStatus.HEALTHY:
            overall_status = HealthStatus.DEGRADED

    # Calculate uptime
    uptime_seconds = int(time.time() - APP_START_TIME)

    return HealthCheckResponse(
        status=overall_status,
        version="2.1.0",
        timestamp=datetime.utcnow(),
        checks=checks,
        uptime_seconds=uptime_seconds
    )


@router.get("/health/live")
async def liveness_probe():
    """
    Kubernetes liveness probe.

    Simple endpoint to check if the application is alive.

    Returns:
        Simple status indicating the app is alive
    """
    return {"status": "alive", "timestamp": datetime.utcnow().isoformat()}


@router.get("/health/ready")
async def readiness_probe(
    container: Container = Depends(get_container)
):
    """
    Kubernetes readiness probe.

    Check if the application is ready to serve requests.

    Args:
        container: Dependency injection container

    Returns:
        Ready status if all critical services are available

    Raises:
        HTTPException: If the application is not ready
    """
    # Check critical services
    try:
        # Check MySQL connection
        mysql_repo = container.mysql_repository()
        mysql_connected = await mysql_repo.test_connection()

        if not mysql_connected:
            raise HTTPException(status_code=503, detail="MySQL not ready")

        # Check MongoDB connection
        mongodb_repo = container.mongodb_repository()
        mongodb_connected = await mongodb_repo.test_connection()

        if not mongodb_connected:
            raise HTTPException(status_code=503, detail="MongoDB not ready")

        return {
            "status": "ready",
            "timestamp": datetime.utcnow().isoformat()
        }

    except Exception as e:
        raise HTTPException(status_code=503, detail=f"Not ready: {str(e)}")


@router.get("/metrics")
async def metrics(
    container: Container = Depends(get_container)
):
    """
    Prometheus-compatible metrics endpoint.

    Expose application metrics in Prometheus format.

    Args:
        container: Dependency injection container

    Returns:
        Metrics in Prometheus text format
    """
    metrics_lines = []

    # Application info
    metrics_lines.append('# HELP trendspro_info Application information')
    metrics_lines.append('# TYPE trendspro_info gauge')
    metrics_lines.append('trendspro_info{version="2.1.0",environment="production"} 1')

    # Uptime
    uptime = int(time.time() - APP_START_TIME)
    metrics_lines.append('# HELP trendspro_uptime_seconds Application uptime in seconds')
    metrics_lines.append('# TYPE trendspro_uptime_seconds counter')
    metrics_lines.append(f'trendspro_uptime_seconds {uptime}')

    # System metrics
    cpu_percent = psutil.cpu_percent()
    memory = psutil.virtual_memory()

    metrics_lines.append('# HELP system_cpu_usage_percent CPU usage percentage')
    metrics_lines.append('# TYPE system_cpu_usage_percent gauge')
    metrics_lines.append(f'system_cpu_usage_percent {cpu_percent}')

    metrics_lines.append('# HELP system_memory_usage_percent Memory usage percentage')
    metrics_lines.append('# TYPE system_memory_usage_percent gauge')
    metrics_lines.append(f'system_memory_usage_percent {memory.percent}')

    metrics_lines.append('# HELP system_memory_available_bytes Available memory in bytes')
    metrics_lines.append('# TYPE system_memory_available_bytes gauge')
    metrics_lines.append(f'system_memory_available_bytes {memory.available}')

    # TODO: Add application-specific metrics (queries, cache hits, etc.)

    return "\n".join(metrics_lines)


@router.get("/status")
async def status(
    container: Container = Depends(get_container)
):
    """
    Detailed status endpoint.

    Provides detailed information about the application status.

    Args:
        container: Dependency injection container

    Returns:
        Detailed status information
    """
    # Get system information
    cpu_percent = psutil.cpu_percent(interval=1)
    memory = psutil.virtual_memory()
    disk = psutil.disk_usage('/')

    # Get process information
    process = psutil.Process()
    process_info = {
        "pid": process.pid,
        "cpu_percent": process.cpu_percent(),
        "memory_mb": process.memory_info().rss / 1024 / 1024,
        "threads": process.num_threads(),
        "open_files": len(process.open_files())
    }

    # Calculate uptime
    uptime_seconds = int(time.time() - APP_START_TIME)
    uptime_str = str(timedelta(seconds=uptime_seconds))

    return {
        "application": {
            "name": "TrendsPro API",
            "version": "2.1.0",
            "environment": "production",
            "uptime": uptime_str,
            "uptime_seconds": uptime_seconds
        },
        "system": {
            "cpu": {
                "count": psutil.cpu_count(),
                "percent": cpu_percent
            },
            "memory": {
                "total_mb": memory.total / 1024 / 1024,
                "available_mb": memory.available / 1024 / 1024,
                "percent": memory.percent
            },
            "disk": {
                "total_gb": disk.total / 1024 / 1024 / 1024,
                "free_gb": disk.free / 1024 / 1024 / 1024,
                "percent": disk.percent
            }
        },
        "process": process_info,
        "timestamp": datetime.utcnow().isoformat()
    }


# Helper functions for health checks

async def _check_databases(container: Container) -> Dict[str, Dict[str, Any]]:
    """Check database connections."""
    checks = {}

    # Check MySQL
    try:
        mysql_repo = container.mysql_repository()
        mysql_connected = await asyncio.wait_for(
            mysql_repo.test_connection(),
            timeout=5.0
        )

        checks["mysql"] = {
            "status": "healthy" if mysql_connected else "unhealthy",
            "response_time_ms": 0,  # TODO: Measure actual response time
            "details": {
                "connected": mysql_connected,
                "database": "trends_consolidado"
            }
        }
    except asyncio.TimeoutError:
        checks["mysql"] = {
            "status": "unhealthy",
            "error": "Connection timeout",
            "details": {"timeout": True}
        }
    except Exception as e:
        checks["mysql"] = {
            "status": "unhealthy",
            "error": str(e),
            "details": {"exception": type(e).__name__}
        }

    # Check MongoDB
    try:
        mongodb_repo = container.mongodb_repository()
        mongodb_connected = await asyncio.wait_for(
            mongodb_repo.test_connection(),
            timeout=5.0
        )

        checks["mongodb"] = {
            "status": "healthy" if mongodb_connected else "unhealthy",
            "response_time_ms": 0,  # TODO: Measure actual response time
            "details": {
                "connected": mongodb_connected,
                "database": "ludafarma"
            }
        }
    except asyncio.TimeoutError:
        checks["mongodb"] = {
            "status": "unhealthy",
            "error": "Connection timeout",
            "details": {"timeout": True}
        }
    except Exception as e:
        checks["mongodb"] = {
            "status": "unhealthy",
            "error": str(e),
            "details": {"exception": type(e).__name__}
        }

    return checks


async def _check_cache(container: Container) -> Dict[str, Any]:
    """Check cache service."""
    try:
        # TODO: Implement cache health check
        # For now, assume it's healthy
        return {
            "status": "healthy",
            "type": "in-memory",
            "details": {
                "available": True
            }
        }
    except Exception as e:
        return {
            "status": "unhealthy",
            "error": str(e),
            "details": {"exception": type(e).__name__}
        }


async def _check_llm_service(container: Container) -> Dict[str, Any]:
    """Check LLM service availability."""
    try:
        llm_repo = container.openai_llm_repository()
        model_info = llm_repo.get_model_info()

        return {
            "status": "healthy",
            "model": model_info.get("model", "unknown"),
            "details": model_info
        }
    except Exception as e:
        return {
            "status": "degraded",  # LLM issues shouldn't make the app unhealthy
            "error": str(e),
            "details": {"exception": type(e).__name__}
        }


def _check_system_resources() -> Dict[str, Any]:
    """Check system resource usage."""
    cpu_percent = psutil.cpu_percent(interval=1)
    memory = psutil.virtual_memory()
    disk = psutil.disk_usage('/')

    # Determine status based on usage
    status = "healthy"
    warnings = []

    if cpu_percent > 90:
        status = "degraded"
        warnings.append("High CPU usage")
    elif cpu_percent > 95:
        status = "unhealthy"
        warnings.append("Critical CPU usage")

    if memory.percent > 85:
        if status == "healthy":
            status = "degraded"
        warnings.append("High memory usage")
    elif memory.percent > 95:
        status = "unhealthy"
        warnings.append("Critical memory usage")

    if disk.percent > 90:
        if status == "healthy":
            status = "degraded"
        warnings.append("Low disk space")
    elif disk.percent > 95:
        status = "unhealthy"
        warnings.append("Critical disk space")

    return {
        "status": status,
        "cpu_percent": cpu_percent,
        "memory_percent": memory.percent,
        "disk_percent": disk.percent,
        "warnings": warnings,
        "details": {
            "cpu_count": psutil.cpu_count(),
            "memory_available_mb": memory.available / 1024 / 1024,
            "disk_free_gb": disk.free / 1024 / 1024 / 1024
        }
    }