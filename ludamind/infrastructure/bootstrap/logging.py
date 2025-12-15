"""
Logging Module

Configures structured logging for the application.
"""

import logging
import sys
import json
from pathlib import Path
from datetime import datetime
from typing import Optional, Dict, Any
from logging.handlers import RotatingFileHandler, TimedRotatingFileHandler


class JSONFormatter(logging.Formatter):
    """Custom JSON formatter for structured logging"""

    def __init__(self, app_name: str = "TrendsPro", environment: str = "development"):
        super().__init__()
        self.app_name = app_name
        self.environment = environment

    def format(self, record: logging.LogRecord) -> str:
        """Format log record as JSON"""
        log_obj = {
            '@timestamp': datetime.utcnow().isoformat(),
            'level': record.levelname,
            'logger': record.name,
            'message': record.getMessage(),
            'app': self.app_name,
            'environment': self.environment,
            'module': record.module,
            'function': record.funcName,
            'line': record.lineno
        }

        # Add exception info if present
        if record.exc_info:
            log_obj['exception'] = self.formatException(record.exc_info)

        # Add extra fields
        if hasattr(record, 'user_id'):
            log_obj['user_id'] = record.user_id
        if hasattr(record, 'request_id'):
            log_obj['request_id'] = record.request_id
        if hasattr(record, 'query_id'):
            log_obj['query_id'] = record.query_id
        if hasattr(record, 'conversation_id'):
            log_obj['conversation_id'] = record.conversation_id

        return json.dumps(log_obj)


class ColoredFormatter(logging.Formatter):
    """Colored formatter for console output"""

    COLORS = {
        'DEBUG': '\033[36m',    # Cyan
        'INFO': '\033[32m',     # Green
        'WARNING': '\033[33m',  # Yellow
        'ERROR': '\033[31m',    # Red
        'CRITICAL': '\033[35m'  # Magenta
    }
    RESET = '\033[0m'

    def format(self, record: logging.LogRecord) -> str:
        """Format with colors"""
        levelname = record.levelname
        if levelname in self.COLORS:
            record.levelname = f"{self.COLORS[levelname]}{levelname}{self.RESET}"

        # Format timestamp
        record.asctime = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

        # Use different format for different levels
        if levelname == 'DEBUG':
            format_str = '%(asctime)s - %(levelname)s - %(name)s.%(funcName)s:%(lineno)d - %(message)s'
        elif levelname in ['ERROR', 'CRITICAL']:
            format_str = '%(asctime)s - %(levelname)s - %(name)s - %(message)s\n%(pathname)s:%(lineno)d'
        else:
            format_str = '%(asctime)s - %(levelname)s - %(name)s - %(message)s'

        formatter = logging.Formatter(format_str)
        return formatter.format(record)


def setup_logging(
    level: str = "INFO",
    format: str = "json",
    app_name: str = "TrendsPro",
    environment: str = "development",
    log_file: Optional[Path] = None,
    max_bytes: int = 10485760,  # 10MB
    backup_count: int = 5,
    **kwargs
) -> None:
    """
    Setup logging configuration

    Args:
        level: Log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        format: Log format ('json' or 'text')
        app_name: Application name for logs
        environment: Environment name
        log_file: Optional log file path
        max_bytes: Max size for log rotation
        backup_count: Number of backup files to keep
    """
    # Get root logger
    root_logger = logging.getLogger()

    # Clear existing handlers
    root_logger.handlers = []

    # Set level
    log_level = getattr(logging, level.upper(), logging.INFO)
    root_logger.setLevel(log_level)

    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)

    if format.lower() == "json":
        console_formatter = JSONFormatter(app_name, environment)
    else:
        console_formatter = ColoredFormatter()

    console_handler.setFormatter(console_formatter)
    root_logger.addHandler(console_handler)

    # File handler (if specified)
    if log_file:
        log_file = Path(log_file)
        log_file.parent.mkdir(parents=True, exist_ok=True)

        file_handler = RotatingFileHandler(
            log_file,
            maxBytes=max_bytes,
            backupCount=backup_count
        )

        # Always use JSON for file logging
        file_formatter = JSONFormatter(app_name, environment)
        file_handler.setFormatter(file_formatter)
        root_logger.addHandler(file_handler)

    # Configure specific loggers
    _configure_library_loggers()

    # Log initial message
    logging.info(
        f"Logging configured: level={level}, format={format}, environment={environment}"
    )


def _configure_library_loggers() -> None:
    """Configure third-party library loggers"""

    # Reduce noise from libraries
    noisy_loggers = [
        'urllib3',
        'asyncio',
        'pymongo',
        'mysql.connector',
        'openai',
        'httpx',
        'httpcore'
    ]

    for logger_name in noisy_loggers:
        logger = logging.getLogger(logger_name)
        logger.setLevel(logging.WARNING)

    # Special configuration for SQLAlchemy
    logging.getLogger('sqlalchemy.engine').setLevel(logging.WARNING)
    logging.getLogger('sqlalchemy.pool').setLevel(logging.WARNING)

    # FastAPI/Uvicorn loggers
    logging.getLogger('uvicorn.access').setLevel(logging.INFO)
    logging.getLogger('uvicorn.error').setLevel(logging.INFO)


class RequestContextFilter(logging.Filter):
    """Add request context to log records"""

    def __init__(self, request_id_header: str = "X-Request-ID"):
        super().__init__()
        self.request_id_header = request_id_header

    def filter(self, record: logging.LogRecord) -> bool:
        """Add request context to record"""
        # Try to get request context from contextvars
        try:
            from contextvars import ContextVar
            request_id_var: ContextVar[Optional[str]] = ContextVar('request_id', default=None)
            user_id_var: ContextVar[Optional[str]] = ContextVar('user_id', default=None)

            request_id = request_id_var.get()
            user_id = user_id_var.get()

            if request_id:
                record.request_id = request_id
            if user_id:
                record.user_id = user_id

        except ImportError:
            pass

        return True


class PerformanceLogger:
    """Logger for performance metrics"""

    def __init__(self, logger: Optional[logging.Logger] = None):
        self.logger = logger or logging.getLogger(__name__)

    def log_query_performance(
        self,
        query_id: str,
        query_text: str,
        database: str,
        execution_time_ms: float,
        from_cache: bool = False,
        result_count: int = 0
    ) -> None:
        """Log query performance metrics"""
        self.logger.info(
            "Query executed",
            extra={
                'query_id': query_id,
                'query_text': query_text[:100],  # Truncate long queries
                'database': database,
                'execution_time_ms': execution_time_ms,
                'from_cache': from_cache,
                'result_count': result_count,
                'metric_type': 'query_performance'
            }
        )

    def log_api_request(
        self,
        method: str,
        path: str,
        status_code: int,
        response_time_ms: float,
        user_id: Optional[str] = None
    ) -> None:
        """Log API request metrics"""
        self.logger.info(
            f"{method} {path} - {status_code}",
            extra={
                'method': method,
                'path': path,
                'status_code': status_code,
                'response_time_ms': response_time_ms,
                'user_id': user_id,
                'metric_type': 'api_request'
            }
        )

    def log_llm_usage(
        self,
        model: str,
        prompt_tokens: int,
        completion_tokens: int,
        total_tokens: int,
        cost_usd: float,
        latency_ms: float
    ) -> None:
        """Log LLM usage metrics"""
        self.logger.info(
            f"LLM usage: {model}",
            extra={
                'model': model,
                'prompt_tokens': prompt_tokens,
                'completion_tokens': completion_tokens,
                'total_tokens': total_tokens,
                'cost_usd': cost_usd,
                'latency_ms': latency_ms,
                'metric_type': 'llm_usage'
            }
        )


class AuditLogger:
    """Logger for audit events"""

    def __init__(self, logger: Optional[logging.Logger] = None):
        self.logger = logger or logging.getLogger('audit')

    def log_login(self, user_id: str, success: bool, ip_address: str) -> None:
        """Log login attempt"""
        self.logger.info(
            f"Login {'successful' if success else 'failed'}",
            extra={
                'user_id': user_id,
                'success': success,
                'ip_address': ip_address,
                'event_type': 'login'
            }
        )

    def log_data_access(
        self,
        user_id: str,
        resource: str,
        action: str,
        success: bool
    ) -> None:
        """Log data access"""
        self.logger.info(
            f"Data access: {action} on {resource}",
            extra={
                'user_id': user_id,
                'resource': resource,
                'action': action,
                'success': success,
                'event_type': 'data_access'
            }
        )

    def log_configuration_change(
        self,
        user_id: str,
        setting: str,
        old_value: Any,
        new_value: Any
    ) -> None:
        """Log configuration changes"""
        self.logger.warning(
            f"Configuration changed: {setting}",
            extra={
                'user_id': user_id,
                'setting': setting,
                'old_value': str(old_value),
                'new_value': str(new_value),
                'event_type': 'config_change'
            }
        )


# Create global logger instances
performance_logger = PerformanceLogger()
audit_logger = AuditLogger()