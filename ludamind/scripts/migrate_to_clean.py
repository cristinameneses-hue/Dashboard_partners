#!/usr/bin/env python3
"""
Migration script to transition from Flask legacy to Clean Architecture.

This script handles the transition between three architecture modes:
- legacy: Original Flask monolith
- transitional: Both Flask and FastAPI running with adapter
- clean: Pure FastAPI with Clean Architecture
"""

import os
import sys
import asyncio
import logging
from pathlib import Path
from typing import Optional, Dict, Any
import subprocess
import signal
from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor
import json
import time

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class ArchitectureMigrator:
    """Handles migration between different architecture modes."""
    
    MODES = {
        'legacy': 'Flask monolith (original)',
        'transitional': 'Flask + FastAPI with adapter',
        'clean': 'Pure FastAPI with Clean Architecture'
    }
    
    def __init__(self):
        """Initialize the migrator."""
        self.mode = os.getenv('ARCHITECTURE_MODE', 'legacy').lower()
        self.processes = []
        self.executor = ThreadPoolExecutor(max_workers=2)
        
        # Validate mode
        if self.mode not in self.MODES:
            raise ValueError(f"Invalid ARCHITECTURE_MODE: {self.mode}. Must be one of: {list(self.MODES.keys())}")
        
        logger.info(f"Initializing migration in '{self.mode}' mode: {self.MODES[self.mode]}")
        
        # Setup signal handlers for graceful shutdown
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)
    
    def _signal_handler(self, signum, frame):
        """Handle shutdown signals gracefully."""
        logger.info(f"Received signal {signum}, shutting down gracefully...")
        self.shutdown()
        sys.exit(0)
    
    def run(self):
        """Run the appropriate architecture based on mode."""
        logger.info(f"Starting application in {self.mode} mode...")
        
        if self.mode == 'legacy':
            self._run_legacy()
        elif self.mode == 'transitional':
            self._run_transitional()
        elif self.mode == 'clean':
            self._run_clean()
    
    def _run_legacy(self):
        """Run the legacy Flask application."""
        logger.info("Starting legacy Flask application...")
        
        try:
            # Import and run Flask app
            from web.server_unified import app
            
            # Get configuration
            host = os.getenv('FLASK_HOST', '0.0.0.0')
            port = int(os.getenv('FLASK_PORT', '5000'))
            debug = os.getenv('FLASK_DEBUG', 'False').lower() == 'true'
            
            logger.info(f"Flask server starting on {host}:{port} (debug={debug})")
            
            # Run Flask
            app.run(
                host=host,
                port=port,
                debug=debug,
                use_reloader=False  # Disable reloader when running through this script
            )
            
        except ImportError as e:
            logger.error(f"Failed to import Flask app: {e}")
            logger.error("Make sure you're in the correct directory and dependencies are installed")
            sys.exit(1)
        except Exception as e:
            logger.error(f"Failed to start Flask: {e}")
            sys.exit(1)
    
    def _run_transitional(self):
        """Run both Flask and FastAPI with the adapter."""
        logger.info("Starting transitional mode (Flask + FastAPI)...")
        
        try:
            # Start FastAPI in a separate process
            fastapi_process = self._start_fastapi_process()
            self.processes.append(fastapi_process)
            
            # Wait a bit for FastAPI to start
            time.sleep(3)
            
            # Check if FastAPI is running
            if not self._check_fastapi_health():
                logger.error("FastAPI failed to start, falling back to legacy mode")
                self._run_legacy()
                return
            
            # Start Flask with adapter
            self._start_flask_with_adapter()
            
        except Exception as e:
            logger.error(f"Failed to start transitional mode: {e}")
            self.shutdown()
            sys.exit(1)
    
    def _run_clean(self):
        """Run the clean FastAPI application with Bootstrap."""
        logger.info("Starting clean FastAPI application with Bootstrap...")
        
        try:
            # Use asyncio to run the async bootstrap
            asyncio.run(self._run_clean_async())
            
        except Exception as e:
            logger.error(f"Failed to start clean architecture: {e}")
            sys.exit(1)
    
    async def _run_clean_async(self):
        """Async runner for clean architecture."""
        from infrastructure.bootstrap import Bootstrap, BootstrapConfig
        
        # Create bootstrap configuration
        config = BootstrapConfig(
            app_name="TrendsPro",
            version="2.0.0",
            environment=os.getenv('ENVIRONMENT', 'development'),
            enable_health_checks=os.getenv('ENABLE_HEALTH_CHECKS', 'true').lower() == 'true',
            enable_metrics=os.getenv('ENABLE_METRICS', 'true').lower() == 'true',
            enable_cache_warming=os.getenv('ENABLE_CACHE_WARMING', 'false').lower() == 'true',
            log_level=os.getenv('LOG_LEVEL', 'INFO')
        )
        
        # Initialize bootstrap
        bootstrap = Bootstrap(config)
        
        try:
            # Start the system
            logger.info("Initializing Bootstrap system...")
            await bootstrap.initialize()
            
            logger.info("Starting FastAPI application...")
            await bootstrap.start()
            
            # Import and run FastAPI app
            from presentation.api.main import app
            import uvicorn
            
            # Get configuration
            host = os.getenv('FASTAPI_HOST', '0.0.0.0')
            port = int(os.getenv('FASTAPI_PORT', '8000'))
            
            # Run FastAPI with uvicorn
            config = uvicorn.Config(
                app,
                host=host,
                port=port,
                log_level=os.getenv('LOG_LEVEL', 'info').lower(),
                reload=False  # Disable reload in production
            )
            server = uvicorn.Server(config)
            await server.serve()
            
        except Exception as e:
            logger.error(f"Bootstrap initialization failed: {e}")
            await bootstrap.shutdown()
            raise
    
    def _start_fastapi_process(self) -> subprocess.Popen:
        """Start FastAPI in a separate process."""
        logger.info("Starting FastAPI server in subprocess...")
        
        # Prepare command
        cmd = [
            sys.executable,
            '-m',
            'uvicorn',
            'presentation.api.main:app',
            '--host', os.getenv('FASTAPI_HOST', '0.0.0.0'),
            '--port', os.getenv('FASTAPI_PORT', '8000'),
            '--log-level', os.getenv('LOG_LEVEL', 'info').lower()
        ]
        
        # Start process
        process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        
        logger.info(f"FastAPI process started with PID: {process.pid}")
        return process
    
    def _check_fastapi_health(self, retries: int = 3) -> bool:
        """Check if FastAPI is healthy."""
        import requests
        
        fastapi_url = f"http://{os.getenv('FASTAPI_HOST', 'localhost')}:{os.getenv('FASTAPI_PORT', '8000')}"
        
        for i in range(retries):
            try:
                response = requests.get(f"{fastapi_url}/health", timeout=5)
                if response.status_code == 200:
                    logger.info("FastAPI health check passed")
                    return True
            except requests.RequestException:
                logger.warning(f"FastAPI health check attempt {i+1}/{retries} failed")
                time.sleep(2)
        
        return False
    
    def _start_flask_with_adapter(self):
        """Start Flask with the migration adapter."""
        logger.info("Starting Flask with migration adapter...")
        
        try:
            from web.server_unified import app
            from infrastructure.adapters import FlaskToFastAPIAdapter, MigrationMiddleware
            
            # Initialize adapter
            fastapi_url = f"http://{os.getenv('FASTAPI_HOST', 'localhost')}:{os.getenv('FASTAPI_PORT', '8000')}"
            adapter = FlaskToFastAPIAdapter(app, fastapi_url)
            
            # Initialize middleware
            middleware = MigrationMiddleware(app, adapter)
            
            # Get routes to migrate from environment
            migration_routes = os.getenv('MIGRATION_ROUTES', '').split(',')
            if migration_routes and migration_routes[0]:
                routes_config = []
                for route in migration_routes:
                    route = route.strip()
                    if route:
                        routes_config.append({
                            'path': route,
                            'methods': ['GET', 'POST', 'PUT', 'DELETE']
                        })
                
                # Migrate routes
                adapter.batch_migrate_routes(routes_config)
                logger.info(f"Migrated {len(routes_config)} routes to FastAPI")
            
            # Add migration status endpoint
            @app.route('/migration-status')
            def migration_status():
                return adapter.get_migration_status()
            
            # Add health check endpoint
            @app.route('/adapter-health')
            def adapter_health():
                return adapter.health_check()
            
            # Run Flask
            host = os.getenv('FLASK_HOST', '0.0.0.0')
            port = int(os.getenv('FLASK_PORT', '5000'))
            debug = os.getenv('FLASK_DEBUG', 'False').lower() == 'true'
            
            logger.info(f"Flask server with adapter starting on {host}:{port}")
            
            app.run(
                host=host,
                port=port,
                debug=debug,
                use_reloader=False
            )
            
        except Exception as e:
            logger.error(f"Failed to start Flask with adapter: {e}")
            raise
    
    def shutdown(self):
        """Shutdown all processes gracefully."""
        logger.info("Shutting down all processes...")
        
        # Terminate subprocesses
        for process in self.processes:
            if process.poll() is None:  # Process is still running
                logger.info(f"Terminating process {process.pid}")
                process.terminate()
                try:
                    process.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    logger.warning(f"Process {process.pid} didn't terminate, killing...")
                    process.kill()
        
        # Shutdown executor
        self.executor.shutdown(wait=True)
        logger.info("All processes shut down")
    
    def validate_environment(self) -> Dict[str, Any]:
        """Validate environment configuration."""
        validation = {
            'mode': self.mode,
            'valid': True,
            'errors': [],
            'warnings': []
        }
        
        # Check required environment variables
        required_vars = {
            'legacy': [],
            'transitional': ['FASTAPI_HOST', 'FASTAPI_PORT'],
            'clean': []
        }
        
        for var in required_vars.get(self.mode, []):
            if not os.getenv(var):
                validation['errors'].append(f"Missing required environment variable: {var}")
                validation['valid'] = False
        
        # Check database configuration
        if not os.getenv('DB_TRENDS_URL') and not os.getenv('MYSQL_HOST'):
            validation['warnings'].append("No MySQL database configured")
        
        if not os.getenv('MONGO_LUDAFARMA_URL') and not os.getenv('MONGODB_URI'):
            validation['warnings'].append("No MongoDB database configured")
        
        if not os.getenv('OPENAI_API_KEY'):
            validation['errors'].append("OPENAI_API_KEY not configured")
            validation['valid'] = False
        
        return validation


def main():
    """Main entry point for the migration script."""
    print("""
    ╔══════════════════════════════════════════════════════════╗
    ║         TrendsPro Architecture Migration Tool            ║
    ╠══════════════════════════════════════════════════════════╣
    ║  Modes:                                                  ║
    ║  - legacy: Original Flask monolith                      ║
    ║  - transitional: Flask + FastAPI with adapter           ║
    ║  - clean: Pure FastAPI with Clean Architecture          ║
    ╚══════════════════════════════════════════════════════════╝
    """)
    
    # Create migrator
    migrator = ArchitectureMigrator()
    
    # Validate environment
    validation = migrator.validate_environment()
    
    print(f"\n📋 Configuration:")
    print(f"   Mode: {validation['mode']}")
    print(f"   Environment: {os.getenv('ENVIRONMENT', 'development')}")
    
    if validation['errors']:
        print("\n❌ Errors found:")
        for error in validation['errors']:
            print(f"   - {error}")
    
    if validation['warnings']:
        print("\n⚠️  Warnings:")
        for warning in validation['warnings']:
            print(f"   - {warning}")
    
    if not validation['valid']:
        print("\n❌ Configuration validation failed. Please fix errors and try again.")
        sys.exit(1)
    
    print("\n✅ Configuration valid. Starting migration...\n")
    
    try:
        # Run the migrator
        migrator.run()
    except KeyboardInterrupt:
        print("\n\n🛑 Migration interrupted by user")
        migrator.shutdown()
    except Exception as e:
        print(f"\n❌ Migration failed: {e}")
        migrator.shutdown()
        sys.exit(1)


if __name__ == '__main__':
    main()