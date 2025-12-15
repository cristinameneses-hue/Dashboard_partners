"""
Flask to FastAPI Adapter for gradual migration.

This adapter allows both Flask and FastAPI to coexist during the migration period,
enabling a gradual route-by-route migration from the legacy Flask application
to the new FastAPI clean architecture.
"""

import asyncio
import json
import logging
from functools import wraps
from typing import Any, Dict, List, Optional, Callable
from urllib.parse import urljoin
import requests
from flask import Flask, Request, Response, jsonify, session
from werkzeug.exceptions import HTTPException
import jwt
from datetime import datetime, timedelta
import os

logger = logging.getLogger(__name__)


class FlaskToFastAPIAdapter:
    """
    Adapter for migrating from Flask to FastAPI.
    
    This adapter provides:
    - Route proxying from Flask to FastAPI
    - Session migration from Flask sessions to JWT tokens
    - Request/Response translation between frameworks
    - Gradual migration capabilities
    """
    
    def __init__(
        self,
        flask_app: Flask,
        fastapi_url: str = "http://localhost:8000",
        secret_key: Optional[str] = None
    ):
        """
        Initialize the adapter.
        
        Args:
            flask_app: The Flask application instance
            fastapi_url: Base URL of the FastAPI server
            secret_key: Secret key for JWT encoding (defaults to Flask secret key)
        """
        self.flask_app = flask_app
        self.fastapi_url = fastapi_url.rstrip('/')
        self.secret_key = secret_key or flask_app.secret_key or os.getenv('SECRET_KEY', 'default-secret-key')
        self.migrated_routes: List[str] = []
        self.session_mapping: Dict[str, str] = {}  # Flask session ID -> JWT token
        
        # Configure logging
        self._setup_logging()
        
    def _setup_logging(self):
        """Configure adapter-specific logging."""
        handler = logging.StreamHandler()
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - [ADAPTER] %(message)s'
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        logger.setLevel(logging.INFO)
    
    def route_to_fastapi(self, path: str, methods: List[str] = None):
        """
        Decorator to redirect specific Flask routes to FastAPI.
        
        Usage:
            @adapter.route_to_fastapi('/api/v1/query')
            def query_handler():
                pass  # This will never be called
        
        Args:
            path: The route path to migrate
            methods: HTTP methods to proxy (default: all)
        
        Returns:
            Decorator function
        """
        def decorator(f):
            @wraps(f)
            def wrapper(*args, **kwargs):
                return self._proxy_to_fastapi(path, methods)
            
            # Register the route as migrated
            self.migrated_routes.append(path)
            logger.info(f"Route {path} migrated to FastAPI")
            
            return wrapper
        return decorator
    
    def _proxy_to_fastapi(self, path: str, allowed_methods: List[str] = None):
        """
        Proxy a request from Flask to FastAPI.
        
        Args:
            path: The API path
            allowed_methods: Allowed HTTP methods
            
        Returns:
            Flask Response object
        """
        from flask import request
        
        # Check if method is allowed
        if allowed_methods and request.method not in allowed_methods:
            return jsonify({"error": "Method not allowed"}), 405
        
        # Build FastAPI URL
        fastapi_endpoint = urljoin(self.fastapi_url, path)
        
        # Convert Flask session to JWT if needed
        auth_header = self._get_auth_header()
        
        # Prepare headers
        headers = {
            'Content-Type': request.content_type or 'application/json',
            'Accept': 'application/json'
        }
        if auth_header:
            headers['Authorization'] = auth_header
        
        # Forward additional headers
        for header in ['X-Request-ID', 'X-User-Agent', 'X-Forwarded-For']:
            if header in request.headers:
                headers[header] = request.headers[header]
        
        try:
            # Prepare request data
            data = None
            json_data = None
            
            if request.is_json:
                json_data = request.get_json()
            elif request.form:
                data = request.form.to_dict()
            else:
                data = request.data
            
            # Make request to FastAPI
            response = requests.request(
                method=request.method,
                url=fastapi_endpoint,
                headers=headers,
                params=request.args.to_dict(),
                json=json_data,
                data=data,
                timeout=30,
                stream=True  # Enable streaming for large responses
            )
            
            # Handle streaming responses
            if 'text/event-stream' in response.headers.get('Content-Type', ''):
                return Response(
                    response.iter_content(chunk_size=1024),
                    content_type='text/event-stream',
                    status=response.status_code,
                    headers=dict(response.headers)
                )
            
            # Regular response
            return Response(
                response.content,
                status=response.status_code,
                headers=dict(response.headers)
            )
            
        except requests.RequestException as e:
            logger.error(f"Error proxying to FastAPI: {e}")
            return jsonify({
                "error": "Service temporarily unavailable",
                "details": str(e) if self.flask_app.debug else None
            }), 503
    
    def migrate_session(self, flask_session: Dict[str, Any]) -> str:
        """
        Convert Flask session to JWT token.
        
        Args:
            flask_session: Flask session dictionary
            
        Returns:
            JWT token string
        """
        # Extract relevant session data
        payload = {
            'user_id': flask_session.get('user_id'),
            'username': flask_session.get('username'),
            'email': flask_session.get('email'),
            'roles': flask_session.get('roles', ['user']),
            'authenticated': flask_session.get('authenticated', False),
            'iat': datetime.utcnow(),
            'exp': datetime.utcnow() + timedelta(hours=24)
        }
        
        # Remove None values
        payload = {k: v for k, v in payload.items() if v is not None}
        
        # Encode JWT
        token = jwt.encode(payload, self.secret_key, algorithm='HS256')
        
        # Store mapping if session has an ID
        if 'session_id' in flask_session:
            self.session_mapping[flask_session['session_id']] = token
        
        logger.info(f"Migrated session for user: {payload.get('username', 'unknown')}")
        return token
    
    def _get_auth_header(self) -> Optional[str]:
        """
        Get authorization header from Flask session.
        
        Returns:
            Authorization header value or None
        """
        from flask import session, request
        
        # Check if there's already a Bearer token in the request
        auth_header = request.headers.get('Authorization')
        if auth_header and auth_header.startswith('Bearer '):
            return auth_header
        
        # Try to migrate Flask session to JWT
        if session and session.get('authenticated'):
            token = self.migrate_session(dict(session))
            return f"Bearer {token}"
        
        return None
    
    def batch_migrate_routes(self, routes: List[Dict[str, Any]]):
        """
        Migrate multiple routes at once.
        
        Args:
            routes: List of route configurations
                Each dict should have: {'path': str, 'methods': List[str]}
        """
        for route_config in routes:
            path = route_config['path']
            methods = route_config.get('methods', ['GET', 'POST', 'PUT', 'DELETE'])
            
            # Create a proxy view function for this route
            def create_proxy_view(p, m):
                def proxy_view():
                    return self._proxy_to_fastapi(p, m)
                return proxy_view
            
            # Register the route with Flask
            view_func = create_proxy_view(path, methods)
            endpoint_name = f"proxy_{path.replace('/', '_')}"
            
            self.flask_app.add_url_rule(
                path,
                endpoint=endpoint_name,
                view_func=view_func,
                methods=methods
            )
            
            self.migrated_routes.append(path)
            logger.info(f"Batch migrated route: {path} with methods {methods}")
    
    def get_migration_status(self) -> Dict[str, Any]:
        """
        Get the current migration status.
        
        Returns:
            Dictionary with migration statistics
        """
        from flask import url_for
        
        # Get all Flask routes
        all_routes = []
        for rule in self.flask_app.url_map.iter_rules():
            if not rule.endpoint.startswith('static'):
                all_routes.append(rule.rule)
        
        # Calculate migration percentage
        total_routes = len(all_routes)
        migrated_count = len(self.migrated_routes)
        migration_percentage = (migrated_count / total_routes * 100) if total_routes > 0 else 0
        
        return {
            'total_routes': total_routes,
            'migrated_routes': migrated_count,
            'migration_percentage': round(migration_percentage, 2),
            'migrated_paths': self.migrated_routes,
            'remaining_paths': [r for r in all_routes if r not in self.migrated_routes],
            'fastapi_url': self.fastapi_url,
            'adapter_active': True
        }
    
    def enable_debug_mode(self):
        """Enable debug logging for the adapter."""
        logger.setLevel(logging.DEBUG)
        logger.debug("Debug mode enabled for Flask-FastAPI adapter")
    
    def health_check(self) -> Dict[str, Any]:
        """
        Check health of both Flask and FastAPI services.
        
        Returns:
            Health status dictionary
        """
        health_status = {
            'flask': 'unknown',
            'fastapi': 'unknown',
            'adapter': 'healthy',
            'timestamp': datetime.utcnow().isoformat()
        }
        
        # Check Flask (it's running if we're here)
        health_status['flask'] = 'healthy'
        
        # Check FastAPI
        try:
            response = requests.get(
                f"{self.fastapi_url}/health",
                timeout=5
            )
            if response.status_code == 200:
                health_status['fastapi'] = 'healthy'
            else:
                health_status['fastapi'] = 'unhealthy'
        except requests.RequestException:
            health_status['fastapi'] = 'unreachable'
        
        # Overall status
        if health_status['flask'] == 'healthy' and health_status['fastapi'] == 'healthy':
            health_status['overall'] = 'healthy'
        elif health_status['flask'] == 'healthy':
            health_status['overall'] = 'partial'
        else:
            health_status['overall'] = 'unhealthy'
        
        return health_status


class MigrationMiddleware:
    """
    Flask middleware for handling migration logic.
    """
    
    def __init__(self, app: Flask, adapter: FlaskToFastAPIAdapter):
        """
        Initialize middleware.
        
        Args:
            app: Flask application
            adapter: Flask to FastAPI adapter
        """
        self.app = app
        self.adapter = adapter
        self.init_app()
    
    def init_app(self):
        """Initialize middleware with the Flask app."""
        self.app.before_request(self.before_request)
        self.app.after_request(self.after_request)
    
    def before_request(self):
        """Execute before each request."""
        from flask import request, g
        
        # Store request start time
        g.request_start_time = datetime.utcnow()
        
        # Log migrated route access
        if request.path in self.adapter.migrated_routes:
            logger.debug(f"Accessing migrated route: {request.path}")
    
    def after_request(self, response: Response) -> Response:
        """
        Execute after each request.
        
        Args:
            response: Flask response object
            
        Returns:
            Modified response
        """
        from flask import g
        
        # Add migration headers
        response.headers['X-Migration-Status'] = 'active'
        response.headers['X-Served-By'] = 'flask-adapter'
        
        # Add timing header
        if hasattr(g, 'request_start_time'):
            duration = (datetime.utcnow() - g.request_start_time).total_seconds()
            response.headers['X-Response-Time'] = f"{duration:.3f}s"
        
        return response
