"""
Environment Module

Handles environment variable loading and validation.
"""

import os
import logging
from pathlib import Path
from typing import Dict, Any, List, Optional
from dotenv import load_dotenv

logger = logging.getLogger(__name__)


def load_environment(env_file: Optional[Path] = None) -> Dict[str, Any]:
    """
    Load environment variables

    Args:
        env_file: Optional path to .env file

    Returns:
        Dict[str, Any]: Environment variables
    """
    # Load from file if provided
    if env_file and env_file.exists():
        logger.info(f"Loading environment from: {env_file}")
        load_dotenv(env_file, override=True)
    else:
        # Try to find .env in current directory
        default_env = Path.cwd() / ".env"
        if default_env.exists():
            logger.info(f"Loading environment from default: {default_env}")
            load_dotenv(default_env)

    # Collect all environment variables
    env_vars = dict(os.environ)

    # Log loaded configuration (without sensitive data)
    _log_environment(env_vars)

    return env_vars


def validate_environment(env_vars: Dict[str, Any], required: List[str]) -> List[str]:
    """
    Validate required environment variables

    Args:
        env_vars: Environment variables
        required: List of required variable names

    Returns:
        List[str]: List of missing variables
    """
    missing = []

    for var in required:
        if var not in env_vars or not env_vars[var]:
            missing.append(var)

    if missing:
        logger.error(f"Missing required environment variables: {', '.join(missing)}")
    else:
        logger.info("All required environment variables are set")

    return missing


def get_database_configs(env_vars: Dict[str, Any]) -> Dict[str, Dict[str, Any]]:
    """
    Extract database configurations from environment

    Args:
        env_vars: Environment variables

    Returns:
        Dict with 'mysql' and 'mongodb' configurations
    """
    mysql_configs = {}
    mongodb_configs = {}

    for key, value in env_vars.items():
        # MySQL databases (DB_*_URL pattern)
        if key.startswith('DB_') and key.endswith('_URL'):
            db_name = key[3:-4].lower()  # Extract name between DB_ and _URL
            mysql_configs[db_name] = {
                'url': value,
                'can_insert': env_vars.get(f'DB_{db_name.upper()}_CAN_INSERT', 'false').lower() == 'true',
                'can_update': env_vars.get(f'DB_{db_name.upper()}_CAN_UPDATE', 'false').lower() == 'true',
                'can_delete': env_vars.get(f'DB_{db_name.upper()}_CAN_DELETE', 'false').lower() == 'true',
                'is_default': env_vars.get(f'DB_{db_name.upper()}_IS_DEFAULT', 'false').lower() == 'true'
            }

        # MongoDB databases (MONGO_*_URL pattern)
        elif key.startswith('MONGO_') and key.endswith('_URL'):
            db_name = key[6:-4].lower()  # Extract name between MONGO_ and _URL
            mongodb_configs[db_name] = {
                'url': value,
                'can_insert': env_vars.get(f'MONGO_{db_name.upper()}_CAN_INSERT', 'false').lower() == 'true',
                'can_update': env_vars.get(f'MONGO_{db_name.upper()}_CAN_UPDATE', 'false').lower() == 'true',
                'can_delete': env_vars.get(f'MONGO_{db_name.upper()}_CAN_DELETE', 'false').lower() == 'true',
                'is_default': env_vars.get(f'MONGO_{db_name.upper()}_IS_DEFAULT', 'false').lower() == 'true'
            }

    return {
        'mysql': mysql_configs,
        'mongodb': mongodb_configs
    }


def get_openai_config(env_vars: Dict[str, Any]) -> Dict[str, Any]:
    """
    Extract OpenAI configuration

    Args:
        env_vars: Environment variables

    Returns:
        OpenAI configuration dict
    """
    return {
        'api_key': env_vars.get('OPENAI_API_KEY'),
        'model': env_vars.get('OPENAI_MODEL', 'gpt-4o-mini'),
        'temperature': float(env_vars.get('OPENAI_TEMPERATURE', '0.1')),
        'max_tokens': int(env_vars.get('OPENAI_MAX_TOKENS', '2000')),
        'stream': env_vars.get('OPENAI_STREAM', 'true').lower() == 'true'
    }


def get_chatgpt_config(env_vars: Dict[str, Any]) -> Dict[str, Any]:
    """
    Extract ChatGPT configuration

    Args:
        env_vars: Environment variables

    Returns:
        ChatGPT configuration dict
    """
    return {
        'api_key': env_vars.get('CHATGPT_API_KEY') or env_vars.get('OPENAI_API_KEY'),
        'model': env_vars.get('CHATGPT_MODEL', 'gpt-4'),
        'temperature': float(env_vars.get('CHATGPT_TEMPERATURE', '0.1')),
        'max_tokens': int(env_vars.get('CHATGPT_MAX_TOKENS', '3000')),
        'system_prompt': env_vars.get('CHATGPT_SYSTEM_PROMPT')
    }


def get_redis_config(env_vars: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """
    Extract Redis configuration

    Args:
        env_vars: Environment variables

    Returns:
        Redis configuration dict or None
    """
    redis_url = env_vars.get('REDIS_URL')
    if not redis_url:
        return None

    return {
        'url': redis_url,
        'max_connections': int(env_vars.get('REDIS_MAX_CONNECTIONS', '10')),
        'socket_timeout': int(env_vars.get('REDIS_SOCKET_TIMEOUT', '5')),
        'decode_responses': True
    }


def get_security_config(env_vars: Dict[str, Any]) -> Dict[str, Any]:
    """
    Extract security configuration

    Args:
        env_vars: Environment variables

    Returns:
        Security configuration dict
    """
    return {
        'secret_key': env_vars.get('SECRET_KEY', 'dev-secret-key-change-in-production'),
        'jwt_secret': env_vars.get('JWT_SECRET', 'dev-jwt-secret'),
        'jwt_algorithm': env_vars.get('JWT_ALGORITHM', 'HS256'),
        'jwt_expiration_minutes': int(env_vars.get('JWT_EXPIRATION_MINUTES', '1440')),  # 24 hours
        'allow_insert': env_vars.get('ALLOW_INSERT_OPERATION', 'false').lower() == 'true',
        'allow_update': env_vars.get('ALLOW_UPDATE_OPERATION', 'false').lower() == 'true',
        'allow_delete': env_vars.get('ALLOW_DELETE_OPERATION', 'false').lower() == 'true',
        'allow_ddl': env_vars.get('ALLOW_DDL_OPERATION', 'false').lower() == 'true',
        'cors_origins': env_vars.get('CORS_ORIGINS', '*').split(','),
        'rate_limit_requests': int(env_vars.get('RATE_LIMIT_REQUESTS', '100')),
        'rate_limit_period': int(env_vars.get('RATE_LIMIT_PERIOD', '60'))  # seconds
    }


def get_app_config(env_vars: Dict[str, Any]) -> Dict[str, Any]:
    """
    Extract application configuration

    Args:
        env_vars: Environment variables

    Returns:
        Application configuration dict
    """
    return {
        'name': env_vars.get('APP_NAME', 'TrendsPro'),
        'version': env_vars.get('APP_VERSION', '3.0.0'),
        'environment': env_vars.get('ENVIRONMENT', 'development'),
        'debug': env_vars.get('DEBUG', 'false').lower() == 'true',
        'host': env_vars.get('APP_HOST', '0.0.0.0'),
        'port': int(env_vars.get('APP_PORT', '8000')),
        'workers': int(env_vars.get('APP_WORKERS', '1')),
        'reload': env_vars.get('APP_RELOAD', 'false').lower() == 'true',
        'log_level': env_vars.get('LOG_LEVEL', 'INFO'),
        'enable_docs': env_vars.get('ENABLE_DOCS', 'true').lower() == 'true',
        'docs_url': env_vars.get('DOCS_URL', '/docs'),
        'redoc_url': env_vars.get('REDOC_URL', '/redoc')
    }


def _log_environment(env_vars: Dict[str, Any]) -> None:
    """
    Log environment configuration (hiding sensitive values)

    Args:
        env_vars: Environment variables
    """
    sensitive_patterns = [
        'KEY', 'SECRET', 'PASSWORD', 'PASS', 'TOKEN', 'API', 'CREDENTIAL'
    ]

    logger.info("Environment configuration:")

    for key, value in sorted(env_vars.items()):
        # Skip system environment variables
        if key.startswith('_') or key in ['PATH', 'PYTHONPATH', 'HOME', 'USER']:
            continue

        # Check if sensitive
        is_sensitive = any(pattern in key.upper() for pattern in sensitive_patterns)

        if is_sensitive:
            masked_value = value[:4] + '***' if value and len(value) > 4 else '***'
            logger.info(f"  {key}: {masked_value}")
        else:
            logger.info(f"  {key}: {value}")


def create_env_file(
    path: Path,
    mysql_url: str,
    mongodb_url: str,
    openai_key: str,
    **kwargs
) -> None:
    """
    Create a new .env file with basic configuration

    Args:
        path: Path to create .env file
        mysql_url: MySQL connection URL
        mongodb_url: MongoDB connection URL
        openai_key: OpenAI API key
        **kwargs: Additional configuration
    """
    template = f"""# TrendsPro Environment Configuration
# Generated automatically - Please review and update

# Application
APP_NAME=TrendsPro
APP_VERSION=3.0.0
ENVIRONMENT=development
DEBUG=false
LOG_LEVEL=INFO

# MySQL Database
DB_TRENDS_URL={mysql_url}
DB_TRENDS_CAN_INSERT=false
DB_TRENDS_CAN_UPDATE=false
DB_TRENDS_CAN_DELETE=false
DB_TRENDS_IS_DEFAULT=true

# MongoDB Database
MONGO_LUDAFARMA_URL={mongodb_url}
MONGO_LUDAFARMA_CAN_INSERT=false
MONGO_LUDAFARMA_CAN_UPDATE=false
MONGO_LUDAFARMA_CAN_DELETE=false
MONGO_LUDAFARMA_IS_DEFAULT=false

# OpenAI
OPENAI_API_KEY={openai_key}
OPENAI_MODEL=gpt-4o-mini
OPENAI_TEMPERATURE=0.1
OPENAI_MAX_TOKENS=2000

# ChatGPT (optional - uses OpenAI key if not set)
# CHATGPT_API_KEY=
# CHATGPT_MODEL=gpt-4

# Redis Cache (optional)
# REDIS_URL=redis://localhost:6379/0

# Security
SECRET_KEY={kwargs.get('secret_key', 'change-this-in-production')}
JWT_SECRET={kwargs.get('jwt_secret', 'change-this-in-production')}
JWT_ALGORITHM=HS256
JWT_EXPIRATION_MINUTES=1440

# Security Permissions
ALLOW_INSERT_OPERATION=false
ALLOW_UPDATE_OPERATION=false
ALLOW_DELETE_OPERATION=false
ALLOW_DDL_OPERATION=false

# CORS
CORS_ORIGINS=http://localhost:3000,http://localhost:8000

# Rate Limiting
RATE_LIMIT_REQUESTS=100
RATE_LIMIT_PERIOD=60

# Server
APP_HOST=0.0.0.0
APP_PORT=8000
APP_WORKERS=1
APP_RELOAD=false

# API Documentation
ENABLE_DOCS=true
DOCS_URL=/docs
REDOC_URL=/redoc
"""

    path.write_text(template)
    logger.info(f"Created .env file at: {path}")


def check_environment_health() -> Dict[str, Any]:
    """
    Check environment configuration health

    Returns:
        Dict with health status and issues
    """
    env_vars = dict(os.environ)
    issues = []
    warnings = []

    # Check required variables
    required = ['DB_TRENDS_URL', 'MONGO_LUDAFARMA_URL', 'OPENAI_API_KEY']
    missing = validate_environment(env_vars, required)
    if missing:
        issues.extend([f"Missing: {var}" for var in missing])

    # Check for development defaults in production
    if env_vars.get('ENVIRONMENT') == 'production':
        if env_vars.get('SECRET_KEY', '').startswith('dev-'):
            issues.append("Using development SECRET_KEY in production")
        if env_vars.get('JWT_SECRET', '').startswith('dev-'):
            issues.append("Using development JWT_SECRET in production")
        if env_vars.get('DEBUG', 'false').lower() == 'true':
            warnings.append("DEBUG mode enabled in production")

    # Check database permissions
    if env_vars.get('ALLOW_DDL_OPERATION', 'false').lower() == 'true':
        warnings.append("DDL operations are enabled - use with caution")

    # Check Redis availability for production
    if env_vars.get('ENVIRONMENT') == 'production' and not env_vars.get('REDIS_URL'):
        warnings.append("Redis not configured for production - caching disabled")

    return {
        'healthy': len(issues) == 0,
        'issues': issues,
        'warnings': warnings,
        'environment': env_vars.get('ENVIRONMENT', 'unknown'),
        'databases': {
            'mysql': bool(env_vars.get('DB_TRENDS_URL')),
            'mongodb': bool(env_vars.get('MONGO_LUDAFARMA_URL')),
            'redis': bool(env_vars.get('REDIS_URL'))
        }
    }