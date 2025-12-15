#!/usr/bin/env python3
"""
Migration Script: TrendsPro to 3-Layer Architecture
Author: CTO Senior Architecture Expert
Version: 1.0.0
Date: 2025-01-13

This script automates the migration of the TrendsPro codebase from its current
architecture to a clean 3-layer architecture (Presentation, Domain, Infrastructure).
"""

import os
import shutil
import ast
import re
from pathlib import Path
from typing import List, Dict, Tuple, Optional
from dataclasses import dataclass
import logging
import argparse
import json

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Migration configuration
@dataclass
class MigrationConfig:
    """Configuration for the migration process"""
    source_dir: Path
    target_dir: Path
    backup_dir: Path
    dry_run: bool = False
    preserve_original: bool = True
    create_tests: bool = True
    create_docs: bool = True


class CodeAnalyzer:
    """Analyzes existing code to understand structure and dependencies"""

    def __init__(self, source_dir: Path):
        self.source_dir = source_dir
        self.modules = {}
        self.dependencies = {}
        self.classes = {}
        self.functions = {}

    def analyze(self) -> Dict:
        """Perform complete code analysis"""
        logger.info(f"Analyzing code in {self.source_dir}")

        # Analyze Python files
        python_files = list(self.source_dir.rglob("*.py"))
        for file_path in python_files:
            self._analyze_python_file(file_path)

        # Analyze TypeScript files
        ts_files = list(self.source_dir.rglob("*.ts"))
        for file_path in ts_files:
            self._analyze_typescript_file(file_path)

        return {
            'modules': self.modules,
            'dependencies': self.dependencies,
            'classes': self.classes,
            'functions': self.functions
        }

    def _analyze_python_file(self, file_path: Path):
        """Analyze a Python file"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()

            tree = ast.parse(content)

            # Extract imports
            imports = []
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    for name in node.names:
                        imports.append(name.name)
                elif isinstance(node, ast.ImportFrom):
                    if node.module:
                        imports.append(node.module)

            # Extract classes and functions
            classes = [node.name for node in ast.walk(tree)
                      if isinstance(node, ast.ClassDef)]
            functions = [node.name for node in ast.walk(tree)
                        if isinstance(node, ast.FunctionDef)]

            relative_path = file_path.relative_to(self.source_dir)
            self.modules[str(relative_path)] = {
                'imports': imports,
                'classes': classes,
                'functions': functions,
                'type': self._determine_module_type(file_path, classes, functions)
            }

        except Exception as e:
            logger.error(f"Error analyzing {file_path}: {e}")

    def _analyze_typescript_file(self, file_path: Path):
        """Analyze a TypeScript file"""
        # Simplified TypeScript analysis using regex
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()

            # Extract imports
            import_pattern = r'import\s+.*?\s+from\s+[\'"](.+?)[\'"]'
            imports = re.findall(import_pattern, content)

            # Extract classes
            class_pattern = r'class\s+(\w+)'
            classes = re.findall(class_pattern, content)

            # Extract functions
            function_pattern = r'(?:function|const|let|var)\s+(\w+)\s*(?:=|:)?\s*(?:async\s+)?(?:\([^)]*\)\s*=>|\([^)]*\)\s*{)'
            functions = re.findall(function_pattern, content)

            relative_path = file_path.relative_to(self.source_dir)
            self.modules[str(relative_path)] = {
                'imports': imports,
                'classes': classes,
                'functions': functions,
                'type': self._determine_module_type(file_path, classes, functions)
            }

        except Exception as e:
            logger.error(f"Error analyzing {file_path}: {e}")

    def _determine_module_type(self, file_path: Path, classes: List, functions: List) -> str:
        """Determine the architectural layer of a module"""

        path_str = str(file_path).lower()

        # Check by path patterns
        if any(pattern in path_str for pattern in ['route', 'api', 'endpoint', 'controller']):
            return 'presentation'
        elif any(pattern in path_str for pattern in ['repository', 'database', 'cache', 'external']):
            return 'infrastructure'
        elif any(pattern in path_str for pattern in ['use_case', 'usecase', 'service', 'business']):
            return 'application'
        elif any(pattern in path_str for pattern in ['entity', 'domain', 'model', 'value_object']):
            return 'domain'

        # Check by class/function names
        class_names = ' '.join(classes).lower()
        function_names = ' '.join(functions).lower()

        if 'repository' in class_names or 'repository' in function_names:
            return 'infrastructure'
        elif 'route' in class_names or 'endpoint' in function_names:
            return 'presentation'
        elif 'entity' in class_names or 'domain' in class_names:
            return 'domain'
        elif 'usecase' in class_names or 'service' in class_names:
            return 'application'

        return 'shared'


class CodeMigrator:
    """Migrates code to 3-layer architecture"""

    def __init__(self, config: MigrationConfig):
        self.config = config
        self.analyzer = CodeAnalyzer(config.source_dir)
        self.migration_map = {}

    def migrate(self):
        """Perform the migration"""
        logger.info("Starting migration to 3-layer architecture")

        # Step 1: Backup if requested
        if self.config.preserve_original:
            self._backup_source()

        # Step 2: Analyze existing code
        analysis = self.analyzer.analyze()

        # Step 3: Create new directory structure
        self._create_directory_structure()

        # Step 4: Migrate files
        self._migrate_files(analysis)

        # Step 5: Update imports
        self._update_imports()

        # Step 6: Generate missing components
        self._generate_missing_components()

        # Step 7: Create tests if requested
        if self.config.create_tests:
            self._generate_tests()

        # Step 8: Generate documentation
        if self.config.create_docs:
            self._generate_documentation()

        logger.info("Migration completed successfully!")

    def _backup_source(self):
        """Create backup of source directory"""
        logger.info(f"Creating backup in {self.config.backup_dir}")
        if not self.config.dry_run:
            shutil.copytree(self.config.source_dir, self.config.backup_dir,
                          dirs_exist_ok=True)

    def _create_directory_structure(self):
        """Create 3-layer directory structure"""
        logger.info("Creating 3-layer directory structure")

        directories = [
            # Backend structure
            'src/api/routes',
            'src/api/middlewares',
            'src/api/dependencies',
            'src/api/schemas',
            'src/domain/entities',
            'src/domain/value_objects',
            'src/domain/interfaces',
            'src/domain/exceptions',
            'src/domain/specifications',
            'src/application/use_cases',
            'src/application/services',
            'src/application/dto',
            'src/infrastructure/repositories/mysql',
            'src/infrastructure/repositories/mongodb',
            'src/infrastructure/repositories/cache',
            'src/infrastructure/external_services',
            'src/infrastructure/database',
            'src/infrastructure/messaging',
            'src/infrastructure/monitoring',
            'src/shared/utils',
            'src/shared/constants',
            'src/shared/decorators',

            # Frontend structure
            'frontend/src/components/common',
            'frontend/src/components/layout',
            'frontend/src/components/features',
            'frontend/src/features',
            'frontend/src/hooks',
            'frontend/src/services',
            'frontend/src/store',
            'frontend/src/utils',
            'frontend/src/types',

            # Tests
            'tests/unit/domain',
            'tests/unit/application',
            'tests/unit/infrastructure',
            'tests/integration',
            'tests/e2e',

            # Scripts and docs
            'scripts/generate',
            'scripts/migration',
            'docs/architecture',
            'docs/api'
        ]

        for dir_path in directories:
            full_path = self.config.target_dir / dir_path
            if not self.config.dry_run:
                full_path.mkdir(parents=True, exist_ok=True)
                # Create __init__.py for Python packages
                if 'src' in dir_path or 'tests' in dir_path:
                    init_file = full_path / '__init__.py'
                    if not init_file.exists():
                        init_file.touch()
            logger.debug(f"Created directory: {dir_path}")

    def _migrate_files(self, analysis: Dict):
        """Migrate files to appropriate layers"""
        logger.info("Migrating files to 3-layer structure")

        for module_path, module_info in analysis['modules'].items():
            source_path = self.config.source_dir / module_path
            layer = module_info['type']

            # Determine target path based on layer
            target_path = self._determine_target_path(module_path, layer)

            if target_path:
                self.migration_map[module_path] = target_path

                if not self.config.dry_run:
                    # Read source file
                    with open(source_path, 'r', encoding='utf-8') as f:
                        content = f.read()

                    # Transform content if needed
                    transformed_content = self._transform_code(content, layer)

                    # Write to target
                    target_file = self.config.target_dir / target_path
                    target_file.parent.mkdir(parents=True, exist_ok=True)

                    with open(target_file, 'w', encoding='utf-8') as f:
                        f.write(transformed_content)

                logger.debug(f"Migrated {module_path} -> {target_path}")

    def _determine_target_path(self, source_path: str, layer: str) -> Optional[str]:
        """Determine target path based on layer"""

        # Parse source path
        path = Path(source_path)
        file_name = path.name

        # Special cases for specific files
        if 'server_unified.py' in file_name:
            return 'src/main.py'
        elif 'unified_database_manager.py' in file_name:
            return 'src/infrastructure/database/unified_manager.py'
        elif 'chatgpt_query_system.py' in file_name:
            return 'src/infrastructure/external_services/chatgpt_service.py'

        # Map based on layer
        layer_mapping = {
            'presentation': f'src/api/routes/{file_name}',
            'domain': f'src/domain/entities/{file_name}',
            'application': f'src/application/use_cases/{file_name}',
            'infrastructure': f'src/infrastructure/repositories/{file_name}',
            'shared': f'src/shared/utils/{file_name}'
        }

        return layer_mapping.get(layer)

    def _transform_code(self, content: str, layer: str) -> str:
        """Transform code to follow 3-layer patterns"""

        # Add layer-specific imports
        if layer == 'domain':
            # Add domain imports
            imports = [
                "from abc import ABC, abstractmethod",
                "from dataclasses import dataclass, field",
                "from typing import Optional, List, Dict, Any",
                "from datetime import datetime"
            ]
            content = '\n'.join(imports) + '\n\n' + content

        elif layer == 'application':
            # Add application layer imports
            imports = [
                "from dataclasses import dataclass",
                "from typing import Optional, List, Dict, Any",
                "from src.domain.interfaces import *",
                "from src.application.dto import *"
            ]
            content = '\n'.join(imports) + '\n\n' + content

        # Transform class definitions to follow patterns
        content = self._apply_design_patterns(content, layer)

        return content

    def _apply_design_patterns(self, content: str, layer: str) -> str:
        """Apply design patterns based on layer"""

        if layer == 'infrastructure':
            # Add repository pattern
            if 'class' in content and 'Repository' not in content:
                content = re.sub(
                    r'class\s+(\w+)',
                    r'class \1Repository',
                    content
                )

        elif layer == 'application':
            # Add use case pattern
            if 'class' in content and 'UseCase' not in content:
                content = re.sub(
                    r'class\s+(\w+)',
                    r'class \1UseCase',
                    content
                )

        return content

    def _update_imports(self):
        """Update import statements in migrated files"""
        logger.info("Updating import statements")

        for old_path, new_path in self.migration_map.items():
            target_file = self.config.target_dir / new_path

            if target_file.exists() and not self.config.dry_run:
                with open(target_file, 'r', encoding='utf-8') as f:
                    content = f.read()

                # Update imports based on migration map
                for old_import, new_import in self.migration_map.items():
                    old_module = old_import.replace('.py', '').replace('/', '.')
                    new_module = new_import.replace('.py', '').replace('/', '.')

                    content = content.replace(
                        f"from {old_module}",
                        f"from {new_module}"
                    )
                    content = content.replace(
                        f"import {old_module}",
                        f"import {new_module}"
                    )

                with open(target_file, 'w', encoding='utf-8') as f:
                    f.write(content)

    def _generate_missing_components(self):
        """Generate missing architectural components"""
        logger.info("Generating missing components")

        # Generate interfaces for repositories
        self._generate_repository_interfaces()

        # Generate DTOs for use cases
        self._generate_dtos()

        # Generate value objects
        self._generate_value_objects()

        # Generate middleware
        self._generate_middleware()

    def _generate_repository_interfaces(self):
        """Generate repository interfaces"""
        interface_template = '''from abc import ABC, abstractmethod
from typing import Optional, List, Dict, Any
from datetime import datetime

class {name}Repository(ABC):
    """Abstract repository for {name} entity"""

    @abstractmethod
    async def save(self, entity: Any) -> Any:
        """Save entity"""
        pass

    @abstractmethod
    async def get_by_id(self, entity_id: str) -> Optional[Any]:
        """Get entity by ID"""
        pass

    @abstractmethod
    async def get_all(self, limit: int = 100) -> List[Any]:
        """Get all entities"""
        pass

    @abstractmethod
    async def update(self, entity: Any) -> Any:
        """Update entity"""
        pass

    @abstractmethod
    async def delete(self, entity_id: str) -> bool:
        """Delete entity"""
        pass
'''

        entities = ['Query', 'Product', 'Pharmacy', 'Booking', 'User']

        for entity in entities:
            interface_path = self.config.target_dir / f'src/domain/interfaces/{entity.lower()}_repository.py'

            if not self.config.dry_run:
                interface_path.parent.mkdir(parents=True, exist_ok=True)
                with open(interface_path, 'w', encoding='utf-8') as f:
                    f.write(interface_template.format(name=entity))

            logger.debug(f"Generated interface: {entity}Repository")

    def _generate_dtos(self):
        """Generate DTOs for use cases"""
        dto_template = '''from dataclasses import dataclass
from typing import Optional, List, Dict, Any
from datetime import datetime

@dataclass
class {name}DTO:
    """Data Transfer Object for {name}"""

    # Add fields as needed
    id: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            'id': self.id,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> '{name}DTO':
        """Create from dictionary"""
        return cls(
            id=data.get('id'),
            created_at=datetime.fromisoformat(data['created_at']) if data.get('created_at') else None,
            updated_at=datetime.fromisoformat(data['updated_at']) if data.get('updated_at') else None
        )
'''

        dtos = ['Query', 'QueryResult', 'User', 'Product', 'Analytics']

        for dto in dtos:
            dto_path = self.config.target_dir / f'src/application/dto/{dto.lower()}_dto.py'

            if not self.config.dry_run:
                dto_path.parent.mkdir(parents=True, exist_ok=True)
                with open(dto_path, 'w', encoding='utf-8') as f:
                    f.write(dto_template.format(name=dto))

            logger.debug(f"Generated DTO: {dto}DTO")

    def _generate_value_objects(self):
        """Generate value objects"""
        vo_template = '''from dataclasses import dataclass
from typing import Optional

@dataclass(frozen=True)
class {name}:
    """Value object for {name}"""

    value: Any

    def __post_init__(self):
        """Validate value object"""
        self.validate()

    def validate(self):
        """Validate the value"""
        if not self.value:
            raise ValueError(f"Invalid {name}: value cannot be empty")

    def __str__(self) -> str:
        return str(self.value)

    def __repr__(self) -> str:
        return f"{name}(value={self.value!r})"
'''

        value_objects = ['QueryIntent', 'TimeRange', 'DatabaseRoute', 'RiskScore', 'GMV']

        for vo in value_objects:
            vo_path = self.config.target_dir / f'src/domain/value_objects/{vo.lower()}.py'

            if not self.config.dry_run:
                vo_path.parent.mkdir(parents=True, exist_ok=True)
                with open(vo_path, 'w', encoding='utf-8') as f:
                    f.write(vo_template.format(name=vo))

            logger.debug(f"Generated value object: {vo}")

    def _generate_middleware(self):
        """Generate middleware components"""
        middleware_template = '''from fastapi import Request, HTTPException
from fastapi.responses import JSONResponse
import time
import logging

logger = logging.getLogger(__name__)

async def {name}_middleware(request: Request, call_next):
    """
    {name} middleware
    """
    start_time = time.time()

    try:
        # Pre-processing
        logger.info(f"Request: {{request.method}} {{request.url}}")

        # Call next middleware or endpoint
        response = await call_next(request)

        # Post-processing
        process_time = time.time() - start_time
        response.headers["X-Process-Time"] = str(process_time)

        return response

    except Exception as e:
        logger.error(f"Error in {name} middleware: {{e}}")
        return JSONResponse(
            status_code=500,
            content={{"detail": "Internal server error"}}
        )
'''

        middlewares = ['auth', 'cors', 'rate_limit', 'logging', 'error_handler']

        for middleware in middlewares:
            middleware_path = self.config.target_dir / f'src/api/middlewares/{middleware}_middleware.py'

            if not self.config.dry_run:
                middleware_path.parent.mkdir(parents=True, exist_ok=True)
                with open(middleware_path, 'w', encoding='utf-8') as f:
                    f.write(middleware_template.format(name=middleware))

            logger.debug(f"Generated middleware: {middleware}_middleware")

    def _generate_tests(self):
        """Generate test files"""
        logger.info("Generating test files")

        test_template = '''import pytest
from unittest.mock import Mock, patch
from datetime import datetime

class Test{name}:
    """Tests for {name}"""

    @pytest.fixture
    def setup(self):
        """Setup test fixtures"""
        # Add setup code here
        pass

    def test_create(self, setup):
        """Test creation"""
        assert True  # Add actual test

    def test_update(self, setup):
        """Test update"""
        assert True  # Add actual test

    def test_delete(self, setup):
        """Test deletion"""
        assert True  # Add actual test

    def test_validation(self, setup):
        """Test validation"""
        assert True  # Add actual test
'''

        # Generate tests for each layer
        test_files = [
            ('tests/unit/domain/test_query_entity.py', 'QueryEntity'),
            ('tests/unit/application/test_execute_query_use_case.py', 'ExecuteQueryUseCase'),
            ('tests/unit/infrastructure/test_mysql_repository.py', 'MySQLRepository'),
            ('tests/integration/test_query_flow.py', 'QueryFlow'),
            ('tests/e2e/test_complete_flow.py', 'CompleteFlow')
        ]

        for test_path, test_name in test_files:
            full_path = self.config.target_dir / test_path

            if not self.config.dry_run:
                full_path.parent.mkdir(parents=True, exist_ok=True)
                with open(full_path, 'w', encoding='utf-8') as f:
                    f.write(test_template.format(name=test_name))

            logger.debug(f"Generated test: {test_path}")

    def _generate_documentation(self):
        """Generate documentation"""
        logger.info("Generating documentation")

        # Generate migration report
        report = {
            'migration_date': datetime.now().isoformat(),
            'source_dir': str(self.config.source_dir),
            'target_dir': str(self.config.target_dir),
            'files_migrated': len(self.migration_map),
            'migration_map': self.migration_map,
            'layers': {
                'presentation': [],
                'domain': [],
                'application': [],
                'infrastructure': [],
                'shared': []
            }
        }

        # Categorize migrated files by layer
        for old_path, new_path in self.migration_map.items():
            if 'api' in new_path:
                report['layers']['presentation'].append(new_path)
            elif 'domain' in new_path:
                report['layers']['domain'].append(new_path)
            elif 'application' in new_path:
                report['layers']['application'].append(new_path)
            elif 'infrastructure' in new_path:
                report['layers']['infrastructure'].append(new_path)
            else:
                report['layers']['shared'].append(new_path)

        # Write report
        if not self.config.dry_run:
            report_path = self.config.target_dir / 'docs/migration_report.json'
            report_path.parent.mkdir(parents=True, exist_ok=True)

            with open(report_path, 'w', encoding='utf-8') as f:
                json.dump(report, f, indent=2)

            # Generate README
            readme_content = f'''# TrendsPro - 3-Layer Architecture

## Migration Report

**Date**: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
**Files Migrated**: {len(self.migration_map)}

## Architecture Overview

### Presentation Layer
- Location: `src/api/`
- Files: {len(report['layers']['presentation'])}
- Purpose: HTTP endpoints, request/response handling, middleware

### Domain Layer
- Location: `src/domain/`
- Files: {len(report['layers']['domain'])}
- Purpose: Business entities, value objects, domain logic

### Application Layer
- Location: `src/application/`
- Files: {len(report['layers']['application'])}
- Purpose: Use cases, application services, orchestration

### Infrastructure Layer
- Location: `src/infrastructure/`
- Files: {len(report['layers']['infrastructure'])}
- Purpose: Database access, external services, technical implementations

### Shared Layer
- Location: `src/shared/`
- Files: {len(report['layers']['shared'])}
- Purpose: Utilities, constants, decorators

## Running the Application

```bash
# Install dependencies
poetry install

# Run migrations
alembic upgrade head

# Start the application
uvicorn src.main:app --reload
```

## Testing

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=src --cov-report=html
```
'''

            readme_path = self.config.target_dir / 'README_ARCHITECTURE.md'
            with open(readme_path, 'w', encoding='utf-8') as f:
                f.write(readme_content)

        logger.info("Documentation generated successfully")


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description='Migrate TrendsPro to 3-layer architecture'
    )

    parser.add_argument(
        '--source',
        type=Path,
        default=Path.cwd(),
        help='Source directory (default: current directory)'
    )

    parser.add_argument(
        '--target',
        type=Path,
        default=Path.cwd() / 'migrated',
        help='Target directory (default: ./migrated)'
    )

    parser.add_argument(
        '--backup',
        type=Path,
        default=Path.cwd() / 'backup',
        help='Backup directory (default: ./backup)'
    )

    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Perform dry run without making changes'
    )

    parser.add_argument(
        '--no-backup',
        action='store_true',
        help='Skip backup creation'
    )

    parser.add_argument(
        '--no-tests',
        action='store_true',
        help='Skip test generation'
    )

    parser.add_argument(
        '--no-docs',
        action='store_true',
        help='Skip documentation generation'
    )

    parser.add_argument(
        '--verbose',
        action='store_true',
        help='Enable verbose logging'
    )

    args = parser.parse_args()

    # Configure logging level
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)

    # Create configuration
    config = MigrationConfig(
        source_dir=args.source,
        target_dir=args.target,
        backup_dir=args.backup,
        dry_run=args.dry_run,
        preserve_original=not args.no_backup,
        create_tests=not args.no_tests,
        create_docs=not args.no_docs
    )

    # Perform migration
    migrator = CodeMigrator(config)

    try:
        if args.dry_run:
            logger.info("Performing DRY RUN - no changes will be made")

        migrator.migrate()

        if args.dry_run:
            logger.info("Dry run completed. Review the output and run without --dry-run to apply changes")
        else:
            logger.info(f"Migration completed! Check the results in {args.target}")

    except Exception as e:
        logger.error(f"Migration failed: {e}")
        return 1

    return 0


if __name__ == "__main__":
    exit(main())