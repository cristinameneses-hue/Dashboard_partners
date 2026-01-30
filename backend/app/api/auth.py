"""
Authentication endpoints for Google OAuth and JWT token management.
"""
from fastapi import APIRouter, HTTPException, Response, Request, Depends
from pydantic import BaseModel
from typing import Optional
from ..core.config import get_settings
from ..core.security import (
    verify_google_token,
    create_access_token,
    create_refresh_token,
    verify_jwt_token,
    blacklist_token,
    jwt_bearer
)

router = APIRouter(prefix="/auth", tags=["Authentication"])


def _set_refresh_token_cookie(response: Response, refresh_token: str) -> None:
    """
    Set refresh token as httpOnly cookie with proper security settings.

    Security settings are environment-aware:
    - Production: secure=True (HTTPS only), samesite=strict
    - Development: secure=False (allows HTTP), samesite=lax
    """
    settings = get_settings()
    response.set_cookie(
        key="refresh_token",
        value=refresh_token,
        httponly=True,
        secure=settings.cookie_secure,
        samesite=settings.cookie_samesite,
        max_age=60 * 60 * 24 * 7,  # 7 days
        path="/api/auth"
    )


class GoogleToken(BaseModel):
    """Google OAuth credential from frontend."""
    credential: str


class GoogleAccessToken(BaseModel):
    """Google OAuth access token from implicit flow."""
    access_token: str


class TokenResponse(BaseModel):
    """Response with access token and user info."""
    access_token: str
    token_type: str = "bearer"
    expires_in: int
    user: dict


class RefreshTokenRequest(BaseModel):
    """Request to refresh access token."""
    refresh_token: str


@router.post("/google", response_model=TokenResponse)
async def google_login(token: GoogleToken, response: Response):
    """
    Authenticate user with Google OAuth token.

    1. Verifies the Google ID token
    2. Extracts user information
    3. Creates JWT access token
    4. Sets httpOnly cookie with refresh token

    Args:
        token: Google OAuth credential from frontend
        response: FastAPI response object for setting cookies

    Returns:
        TokenResponse with access token and user info
    """
    # Verify Google token and get user info
    user_info = verify_google_token(token.credential)

    # Create token data
    token_data = {
        "sub": user_info["email"],
        "name": user_info["name"],
        "picture": user_info.get("picture", "")
    }

    # Create access token (30 min)
    access_token = create_access_token(token_data)

    # Create refresh token (7 days)
    refresh_token = create_refresh_token(token_data)

    # Set refresh token as httpOnly cookie
    _set_refresh_token_cookie(response, refresh_token)

    return TokenResponse(
        access_token=access_token,
        token_type="bearer",
        expires_in=30 * 60,  # 30 minutes in seconds
        user=user_info
    )


@router.post("/google-token", response_model=TokenResponse)
async def google_login_with_token(token: GoogleAccessToken, response: Response):
    """
    Authenticate user with Google OAuth access token (implicit flow).
    Used when user selects account from account chooser.

    1. Fetches user info from Google using access token
    2. Verifies email domain
    3. Creates JWT access token
    4. Sets httpOnly cookie with refresh token
    """
    import httpx
    from ..core.config import get_settings

    settings = get_settings()

    # Fetch user info from Google using access token
    async with httpx.AsyncClient() as client:
        try:
            google_response = await client.get(
                "https://www.googleapis.com/oauth2/v2/userinfo",
                headers={"Authorization": f"Bearer {token.access_token}"}
            )
            if google_response.status_code != 200:
                raise HTTPException(
                    status_code=401,
                    detail="Invalid Google access token"
                )
            google_user = google_response.json()
        except Exception as e:
            raise HTTPException(
                status_code=401,
                detail=f"Failed to verify Google token: {str(e)}"
            )

    email = google_user.get("email", "")
    name = google_user.get("name", "")
    picture = google_user.get("picture", "")

    # Check email domain if configured
    if settings.allowed_email_domain:
        if not email.endswith(f"@{settings.allowed_email_domain}"):
            raise HTTPException(
                status_code=403,
                detail=f"Email domain not allowed. Only @{settings.allowed_email_domain} emails are permitted."
            )

    user_info = {
        "email": email,
        "name": name,
        "picture": picture
    }

    # Create token data
    token_data = {
        "sub": email,
        "name": name,
        "picture": picture
    }

    # Create access token (30 min)
    access_token = create_access_token(token_data)

    # Create refresh token (7 days)
    refresh_token = create_refresh_token(token_data)

    # Set refresh token as httpOnly cookie
    _set_refresh_token_cookie(response, refresh_token)

    return TokenResponse(
        access_token=access_token,
        token_type="bearer",
        expires_in=30 * 60,
        user=user_info
    )


@router.post("/refresh", response_model=TokenResponse)
async def refresh_access_token(request: Request, response: Response):
    """
    Refresh the access token using the refresh token cookie.

    Args:
        request: FastAPI request to get cookies
        response: FastAPI response to update cookie

    Returns:
        New TokenResponse with fresh access token
    """
    refresh_token = request.cookies.get("refresh_token")

    if not refresh_token:
        raise HTTPException(
            status_code=401,
            detail="No refresh token provided"
        )

    # Verify refresh token
    payload = verify_jwt_token(refresh_token)

    if not payload:
        raise HTTPException(
            status_code=401,
            detail="Invalid or expired refresh token"
        )

    if payload.get("type") != "refresh":
        raise HTTPException(
            status_code=401,
            detail="Invalid token type"
        )

    # Create new tokens
    token_data = {
        "sub": payload["sub"],
        "name": payload.get("name", ""),
        "picture": payload.get("picture", "")
    }

    new_access_token = create_access_token(token_data)
    new_refresh_token = create_refresh_token(token_data)

    # Update refresh token cookie
    _set_refresh_token_cookie(response, new_refresh_token)

    return TokenResponse(
        access_token=new_access_token,
        token_type="bearer",
        expires_in=30 * 60,
        user={
            "email": payload["sub"],
            "name": payload.get("name", ""),
            "picture": payload.get("picture", "")
        }
    )


@router.post("/logout")
async def logout(request: Request, response: Response):
    """
    Log out user by clearing cookies and blacklisting tokens.

    This endpoint:
    1. Blacklists the refresh token (prevents reuse)
    2. Clears the refresh token cookie

    Note: Access tokens in Authorization header should also be discarded
    by the client. They will be blacklisted if provided.

    Args:
        request: FastAPI request to get tokens
        response: FastAPI response to clear cookie

    Returns:
        Success message
    """
    # Blacklist refresh token from cookie
    refresh_token = request.cookies.get("refresh_token")
    if refresh_token:
        blacklist_token(refresh_token)

    # Blacklist access token if provided in header
    auth_header = request.headers.get("Authorization")
    if auth_header and auth_header.startswith("Bearer "):
        access_token = auth_header[7:]  # Remove "Bearer " prefix
        blacklist_token(access_token)

    # Clear the refresh token cookie
    response.delete_cookie(
        key="refresh_token",
        path="/api/auth"
    )

    return {"message": "Logged out successfully"}


@router.get("/me")
async def get_current_user(user: dict = Depends(jwt_bearer)):
    """
    Get current authenticated user info.

    Requires valid JWT token in Authorization header.

    Args:
        user: Decoded JWT payload (injected by jwt_bearer)

    Returns:
        User info from token
    """
    return {
        "email": user.get("sub"),
        "name": user.get("name", ""),
        "picture": user.get("picture", ""),
        "authenticated": True
    }


@router.get("/verify")
async def verify_token(user: dict = Depends(jwt_bearer)):
    """
    Verify if the current token is valid.

    Args:
        user: Decoded JWT payload (injected by jwt_bearer)

    Returns:
        Token verification status
    """
    return {
        "valid": True,
        "email": user.get("sub")
    }
