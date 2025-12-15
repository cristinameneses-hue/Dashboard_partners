#!/usr/bin/env python3
"""
Validation script for TrendsPro Clean Architecture migration.

This script performs comprehensive validation of the migration:
1. Checks all database connections
2. Validates API endpoints
3. Tests critical functionality
4. Generates validation report
"""

import os
import sys
import asyncio
import json
import time
from pathlib import Path
from typing import Dict, Any, List, Tuple
from datetime import datetime
import httpx
import mysql.connector
from pymongo import MongoClient
import openai
from colorama import init, Fore, Style

# Initialize colorama for colored output
init(autoreset=True)

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))


class ValidationResult:
    """Represents a validation result."""
    
    def __init__(self, name: str, passed: bool, message: str, details: Dict = None):
        self.name = name
        self.passed = passed
        self.message = message
        self.details = details or {}
        self.timestamp = datetime.utcnow()
    
    def __str__(self):
        status = f"{Fore.GREEN}✓ PASS{Style.RESET_ALL}" if self.passed else f"{Fore.RED}✗ FAIL{Style.RESET_ALL}"
        return f"{status} {self.name}: {self.message}"


class MigrationValidator:
    """Validates the migration to Clean Architecture."""
    
    def __init__(self):
        self.results: List[ValidationResult] = []
        self.start_time = time.time()
        
        # Configuration
        self.flask_url = os.getenv('FLASK_SERVICE_URL', 'http://localhost:5000')
        self.fastapi_url = os.getenv('FASTAPI_SERVICE_URL', 'http://localhost:8000')
        self.architecture_mode = os.getenv('ARCHITECTURE_MODE', 'legacy')
    
    async def validate_all(self) -> Tuple[bool, Dict[str, Any]]:
        """
        Run all validation checks.
        
        Returns:
            Tuple of (success, report_dict)
        """
        print(f"\n{Fore.CYAN}{'='*60}{Style.RESET_ALL}")
        print(f"{Fore.CYAN}TrendsPro Migration Validator{Style.RESET_ALL}")
        print(f"{Fore.CYAN}{'='*60}{Style.RESET_ALL}\n")
        
        print(f"Architecture Mode: {Fore.YELLOW}{self.architecture_mode}{Style.RESET_ALL}")
        print(f"Flask URL: {self.flask_url}")
        print(f"FastAPI URL: {self.fastapi_url}\n")
        
        # Run validation checks
        checks = [
            ("Environment Variables", self.check_environment_variables),
            ("MySQL Connection", self.check_mysql_connection),
            ("MongoDB Connection", self.check_mongodb_connection),
            ("OpenAI API", self.check_openai_api),
            ("Flask Endpoints", self.check_flask_endpoints),
            ("FastAPI Endpoints", self.check_fastapi_endpoints),
            ("Flask-FastAPI Compatibility", self.check_compatibility),
            ("Query Execution", self.check_query_execution),
            ("Streaming Response", self.check_streaming_response),
            ("Migration Status", self.check_migration_status)
        ]
        
        print(f"{Fore.BLUE}Running validation checks...{Style.RESET_ALL}\n")
        
        for name, check_func in checks:
            print(f"Checking {name}...", end=" ")
            try:
                result = await check_func()
                self.results.append(result)
                print(result)
            except Exception as e:
                result = ValidationResult(
                    name=name,
                    passed=False,
                    message=f"Check failed with error: {str(e)}"
                )
                self.results.append(result)
                print(result)
        
        # Generate report
        report = self.generate_report()
        
        # Determine overall success
        all_passed = all(r.passed for r in self.results)
        
        return all_passed, report
    
    async def check_environment_variables(self) -> ValidationResult:
        """Check required environment variables."""
        required_vars = [
            'OPENAI_API_KEY',
            'DB_TRENDS_URL',
            'MONGO_LUDAFARMA_URL'
        ]
        
        missing = []
        for var in required_vars:
            if not os.getenv(var):
                missing.append(var)
        
        if missing:
            return ValidationResult(
                name="Environment Variables",
                passed=False,
                message=f"Missing variables: {', '.join(missing)}",
                details={'missing': missing}
            )
        
        return ValidationResult(
            name="Environment Variables",
            passed=True,
            message="All required variables present"
        )
    
    async def check_mysql_connection(self) -> ValidationResult:
        """Check MySQL database connection."""
        try:
            # Parse connection string
            mysql_url = os.getenv('DB_TRENDS_URL', '')
            if not mysql_url:
                return ValidationResult(
                    name="MySQL Connection",
                    passed=False,
                    message="DB_TRENDS_URL not configured"
                )
            
            # Simple connection test (would need proper parsing in production)
            # This is a simplified version
            conn = mysql.connector.connect(
                host=os.getenv('MYSQL_HOST', '127.0.0.1'),
                port=int(os.getenv('MYSQL_PORT', '3307')),
                user=os.getenv('MYSQL_USER', 'root'),
                password=os.getenv('MYSQL_PASSWORD', ''),
                database=os.getenv('MYSQL_DATABASE', 'trends_consolidado')
            )
            
            cursor = conn.cursor()
            cursor.execute("SELECT 1")
            cursor.fetchone()
            cursor.close()
            conn.close()
            
            return ValidationResult(
                name="MySQL Connection",
                passed=True,
                message="Successfully connected to MySQL"
            )
            
        except Exception as e:
            return ValidationResult(
                name="MySQL Connection",
                passed=False,
                message=f"Connection failed: {str(e)}"
            )
    
    async def check_mongodb_connection(self) -> ValidationResult:
        """Check MongoDB database connection."""
        try:
            mongo_url = os.getenv('MONGO_LUDAFARMA_URL', '')
            if not mongo_url:
                return ValidationResult(
                    name="MongoDB Connection",
                    passed=False,
                    message="MONGO_LUDAFARMA_URL not configured"
                )
            
            client = MongoClient(mongo_url, serverSelectionTimeoutMS=5000)
            # Ping to verify connection
            client.admin.command('ping')
            client.close()
            
            return ValidationResult(
                name="MongoDB Connection",
                passed=True,
                message="Successfully connected to MongoDB"
            )
            
        except Exception as e:
            return ValidationResult(
                name="MongoDB Connection",
                passed=False,
                message=f"Connection failed: {str(e)}"
            )
    
    async def check_openai_api(self) -> ValidationResult:
        """Check OpenAI API connectivity."""
        try:
            api_key = os.getenv('OPENAI_API_KEY')
            if not api_key:
                return ValidationResult(
                    name="OpenAI API",
                    passed=False,
                    message="OPENAI_API_KEY not configured"
                )
            
            # Test with a minimal API call
            client = openai.OpenAI(api_key=api_key)
            response = client.models.list()
            
            # Check if we can access GPT-4o-mini
            models = [m.id for m in response.data]
            if 'gpt-4o-mini' in models or any('gpt-4' in m for m in models):
                return ValidationResult(
                    name="OpenAI API",
                    passed=True,
                    message="Successfully connected to OpenAI API"
                )
            else:
                return ValidationResult(
                    name="OpenAI API",
                    passed=True,
                    message="Connected but GPT-4o-mini not available",
                    details={'available_models': models[:5]}
                )
            
        except Exception as e:
            return ValidationResult(
                name="OpenAI API",
                passed=False,
                message=f"API check failed: {str(e)}"
            )
    
    async def check_flask_endpoints(self) -> ValidationResult:
        """Check Flask application endpoints."""
        if self.architecture_mode == 'clean':
            return ValidationResult(
                name="Flask Endpoints",
                passed=True,
                message="Skipped (running in clean mode)"
            )
        
        try:
            async with httpx.AsyncClient() as client:
                # Check main endpoint
                response = await client.get(f"{self.flask_url}/", timeout=5)
                
                if response.status_code in [200, 302]:  # 302 for redirect to login
                    return ValidationResult(
                        name="Flask Endpoints",
                        passed=True,
                        message=f"Flask responding at {self.flask_url}"
                    )
                else:
                    return ValidationResult(
                        name="Flask Endpoints",
                        passed=False,
                        message=f"Flask returned status {response.status_code}"
                    )
                    
        except Exception as e:
            return ValidationResult(
                name="Flask Endpoints",
                passed=False,
                message=f"Cannot reach Flask: {str(e)}"
            )
    
    async def check_fastapi_endpoints(self) -> ValidationResult:
        """Check FastAPI application endpoints."""
        if self.architecture_mode == 'legacy':
            return ValidationResult(
                name="FastAPI Endpoints",
                passed=True,
                message="Skipped (running in legacy mode)"
            )
        
        try:
            async with httpx.AsyncClient() as client:
                # Check health endpoint
                response = await client.get(f"{self.fastapi_url}/health", timeout=5)
                
                if response.status_code == 200:
                    data = response.json()
                    return ValidationResult(
                        name="FastAPI Endpoints",
                        passed=True,
                        message=f"FastAPI healthy at {self.fastapi_url}",
                        details=data
                    )
                else:
                    return ValidationResult(
                        name="FastAPI Endpoints",
                        passed=False,
                        message=f"FastAPI returned status {response.status_code}"
                    )
                    
        except Exception as e:
            return ValidationResult(
                name="FastAPI Endpoints",
                passed=False,
                message=f"Cannot reach FastAPI: {str(e)}"
            )
    
    async def check_compatibility(self) -> ValidationResult:
        """Check Flask-FastAPI compatibility in transitional mode."""
        if self.architecture_mode != 'transitional':
            return ValidationResult(
                name="Flask-FastAPI Compatibility",
                passed=True,
                message=f"Skipped (not in transitional mode)"
            )
        
        try:
            async with httpx.AsyncClient() as client:
                # Check adapter health endpoint
                response = await client.get(f"{self.flask_url}/adapter-health", timeout=5)
                
                if response.status_code == 200:
                    data = response.json()
                    if data.get('overall') == 'healthy':
                        return ValidationResult(
                            name="Flask-FastAPI Compatibility",
                            passed=True,
                            message="Adapter is healthy",
                            details=data
                        )
                    else:
                        return ValidationResult(
                            name="Flask-FastAPI Compatibility",
                            passed=False,
                            message=f"Adapter status: {data.get('overall')}",
                            details=data
                        )
                else:
                    return ValidationResult(
                        name="Flask-FastAPI Compatibility",
                        passed=False,
                        message="Adapter health endpoint not available"
                    )
                    
        except Exception as e:
            return ValidationResult(
                name="Flask-FastAPI Compatibility",
                passed=False,
                message=f"Compatibility check failed: {str(e)}"
            )
    
    async def check_query_execution(self) -> ValidationResult:
        """Check query execution functionality."""
        endpoint = self.fastapi_url if self.architecture_mode == 'clean' else self.flask_url
        
        try:
            async with httpx.AsyncClient() as client:
                # Execute a simple query
                response = await client.post(
                    f"{endpoint}/query",
                    json={
                        "question": "SELECT 1",
                        "use_chatgpt": False
                    },
                    timeout=10
                )
                
                if response.status_code == 200:
                    return ValidationResult(
                        name="Query Execution",
                        passed=True,
                        message="Query executed successfully"
                    )
                else:
                    return ValidationResult(
                        name="Query Execution",
                        passed=False,
                        message=f"Query returned status {response.status_code}"
                    )
                    
        except Exception as e:
            return ValidationResult(
                name="Query Execution",
                passed=False,
                message=f"Query execution failed: {str(e)}"
            )
    
    async def check_streaming_response(self) -> ValidationResult:
        """Check streaming response functionality."""
        endpoint = self.fastapi_url if self.architecture_mode == 'clean' else self.flask_url
        
        try:
            async with httpx.AsyncClient() as client:
                # Test streaming endpoint
                response = await client.post(
                    f"{endpoint}/query_stream",
                    json={
                        "question": "Test streaming",
                        "use_chatgpt": False
                    },
                    timeout=10
                )
                
                if response.status_code == 200:
                    return ValidationResult(
                        name="Streaming Response",
                        passed=True,
                        message="Streaming endpoint available"
                    )
                else:
                    return ValidationResult(
                        name="Streaming Response",
                        passed=False,
                        message=f"Streaming returned status {response.status_code}"
                    )
                    
        except Exception as e:
            # Streaming might not be available in all modes
            return ValidationResult(
                name="Streaming Response",
                passed=False,
                message=f"Streaming check failed: {str(e)}"
            )
    
    async def check_migration_status(self) -> ValidationResult:
        """Check migration status if in transitional mode."""
        if self.architecture_mode != 'transitional':
            return ValidationResult(
                name="Migration Status",
                passed=True,
                message="Not applicable for current mode"
            )
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(f"{self.flask_url}/migration-status", timeout=5)
                
                if response.status_code == 200:
                    data = response.json()
                    percentage = data.get('migration_percentage', 0)
                    
                    return ValidationResult(
                        name="Migration Status",
                        passed=True,
                        message=f"Migration {percentage}% complete",
                        details=data
                    )
                else:
                    return ValidationResult(
                        name="Migration Status",
                        passed=False,
                        message="Migration status endpoint not available"
                    )
                    
        except Exception as e:
            return ValidationResult(
                name="Migration Status",
                passed=False,
                message=f"Status check failed: {str(e)}"
            )
    
    def generate_report(self) -> Dict[str, Any]:
        """Generate validation report."""
        total_checks = len(self.results)
        passed_checks = sum(1 for r in self.results if r.passed)
        failed_checks = total_checks - passed_checks
        success_rate = (passed_checks / total_checks * 100) if total_checks > 0 else 0
        
        report = {
            'timestamp': datetime.utcnow().isoformat(),
            'architecture_mode': self.architecture_mode,
            'duration_seconds': time.time() - self.start_time,
            'summary': {
                'total_checks': total_checks,
                'passed': passed_checks,
                'failed': failed_checks,
                'success_rate': round(success_rate, 2)
            },
            'checks': [
                {
                    'name': r.name,
                    'passed': r.passed,
                    'message': r.message,
                    'details': r.details,
                    'timestamp': r.timestamp.isoformat()
                }
                for r in self.results
            ]
        }
        
        return report
    
    def print_summary(self, report: Dict[str, Any]):
        """Print validation summary."""
        print(f"\n{Fore.CYAN}{'='*60}{Style.RESET_ALL}")
        print(f"{Fore.CYAN}VALIDATION SUMMARY{Style.RESET_ALL}")
        print(f"{Fore.CYAN}{'='*60}{Style.RESET_ALL}\n")
        
        summary = report['summary']
        
        # Overall status
        if summary['success_rate'] == 100:
            print(f"{Fore.GREEN}✅ ALL CHECKS PASSED!{Style.RESET_ALL}")
        elif summary['success_rate'] >= 80:
            print(f"{Fore.YELLOW}⚠️  MOSTLY PASSING ({summary['success_rate']}%){Style.RESET_ALL}")
        else:
            print(f"{Fore.RED}❌ VALIDATION FAILED ({summary['success_rate']}%){Style.RESET_ALL}")
        
        print(f"\nTotal Checks: {summary['total_checks']}")
        print(f"Passed: {Fore.GREEN}{summary['passed']}{Style.RESET_ALL}")
        print(f"Failed: {Fore.RED}{summary['failed']}{Style.RESET_ALL}")
        print(f"Duration: {report['duration_seconds']:.2f} seconds")
        
        # Failed checks details
        if summary['failed'] > 0:
            print(f"\n{Fore.YELLOW}Failed Checks:{Style.RESET_ALL}")
            for check in report['checks']:
                if not check['passed']:
                    print(f"  - {check['name']}: {check['message']}")
        
        # Recommendations
        print(f"\n{Fore.CYAN}Recommendations:{Style.RESET_ALL}")
        if summary['success_rate'] == 100:
            if self.architecture_mode == 'legacy':
                print("  ✓ System is healthy. Consider migrating to transitional mode.")
            elif self.architecture_mode == 'transitional':
                print("  ✓ Migration is progressing well. Monitor for a few days before moving to clean mode.")
            else:
                print("  ✓ Clean architecture is fully operational!")
        else:
            print("  ⚠ Fix the failed checks before proceeding with migration")
            print("  ⚠ Check logs for detailed error information")
            if self.architecture_mode != 'legacy':
                print("  ⚠ Consider rolling back to legacy mode if issues persist")


async def main():
    """Main entry point for validation."""
    print(f"{Fore.CYAN}TrendsPro Migration Validator{Style.RESET_ALL}")
    print("="*40)
    
    # Create validator
    validator = MigrationValidator()
    
    # Run validation
    success, report = await validator.validate_all()
    
    # Print summary
    validator.print_summary(report)
    
    # Save report to file
    report_file = f"validation_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(report_file, 'w') as f:
        json.dump(report, f, indent=2)
    
    print(f"\n📄 Full report saved to: {Fore.YELLOW}{report_file}{Style.RESET_ALL}")
    
    # Exit with appropriate code
    sys.exit(0 if success else 1)


if __name__ == '__main__':
    asyncio.run(main())
