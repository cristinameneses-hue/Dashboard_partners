"""
API Dependencies

FastAPI dependency injection functions for common requirements.
"""

from fastapi import Depends, HTTPException, Request, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from typing import Optional
import jwt
import os
from datetime import datetime

from ...domain.entities.user import User
from ...infrastructure.di.container import Container

# Security scheme
security = HTTPBearer(auto_error=False)

# JWT Configuration
JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", "your-secret-key-change-in-production")
JWT_ALGORITHM = "HS256"


async def get_container(request: Request) -> Container:
    """
    Get dependency injection container from application state.

    Args:
        request: FastAPI request object

    Returns:
        Container instance

    Raises:
        HTTPException: If container not initialized
    """
    if not hasattr(request.app.state, "container"):
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Dependency container not initialized"
        )

    return request.app.state.container


async def get_current_user_optional(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
    container: Container = Depends(get_container)
) -> Optional[User]:
    """
    Get current user from JWT token (optional).

    Args:
        credentials: Bearer token credentials
        container: Dependency injection container

    Returns:
        User if authenticated, None otherwise
    """
    if not credentials:
        return None

    try:
        # Decode JWT token
        payload = jwt.decode(
            credentials.credentials,
            JWT_SECRET_KEY,
            algorithms=[JWT_ALGORITHM]
        )

        # Check expiration
        exp = payload.get("exp")
        if exp and datetime.utcfromtimestamp(exp) < datetime.utcnow():
            return None

        # Get user ID from token
        user_id = payload.get("sub")
        if not user_id:
            return None

        # Get user from repository
        user_repository = container.user_repository()
        user = await user_repository.get_by_id(user_id)

        return user

    except jwt.PyJWTError:
        return None
    except Exception:
        return None


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    container: Container = Depends(get_container)
) -> User:
    """
    Get current user from JWT token (required).

    Args:
        credentials: Bearer token credentials
        container: Dependency injection container

    Returns:
        Authenticated user

    Raises:
        HTTPException: If not authenticated or token invalid
    """
    if not credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required",
            headers={"WWW-Authenticate": "Bearer"}
        )

    try:
        # Decode JWT token
        payload = jwt.decode(
            credentials.credentials,
            JWT_SECRET_KEY,
            algorithms=[JWT_ALGORITHM]
        )

        # Check expiration
        exp = payload.get("exp")
        if exp and datetime.utcfromtimestamp(exp) < datetime.utcnow():
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token has expired",
                headers={"WWW-Authenticate": "Bearer"}
            )

        # Get user ID from token
        user_id = payload.get("sub")
        if not user_id:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token payload",
                headers={"WWW-Authenticate": "Bearer"}
            )

        # Get user from repository
        user_repository = container.user_repository()
        user = await user_repository.get_by_id(user_id)

        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User not found",
                headers={"WWW-Authenticate": "Bearer"}
            )

        # Check if user is active
        if not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="User account is disabled"
            )

        return user

    except jwt.PyJWTError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Could not validate credentials: {str(e)}",
            headers={"WWW-Authenticate": "Bearer"}
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Authentication error: {str(e)}"
        )


async def get_admin_user(
    current_user: User = Depends(get_current_user)
) -> User:
    """
    Require admin user.

    Args:
        current_user: Authenticated user

    Returns:
        Admin user

    Raises:
        HTTPException: If user is not admin
    """
    if not current_user.is_admin():
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin privileges required"
        )

    return current_user


async def verify_api_key(
    request: Request,
    api_key: Optional[str] = None
) -> bool:
    """
    Verify API key from headers or query parameter.

    Args:
        request: FastAPI request
        api_key: Optional API key from query

    Returns:
        True if API key is valid

    Raises:
        HTTPException: If API key is invalid
    """
    # Check header first
    key = request.headers.get("X-API-Key") or api_key

    if not key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="API key required"
        )

    # Verify against configured keys
    valid_keys = os.getenv("API_KEYS", "").split(",")
    if key not in valid_keys:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid API key"
        )

    return True


# Request ID dependency
async def get_request_id(request: Request) -> str:
    """
    Get or generate request ID for tracking.

    Args:
        request: FastAPI request

    Returns:
        Request ID string
    """
    request_id = request.headers.get("X-Request-ID")

    if not request_id:
        import uuid
        request_id = f"req_{uuid.uuid4().hex[:8]}"

    return request_id


# Rate limiting dependency (simplified)
class RateLimiter:
    """Simple in-memory rate limiter."""

    def __init__(self, requests_per_minute: int = 60):
        self.requests_per_minute = requests_per_minute
        self.requests = {}

    async def check_rate_limit(self, key: str) -> bool:
        """
        Check if rate limit exceeded.

        Args:
            key: Rate limit key (e.g., user ID or IP)

        Returns:
            True if within limit

        Raises:
            HTTPException: If rate limit exceeded
        """
        from datetime import datetime, timedelta

        now = datetime.utcnow()
        minute_ago = now - timedelta(minutes=1)

        # Clean old requests
        if key in self.requests:
            self.requests[key] = [
                ts for ts in self.requests[key]
                if ts > minute_ago
            ]
        else:
            self.requests[key] = []

        # Check limit
        if len(self.requests[key]) >= self.requests_per_minute:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="Rate limit exceeded",
                headers={"Retry-After": "60"}
            )

        # Add current request
        self.requests[key].append(now)
        return True


# Create rate limiter instances
default_rate_limiter = RateLimiter(requests_per_minute=60)
strict_rate_limiter = RateLimiter(requests_per_minute=20)


async def rate_limit(
    request: Request,
    current_user: Optional[User] = Depends(get_current_user_optional)
):
    """
    Apply rate limiting to requests.

    Args:
        request: FastAPI request
        current_user: Optional authenticated user

    Raises:
        HTTPException: If rate limit exceeded
    """
    # Use user ID if authenticated, otherwise use IP
    if current_user:
        key = f"user:{current_user.id}"
    else:
        key = f"ip:{request.client.host}"

    await default_rate_limiter.check_rate_limit(key)


async def strict_rate_limit(
    request: Request,
    current_user: Optional[User] = Depends(get_current_user_optional)
):
    """
    Apply strict rate limiting to sensitive endpoints.

    Args:
        request: FastAPI request
        current_user: Optional authenticated user

    Raises:
        HTTPException: If rate limit exceeded
    """
    # Use user ID if authenticated, otherwise use IP
    if current_user:
        key = f"user:{current_user.id}"
    else:
        key = f"ip:{request.client.host}"

    await strict_rate_limiter.check_rate_limit(key)