from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from collections import defaultdict
from datetime import datetime, timedelta
import asyncio
import logging

from app.api import ecommerce, shortage, pharmacies, auth, ukie
from app.core.database import connect_to_mongo, close_mongo_connection
from app.core.config import get_settings

settings = get_settings()

# Configure logging
logging.basicConfig(level=logging.INFO if settings.environment == "production" else logging.DEBUG)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Dashboard Partners API",
    description="API para métricas de partners de LudaFarma",
    version="2.0.0",
    # Disable docs in production for security
    docs_url=None if settings.environment == "production" else "/docs",
    redoc_url=None if settings.environment == "production" else "/redoc"
)

# =============================================================================
# Rate Limiting (in-memory, simple implementation)
# =============================================================================
class RateLimiter:
    def __init__(self, requests_per_minute: int = 60):
        self.requests_per_minute = requests_per_minute
        self.requests = defaultdict(list)
        self._lock = asyncio.Lock()

    async def is_allowed(self, client_ip: str) -> bool:
        async with self._lock:
            now = datetime.now()
            minute_ago = now - timedelta(minutes=1)

            # Clean old requests
            self.requests[client_ip] = [
                req_time for req_time in self.requests[client_ip]
                if req_time > minute_ago
            ]

            if len(self.requests[client_ip]) >= self.requests_per_minute:
                return False

            self.requests[client_ip].append(now)
            return True

rate_limiter = RateLimiter(requests_per_minute=100)

# =============================================================================
# Global Error Handler - Hide details in production
# =============================================================================
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    # Log the full error for debugging
    logger.error(f"Unhandled exception: {exc}", exc_info=True)

    # Return generic error in production, detailed in development
    if settings.environment == "production":
        return JSONResponse(
            status_code=500,
            content={"detail": "Internal server error"}
        )
    else:
        return JSONResponse(
            status_code=500,
            content={"detail": str(exc), "type": type(exc).__name__}
        )

@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.detail}
    )

# CORS configuration - Use settings from environment
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type", "X-Requested-With"],
)


# =============================================================================
# Rate Limiting Middleware
# =============================================================================
@app.middleware("http")
async def rate_limit_middleware(request: Request, call_next):
    # Get client IP (consider X-Forwarded-For for proxied requests)
    forwarded = request.headers.get("X-Forwarded-For")
    client_ip = forwarded.split(",")[0].strip() if forwarded else request.client.host

    # Skip rate limiting for health checks
    if request.url.path in ["/health", "/"]:
        return await call_next(request)

    if not await rate_limiter.is_allowed(client_ip):
        logger.warning(f"Rate limit exceeded for IP: {client_ip}")
        return JSONResponse(
            status_code=429,
            content={"detail": "Too many requests. Please try again later."}
        )

    return await call_next(request)

# =============================================================================
# Security Headers Middleware
# =============================================================================
@app.middleware("http")
async def add_security_headers(request: Request, call_next):
    response = await call_next(request)

    # Basic security headers
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    response.headers["Permissions-Policy"] = "geolocation=(), microphone=(), camera=()"

    # Production-only headers
    if settings.environment == "production":
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains; preload"
        # CSP for API (restrictive since it's not serving HTML)
        response.headers["Content-Security-Policy"] = "default-src 'none'; frame-ancestors 'none'"

    return response

# Event handlers
@app.on_event("startup")
async def startup_db_client():
    try:
        await connect_to_mongo()
        logger.info("Successfully connected to MongoDB")
    except Exception as e:
        error_msg = f"Failed to connect to MongoDB: {e}"
        logger.error(error_msg)

        # In production, fail fast - don't start without database
        if settings.environment == "production":
            raise RuntimeError(
                f"CRITICAL: {error_msg}. "
                "Server cannot start without database connection in production."
            )
        else:
            # Development: warn but continue (allows testing without DB)
            logger.warning(
                "Server starting without database connection - "
                "some features will be unavailable. "
                "This is only allowed in development mode."
            )

@app.on_event("shutdown")
async def shutdown_db_client():
    try:
        await close_mongo_connection()
    except Exception:
        pass

# Include routers
app.include_router(
    ecommerce.router, 
    prefix="/api/ecommerce", 
    tags=["Ecommerce"]
)
app.include_router(
    shortage.router, 
    prefix="/api/shortage", 
    tags=["Shortage"]
)
app.include_router(
    pharmacies.router,
    prefix="/api/pharmacies",
    tags=["Pharmacies"]
)
app.include_router(
    auth.router,
    prefix="/api",
    tags=["Authentication"]
)
app.include_router(
    ukie.router,
    prefix="/api/ukie",
    tags=["Ukie"]
)

@app.get("/")
async def root():
    return {
        "message": "Dashboard Partners API - LudaFarma",
        "version": "2.0.0",
        "endpoints": {
            "auth": "/api/auth",
            "ecommerce": "/api/ecommerce",
            "shortage": "/api/shortage",
            "pharmacies": "/api/pharmacies",
            "docs": "/docs"
        }
    }

@app.get("/health")
async def health_check():
    return {"status": "healthy"}
