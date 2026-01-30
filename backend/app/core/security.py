"""
Security module for JWT and Google OAuth authentication.
"""
from datetime import datetime, timedelta
from typing import Optional, Set
from jose import JWTError, jwt
from fastapi import HTTPException, status, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from google.oauth2 import id_token
from google.auth.transport import requests as google_requests
import os
import threading
import logging

logger = logging.getLogger(__name__)

# Configuration from settings (loaded from .env via pydantic)
from .config import get_settings


# =============================================================================
# TOKEN BLACKLIST SYSTEM
# =============================================================================
# Simple in-memory blacklist with automatic cleanup
# For production with multiple instances, use Redis instead

class TokenBlacklist:
    """
    Thread-safe token blacklist for JWT revocation.
    Stores token JTIs (JWT IDs) or full tokens with expiration cleanup.
    """

    def __init__(self):
        self._blacklist: Set[str] = set()
        self._expiry_times: dict = {}  # token -> expiry_timestamp
        self._lock = threading.Lock()

    def add(self, token: str, expires_at: datetime) -> None:
        """Add a token to the blacklist."""
        with self._lock:
            self._blacklist.add(token)
            self._expiry_times[token] = expires_at
            self._cleanup_expired()

    def is_blacklisted(self, token: str) -> bool:
        """Check if a token is blacklisted."""
        with self._lock:
            self._cleanup_expired()
            return token in self._blacklist

    def _cleanup_expired(self) -> None:
        """Remove expired tokens from blacklist to prevent memory growth."""
        now = datetime.utcnow()
        expired = [
            token for token, exp_time in self._expiry_times.items()
            if exp_time < now
        ]
        for token in expired:
            self._blacklist.discard(token)
            del self._expiry_times[token]

    def revoke_all_for_user(self, user_email: str) -> int:
        """
        Revoke all tokens for a specific user.
        Note: This requires storing user info with tokens - simplified version.
        Returns count of revoked tokens.
        """
        # In a full implementation, you'd track user -> tokens mapping
        # For now, this is a placeholder for future enhancement
        logger.info(f"Token revocation requested for user: {user_email}")
        return 0


# Global blacklist instance
token_blacklist = TokenBlacklist()

def _get_jwt_secret_key():
    return get_settings().jwt_secret_key

def _get_jwt_algorithm():
    return get_settings().jwt_algorithm

def _get_jwt_expiration_minutes():
    return get_settings().jwt_expiration_minutes

def _get_google_client_id():
    return get_settings().google_client_id

def _get_allowed_email_domain():
    return get_settings().allowed_email_domain


class JWTBearer(HTTPBearer):
    """Custom JWT Bearer authentication."""

    def __init__(self, auto_error: bool = True):
        super(JWTBearer, self).__init__(auto_error=auto_error)

    async def __call__(self, request: Request) -> Optional[dict]:
        credentials: HTTPAuthorizationCredentials = await super(JWTBearer, self).__call__(request)
        if credentials:
            if not credentials.scheme == "Bearer":
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Invalid authentication scheme."
                )
            payload = verify_jwt_token(credentials.credentials)
            if not payload:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Invalid or expired token."
                )
            return payload
        else:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Invalid authorization code."
            )


def verify_google_token(token: str) -> dict:
    """
    Verify Google OAuth token and return user info.

    Args:
        token: Google ID token from frontend

    Returns:
        User info dict with email, name, picture, etc.

    Raises:
        HTTPException: If token is invalid or email domain not allowed
    """
    google_client_id = _get_google_client_id()
    if not google_client_id:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Google OAuth not configured"
        )

    try:
        # Verify the token
        idinfo = id_token.verify_oauth2_token(
            token,
            google_requests.Request(),
            google_client_id
        )

        # Verify issuer
        if idinfo['iss'] not in ['accounts.google.com', 'https://accounts.google.com']:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token issuer"
            )

        # Verify email domain if configured
        email = idinfo.get('email', '')
        allowed_domain = _get_allowed_email_domain()
        if allowed_domain:
            if not email.endswith(f"@{allowed_domain}"):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"Email domain not allowed. Must be @{allowed_domain}"
                )

        return {
            "email": email,
            "name": idinfo.get('name', ''),
            "picture": idinfo.get('picture', ''),
            "email_verified": idinfo.get('email_verified', False),
            "sub": idinfo.get('sub', '')  # Google user ID
        }

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Invalid Google token: {str(e)}"
        )


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """
    Create a JWT access token.

    Args:
        data: Payload data to encode
        expires_delta: Optional custom expiration time

    Returns:
        Encoded JWT token string
    """
    jwt_secret = _get_jwt_secret_key()
    if not jwt_secret:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="JWT not configured"
        )

    to_encode = data.copy()

    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=_get_jwt_expiration_minutes())

    to_encode.update({
        "exp": expire,
        "iat": datetime.utcnow(),
        "type": "access"
    })

    return jwt.encode(to_encode, jwt_secret, algorithm=_get_jwt_algorithm())


def create_refresh_token(data: dict) -> str:
    """
    Create a JWT refresh token with longer expiration.

    Args:
        data: Payload data to encode

    Returns:
        Encoded JWT refresh token string
    """
    jwt_secret = _get_jwt_secret_key()
    if not jwt_secret:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="JWT not configured"
        )

    to_encode = data.copy()
    # Refresh tokens last 7 days
    expire = datetime.utcnow() + timedelta(days=7)

    to_encode.update({
        "exp": expire,
        "iat": datetime.utcnow(),
        "type": "refresh"
    })

    return jwt.encode(to_encode, jwt_secret, algorithm=_get_jwt_algorithm())


def verify_jwt_token(token: str) -> Optional[dict]:
    """
    Verify and decode a JWT token.

    Args:
        token: JWT token string

    Returns:
        Decoded payload dict or None if invalid/blacklisted
    """
    jwt_secret = _get_jwt_secret_key()
    if not jwt_secret:
        return None

    # Check if token is blacklisted (revoked)
    if token_blacklist.is_blacklisted(token):
        logger.debug("Token rejected: blacklisted")
        return None

    try:
        payload = jwt.decode(token, jwt_secret, algorithms=[_get_jwt_algorithm()])
        return payload
    except JWTError:
        return None


def blacklist_token(token: str) -> bool:
    """
    Add a token to the blacklist (revoke it).

    Args:
        token: JWT token to blacklist

    Returns:
        True if successfully blacklisted, False otherwise
    """
    try:
        # Decode without verification to get expiry
        # (we don't care if it's valid, just need expiry for cleanup)
        payload = jwt.decode(
            token,
            _get_jwt_secret_key(),
            algorithms=[_get_jwt_algorithm()],
            options={"verify_exp": False}  # Allow expired tokens to be blacklisted
        )

        # Get expiration time from payload
        exp_timestamp = payload.get("exp")
        if exp_timestamp:
            expires_at = datetime.fromtimestamp(exp_timestamp)
        else:
            # Default: blacklist for 7 days (max token lifetime)
            expires_at = datetime.utcnow() + timedelta(days=7)

        token_blacklist.add(token, expires_at)
        logger.info(f"Token blacklisted for user: {payload.get('sub', 'unknown')}")
        return True

    except Exception as e:
        logger.error(f"Failed to blacklist token: {e}")
        return False


def get_current_user(token: str) -> dict:
    """
    Get the current user from a JWT token.

    Args:
        token: JWT token string

    Returns:
        User info dict

    Raises:
        HTTPException: If token is invalid
    """
    payload = verify_jwt_token(token)
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return payload


# Dependency for protected routes
jwt_bearer = JWTBearer()
