"""
FastAPI main application for TrendsPro Clean Architecture.
"""

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, JSONResponse
from contextlib import asynccontextmanager
import logging
from typing import Optional

from infrastructure.di.container import DIContainer
from .routers import query_router, conversation_router, health_router
from .middleware import LoggingMiddleware, ErrorHandlerMiddleware, RateLimitMiddleware

logger = logging.getLogger(__name__)

# Global container instance
_container: Optional[DIContainer] = None


def create_app(container: Optional[DIContainer] = None) -> FastAPI:
    """
    Create and configure the FastAPI application.
    
    Args:
        container: Optional DI container instance
    
    Returns:
        Configured FastAPI application
    """
    global _container
    
    # Use provided container or create new one
    if container:
        _container = container
    
    @asynccontextmanager
    async def lifespan(app: FastAPI):
        """Manage application lifecycle."""
        global _container
        
        logger.info("🚀 Starting TrendsPro FastAPI application...")
        
        # Initialize container if not provided
        if not _container:
            logger.info("Initializing DI container...")
            _container = DIContainer()
            await _container.initialize()
        
        # Store container in app state
        app.state.container = _container
        
        logger.info("✅ Application started successfully")
        
        yield
        
        # Cleanup
        logger.info("🛑 Shutting down application...")
        if _container and not container:  # Only shutdown if we created it
            await _container.shutdown()
        logger.info("✅ Application shut down successfully")
    
    # Create FastAPI app
    app = FastAPI(
        title="TrendsPro API",
        description="Natural Language Database Query System with Clean Architecture",
        version="3.0.0",
        lifespan=lifespan,
        docs_url="/docs",
        redoc_url="/redoc",
        openapi_url="/openapi.json"
    )
    
    # Configure CORS
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],  # Configure appropriately for production
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    # Add custom middleware
    app.add_middleware(ErrorHandlerMiddleware)
    app.add_middleware(LoggingMiddleware)
    # app.add_middleware(RateLimitMiddleware)  # Enable when ready
    
    # Include routers
    app.include_router(health_router.router, tags=["Health"])
    app.include_router(query_router.router, prefix="/api/v1", tags=["Queries"])
    app.include_router(conversation_router.router, prefix="/api/v1", tags=["Conversations"])
    
    # Root endpoint
    @app.get("/", response_class=HTMLResponse)
    async def root():
        """Root endpoint with welcome page."""
        html_content = """
        <!DOCTYPE html>
        <html>
        <head>
            <title>TrendsPro API</title>
            <style>
                body {
                    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
                    max-width: 800px;
                    margin: 0 auto;
                    padding: 2rem;
                    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                    min-height: 100vh;
                    color: white;
                }
                .container {
                    background: rgba(255, 255, 255, 0.1);
                    backdrop-filter: blur(10px);
                    border-radius: 20px;
                    padding: 3rem;
                    box-shadow: 0 8px 32px 0 rgba(31, 38, 135, 0.37);
                }
                h1 {
                    margin: 0 0 1rem 0;
                    font-size: 3rem;
                }
                .subtitle {
                    opacity: 0.9;
                    margin-bottom: 2rem;
                }
                .links {
                    display: flex;
                    gap: 1rem;
                    flex-wrap: wrap;
                    margin-top: 2rem;
                }
                a {
                    display: inline-block;
                    padding: 0.8rem 1.5rem;
                    background: rgba(255, 255, 255, 0.2);
                    color: white;
                    text-decoration: none;
                    border-radius: 10px;
                    transition: all 0.3s;
                }
                a:hover {
                    background: rgba(255, 255, 255, 0.3);
                    transform: translateY(-2px);
                }
                .status {
                    display: inline-block;
                    padding: 0.3rem 0.8rem;
                    background: #10b981;
                    border-radius: 20px;
                    font-size: 0.9rem;
                }
                .features {
                    margin-top: 2rem;
                    padding-top: 2rem;
                    border-top: 1px solid rgba(255, 255, 255, 0.2);
                }
                .feature {
                    margin: 1rem 0;
                    padding-left: 1.5rem;
                }
            </style>
        </head>
        <body>
            <div class="container">
                <h1>🚀 TrendsPro API</h1>
                <p class="subtitle">Natural Language Database Query System</p>
                <span class="status">✅ Clean Architecture Active</span>
                
                <div class="features">
                    <h3>Features:</h3>
                    <div class="feature">✨ Natural language queries in Spanish</div>
                    <div class="feature">🔄 Automatic MySQL/MongoDB routing</div>
                    <div class="feature">🤖 GPT-4o-mini integration</div>
                    <div class="feature">📊 Real-time streaming responses</div>
                    <div class="feature">🛡️ JWT authentication ready</div>
                    <div class="feature">📈 Built-in metrics and monitoring</div>
                </div>
                
                <div class="links">
                    <a href="/docs">📚 API Documentation</a>
                    <a href="/redoc">📖 ReDoc</a>
                    <a href="/health">🏥 Health Status</a>
                    <a href="/metrics">📊 Metrics</a>
                    <a href="/openapi.json">📄 OpenAPI Schema</a>
                </div>
            </div>
        </body>
        </html>
        """
        return HTMLResponse(content=html_content)
    
    # Metrics endpoint
    @app.get("/metrics")
    async def metrics():
        """Prometheus-compatible metrics endpoint."""
        # TODO: Implement proper metrics collection
        return JSONResponse({
            "requests_total": 0,
            "requests_duration_seconds": 0,
            "active_connections": 0,
            "database_queries_total": 0
        })
    
    # Version endpoint
    @app.get("/version")
    async def version():
        """Get API version information."""
        return {
            "name": "TrendsPro API",
            "version": "3.0.0",
            "architecture": "clean",
            "mode": "production"
        }
    
    return app


# Create default app instance for direct execution
app = create_app()


if __name__ == "__main__":
    import uvicorn
    import os
    
    # Run with uvicorn when executed directly
    uvicorn.run(
        "presentation.api.main:app",
        host=os.getenv("FASTAPI_HOST", "0.0.0.0"),
        port=int(os.getenv("FASTAPI_PORT", "8000")),
        reload=os.getenv("ENVIRONMENT") == "development",
        log_level=os.getenv("LOG_LEVEL", "info").lower()
    )