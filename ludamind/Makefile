# TrendsPro Enterprise Makefile
# Version: 2.1.0
# Architecture: 3-Layer (Presentation, Domain, Infrastructure)

.PHONY: help install test build deploy clean migrate

# ==================== Variables ====================
PYTHON := python3
POETRY := poetry
NPM := npm
DOCKER := docker
DOCKER_COMPOSE := docker-compose
KUBECTL := kubectl
GIT := git

# Python tools
BLACK := $(POETRY) run black
FLAKE8 := $(POETRY) run flake8
MYPY := $(POETRY) run mypy
PYTEST := $(POETRY) run pytest
BANDIT := $(POETRY) run bandit
ISORT := $(POETRY) run isort

# Node tools
ESLINT := npx eslint
PRETTIER := npx prettier
PLAYWRIGHT := npx playwright

# Directories
SRC_DIR := src
FRONTEND_DIR := frontend
TESTS_DIR := tests
SCRIPTS_DIR := scripts
DOCS_DIR := docs

# Docker
DOCKER_REGISTRY := ghcr.io
IMAGE_NAME := trendspro
VERSION := $(shell git describe --tags --always --dirty)

# Colors for output
RED := \033[0;31m
GREEN := \033[0;32m
YELLOW := \033[0;33m
BLUE := \033[0;34m
MAGENTA := \033[0;35m
CYAN := \033[0;36m
WHITE := \033[0;37m
NC := \033[0m

# ==================== Help ====================
help: ## Show this help message
	@echo "$(CYAN)╔════════════════════════════════════════════════════════════╗$(NC)"
	@echo "$(CYAN)║$(YELLOW)     TrendsPro Enterprise - Make Commands                     $(CYAN)║$(NC)"
	@echo "$(CYAN)║$(WHITE)     3-Layer Architecture | Multi-Agent System                $(CYAN)║$(NC)"
	@echo "$(CYAN)╚════════════════════════════════════════════════════════════╝$(NC)"
	@echo ""
	@echo "$(GREEN)Usage:$(NC) make $(YELLOW)[target]$(NC)"
	@echo ""
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | \
		awk 'BEGIN {FS = ":.*?## "; printf "$(CYAN)%-20s$(NC) %s\n", "Target", "Description"} \
			{printf "$(GREEN)%-20s$(NC) %s\n", $$1, $$2}'
	@echo ""
	@echo "$(MAGENTA)Examples:$(NC)"
	@echo "  make install        # Install all dependencies"
	@echo "  make test          # Run all tests"
	@echo "  make migrate       # Migrate to 3-layer architecture"
	@echo "  make dev           # Start development environment"

# ==================== Installation ====================
install: ## Install all dependencies (Python + Node.js)
	@echo "$(YELLOW)📦 Installing Python dependencies...$(NC)"
	$(POETRY) install --with dev
	@echo "$(YELLOW)📦 Installing Node.js dependencies...$(NC)"
	cd $(FRONTEND_DIR) && $(NPM) ci
	@echo "$(YELLOW)📦 Installing MCP server dependencies...$(NC)"
	$(NPM) ci
	@echo "$(YELLOW)📦 Installing pre-commit hooks...$(NC)"
	pre-commit install
	@echo "$(GREEN)✅ All dependencies installed successfully!$(NC)"

install-prod: ## Install production dependencies only
	@echo "$(YELLOW)📦 Installing production dependencies...$(NC)"
	$(POETRY) install --without dev
	cd $(FRONTEND_DIR) && $(NPM) ci --production
	$(NPM) ci --production
	@echo "$(GREEN)✅ Production dependencies installed!$(NC)"

update-deps: ## Update all dependencies
	@echo "$(YELLOW)🔄 Updating Python dependencies...$(NC)"
	$(POETRY) update
	@echo "$(YELLOW)🔄 Updating Node.js dependencies...$(NC)"
	cd $(FRONTEND_DIR) && $(NPM) update
	$(NPM) update
	@echo "$(GREEN)✅ Dependencies updated!$(NC)"

# ==================== Code Quality ====================
format: ## Format all code (Python + JavaScript)
	@echo "$(YELLOW)🎨 Formatting Python code...$(NC)"
	$(BLACK) $(SRC_DIR) $(TESTS_DIR) $(SCRIPTS_DIR)
	$(ISORT) $(SRC_DIR) $(TESTS_DIR) $(SCRIPTS_DIR)
	@echo "$(YELLOW)🎨 Formatting JavaScript/TypeScript code...$(NC)"
	cd $(FRONTEND_DIR) && $(PRETTIER) --write "src/**/*.{js,jsx,ts,tsx,css,json}"
	$(PRETTIER) --write "src/**/*.{js,ts,json}"
	@echo "$(GREEN)✅ Code formatted!$(NC)"

lint: ## Run all linters
	@echo "$(YELLOW)🔍 Linting Python code...$(NC)"
	$(BLACK) --check $(SRC_DIR) $(TESTS_DIR)
	$(FLAKE8) $(SRC_DIR) $(TESTS_DIR)
	$(MYPY) $(SRC_DIR)
	@echo "$(YELLOW)🔍 Linting JavaScript/TypeScript code...$(NC)"
	cd $(FRONTEND_DIR) && $(ESLINT) src/
	$(ESLINT) src/
	@echo "$(GREEN)✅ All linting checks passed!$(NC)"

security: ## Run security checks
	@echo "$(YELLOW)🔒 Running Python security checks...$(NC)"
	$(BANDIT) -r $(SRC_DIR)
	$(POETRY) run safety check
	@echo "$(YELLOW)🔒 Running Node.js security checks...$(NC)"
	cd $(FRONTEND_DIR) && $(NPM) audit
	$(NPM) audit
	@echo "$(GREEN)✅ Security checks completed!$(NC)"

quality: format lint security ## Run all quality checks

# ==================== Testing ====================
test: ## Run all tests (unit + integration + E2E)
	@echo "$(YELLOW)🧪 Running Python tests...$(NC)"
	$(PYTEST) $(TESTS_DIR) -v --cov=$(SRC_DIR) --cov-report=term-missing
	@echo "$(YELLOW)🧪 Running JavaScript tests...$(NC)"
	cd $(FRONTEND_DIR) && $(NPM) test
	@echo "$(YELLOW)🧪 Running E2E tests...$(NC)"
	$(PLAYWRIGHT) test
	@echo "$(GREEN)✅ All tests passed!$(NC)"

test-unit: ## Run unit tests only
	@echo "$(YELLOW)🧪 Running unit tests...$(NC)"
	$(PYTEST) $(TESTS_DIR)/unit -v
	cd $(FRONTEND_DIR) && $(NPM) run test:unit

test-integration: ## Run integration tests
	@echo "$(YELLOW)🧪 Running integration tests...$(NC)"
	$(PYTEST) $(TESTS_DIR)/integration -v

test-e2e: ## Run E2E tests
	@echo "$(YELLOW)🧪 Running E2E tests...$(NC)"
	$(PLAYWRIGHT) test

test-coverage: ## Generate test coverage report
	@echo "$(YELLOW)📊 Generating coverage report...$(NC)"
	$(PYTEST) $(TESTS_DIR) --cov=$(SRC_DIR) --cov-report=html
	cd $(FRONTEND_DIR) && $(NPM) run test:coverage
	@echo "$(GREEN)✅ Coverage report generated in htmlcov/$(NC)"

test-watch: ## Run tests in watch mode
	$(PYTEST) $(TESTS_DIR) --watch

# ==================== Architecture Migration ====================
migrate: ## Migrate to 3-layer architecture
	@echo "$(CYAN)🏗️  Starting migration to 3-layer architecture...$(NC)"
	$(PYTHON) $(SCRIPTS_DIR)/migrate_to_3_layer.py \
		--source . \
		--target migrated \
		--backup backup
	@echo "$(GREEN)✅ Migration completed! Check 'migrated' directory$(NC)"

migrate-dry-run: ## Dry run migration (no changes)
	@echo "$(YELLOW)🔍 Performing migration dry run...$(NC)"
	$(PYTHON) $(SCRIPTS_DIR)/migrate_to_3_layer.py \
		--source . \
		--target migrated \
		--dry-run \
		--verbose

refactor-solid: ## Apply SOLID principles to code
	@echo "$(YELLOW)♻️  Refactoring code to SOLID principles...$(NC)"
	$(PYTHON) $(SCRIPTS_DIR)/refactor_solid.py $(SRC_DIR)

# ==================== Code Generation ====================
generate-entity: ## Generate new entity (usage: make generate-entity name=Product)
	@echo "$(YELLOW)🏭 Generating entity: $(name)$(NC)"
	$(PYTHON) $(SCRIPTS_DIR)/generate/generate_entity.py \
		--name $(name) \
		--with-repository \
		--with-tests

generate-usecase: ## Generate new use case (usage: make generate-usecase name=ExecuteQuery)
	@echo "$(YELLOW)🏭 Generating use case: $(name)$(NC)"
	$(PYTHON) $(SCRIPTS_DIR)/generate/generate_use_case.py \
		--name $(name) \
		--with-dto \
		--with-tests

generate-component: ## Generate React component (usage: make generate-component name=QueryInterface)
	@echo "$(YELLOW)🏭 Generating React component: $(name)$(NC)"
	cd $(FRONTEND_DIR) && $(NPM) run generate:component $(name)

generate-api: ## Generate API endpoint (usage: make generate-api path=/api/v1/queries)
	@echo "$(YELLOW)🏭 Generating API endpoint: $(path)$(NC)"
	$(PYTHON) $(SCRIPTS_DIR)/generate/generate_endpoint.py --path $(path)

generate-module: ## Generate complete module (usage: make generate-module name=Analytics)
	@echo "$(YELLOW)🏭 Generating complete module: $(name)$(NC)"
	$(PYTHON) $(SCRIPTS_DIR)/generate/generate_module.py \
		--name $(name) \
		--layers all \
		--with-tests \
		--with-docs

# ==================== Database ====================
db-migrate: ## Run database migrations
	@echo "$(YELLOW)📊 Running database migrations...$(NC)"
	alembic upgrade head
	@echo "$(GREEN)✅ Migrations applied!$(NC)"

db-rollback: ## Rollback last migration
	@echo "$(YELLOW)↩️  Rolling back last migration...$(NC)"
	alembic downgrade -1

db-reset: ## Reset database to initial state
	@echo "$(RED)⚠️  Resetting database...$(NC)"
	@read -p "Are you sure? This will delete all data! [y/N] " -n 1 -r; \
	if [[ $$REPLY =~ ^[Yy]$$ ]]; then \
		alembic downgrade base; \
		alembic upgrade head; \
		echo "$(GREEN)✅ Database reset complete!$(NC)"; \
	fi

db-seed: ## Seed database with test data
	@echo "$(YELLOW)🌱 Seeding database...$(NC)"
	$(PYTHON) $(SCRIPTS_DIR)/seed_database.py
	@echo "$(GREEN)✅ Database seeded!$(NC)"

db-backup: ## Backup databases
	@echo "$(YELLOW)💾 Backing up databases...$(NC)"
	@mkdir -p backups
	mysqldump -h 127.0.0.1 -P 3307 trends_consolidado > backups/mysql_$(shell date +%Y%m%d_%H%M%S).sql
	mongodump --uri="mongodb://localhost:27017/ludafarma" --out=backups/mongo_$(shell date +%Y%m%d_%H%M%S)
	@echo "$(GREEN)✅ Backup completed!$(NC)"

# ==================== Development ====================
dev: ## Start complete development environment
	@echo "$(CYAN)🚀 Starting development environment...$(NC)"
	$(DOCKER_COMPOSE) -f docker/docker-compose.dev.yml up -d
	@echo "$(GREEN)✅ Development environment ready!$(NC)"
	@echo "$(WHITE)  Backend: http://localhost:8000$(NC)"
	@echo "$(WHITE)  Frontend: http://localhost:3000$(NC)"
	@echo "$(WHITE)  Docs: http://localhost:8000/docs$(NC)"

dev-backend: ## Start backend only (FastAPI)
	@echo "$(YELLOW)🚀 Starting backend server...$(NC)"
	$(POETRY) run uvicorn src.main:app --reload --port 8000

dev-frontend: ## Start frontend only (React)
	@echo "$(YELLOW)🚀 Starting frontend server...$(NC)"
	cd $(FRONTEND_DIR) && $(NPM) run dev

dev-mcp: ## Start MCP server
	@echo "$(YELLOW)🚀 Starting MCP server...$(NC)"
	$(NPM) run dev

dev-stop: ## Stop development environment
	@echo "$(YELLOW)⏹️  Stopping development environment...$(NC)"
	$(DOCKER_COMPOSE) -f docker/docker-compose.dev.yml down

dev-logs: ## Show development logs
	$(DOCKER_COMPOSE) -f docker/docker-compose.dev.yml logs -f

dev-shell: ## Open Python shell with app context
	@echo "$(CYAN)🐍 Opening Python shell...$(NC)"
	$(POETRY) run python -i $(SCRIPTS_DIR)/shell.py

# ==================== Docker ====================
docker-build: ## Build Docker images
	@echo "$(YELLOW)🐳 Building Docker images...$(NC)"
	$(DOCKER) build -f docker/Dockerfile.backend -t $(IMAGE_NAME)-backend:$(VERSION) .
	$(DOCKER) build -f docker/Dockerfile.frontend -t $(IMAGE_NAME)-frontend:$(VERSION) $(FRONTEND_DIR)
	@echo "$(GREEN)✅ Docker images built!$(NC)"

docker-push: ## Push Docker images to registry
	@echo "$(YELLOW)📤 Pushing Docker images...$(NC)"
	$(DOCKER) tag $(IMAGE_NAME)-backend:$(VERSION) $(DOCKER_REGISTRY)/$(IMAGE_NAME)-backend:$(VERSION)
	$(DOCKER) tag $(IMAGE_NAME)-frontend:$(VERSION) $(DOCKER_REGISTRY)/$(IMAGE_NAME)-frontend:$(VERSION)
	$(DOCKER) push $(DOCKER_REGISTRY)/$(IMAGE_NAME)-backend:$(VERSION)
	$(DOCKER) push $(DOCKER_REGISTRY)/$(IMAGE_NAME)-frontend:$(VERSION)
	@echo "$(GREEN)✅ Images pushed to registry!$(NC)"

docker-run: ## Run Docker containers locally
	@echo "$(YELLOW)🐳 Running Docker containers...$(NC)"
	$(DOCKER_COMPOSE) -f docker/docker-compose.yml up

docker-clean: ## Clean Docker resources
	@echo "$(YELLOW)🧹 Cleaning Docker resources...$(NC)"
	$(DOCKER) system prune -f
	$(DOCKER) volume prune -f
	@echo "$(GREEN)✅ Docker cleaned!$(NC)"

# ==================== Deployment ====================
deploy-staging: ## Deploy to staging environment
	@echo "$(CYAN)🚀 Deploying to STAGING...$(NC)"
	$(KUBECTL) apply -f kubernetes/staging/
	$(KUBECTL) set image deployment/trendspro-backend \
		backend=$(DOCKER_REGISTRY)/$(IMAGE_NAME)-backend:$(VERSION) \
		-n staging
	$(KUBECTL) set image deployment/trendspro-frontend \
		frontend=$(DOCKER_REGISTRY)/$(IMAGE_NAME)-frontend:$(VERSION) \
		-n staging
	$(KUBECTL) rollout status deployment/trendspro-backend -n staging
	$(KUBECTL) rollout status deployment/trendspro-frontend -n staging
	@echo "$(GREEN)✅ Deployed to staging!$(NC)"

deploy-production: ## Deploy to production environment
	@echo "$(RED)⚠️  DEPLOYING TO PRODUCTION$(NC)"
	@read -p "Are you sure? [y/N] " -n 1 -r; \
	if [[ $$REPLY =~ ^[Yy]$$ ]]; then \
		$(KUBECTL) apply -f kubernetes/production/; \
		$(KUBECTL) set image deployment/trendspro-backend \
			backend=$(DOCKER_REGISTRY)/$(IMAGE_NAME)-backend:$(VERSION) \
			-n production; \
		$(KUBECTL) set image deployment/trendspro-frontend \
			frontend=$(DOCKER_REGISTRY)/$(IMAGE_NAME)-frontend:$(VERSION) \
			-n production; \
		$(KUBECTL) rollout status deployment/trendspro-backend -n production; \
		$(KUBECTL) rollout status deployment/trendspro-frontend -n production; \
		echo "$(GREEN)✅ Deployed to production!$(NC)"; \
	fi

rollback: ## Rollback last deployment
	@echo "$(YELLOW)↩️  Rolling back deployment...$(NC)"
	$(KUBECTL) rollout undo deployment/trendspro-backend
	$(KUBECTL) rollout undo deployment/trendspro-frontend
	@echo "$(GREEN)✅ Rollback completed!$(NC)"

# ==================== Monitoring ====================
logs: ## Show application logs
	@echo "$(CYAN)📋 Application logs:$(NC)"
	$(KUBECTL) logs -f deployment/trendspro-backend --tail=100

logs-frontend: ## Show frontend logs
	$(KUBECTL) logs -f deployment/trendspro-frontend --tail=100

metrics: ## Open Prometheus metrics dashboard
	@echo "$(CYAN)📊 Opening Prometheus...$(NC)"
	open http://localhost:9090

grafana: ## Open Grafana dashboard
	@echo "$(CYAN)📈 Opening Grafana...$(NC)"
	open http://localhost:3000

monitor: ## Show system monitoring dashboard
	@echo "$(CYAN)📊 System Monitoring:$(NC)"
	@echo "  CPU Usage: $$(top -bn1 | grep load | awk '{printf \"%.2f%%\", $$(NF-2)}')"
	@echo "  Memory: $$(free -m | awk 'NR==2{printf \"%.2f%%\", $$3*100/$$2}')"
	@echo "  Disk: $$(df -h | awk '$$NF==\"/\"{printf \"%s\", $$5}')"

# ==================== Documentation ====================
docs: ## Generate documentation
	@echo "$(YELLOW)📚 Generating documentation...$(NC)"
	$(POETRY) run sphinx-build -b html $(DOCS_DIR) $(DOCS_DIR)/_build
	@echo "$(GREEN)✅ Documentation generated in docs/_build/$(NC)"

docs-serve: ## Serve documentation locally
	@echo "$(CYAN)📚 Serving documentation at http://localhost:8080$(NC)"
	$(PYTHON) -m http.server --directory $(DOCS_DIR)/_build 8080

docs-api: ## Generate API documentation
	@echo "$(YELLOW)📚 Generating API docs...$(NC)"
	$(POETRY) run python $(SCRIPTS_DIR)/generate_openapi.py > $(DOCS_DIR)/openapi.yaml
	@echo "$(GREEN)✅ API docs generated!$(NC)"

# ==================== Performance ====================
perf-test: ## Run performance tests
	@echo "$(YELLOW)⚡ Running performance tests...$(NC)"
	k6 run tests/k6/load-test.js
	@echo "$(GREEN)✅ Performance tests completed!$(NC)"

perf-profile: ## Profile application performance
	@echo "$(YELLOW)🔍 Profiling application...$(NC)"
	$(POETRY) run py-spy record -o profile.svg -- $(PYTHON) src/main.py
	@echo "$(GREEN)✅ Profile saved to profile.svg$(NC)"

benchmark: ## Run benchmarks
	@echo "$(YELLOW)⚡ Running benchmarks...$(NC)"
	$(POETRY) run python $(SCRIPTS_DIR)/benchmark.py
	@echo "$(GREEN)✅ Benchmarks completed!$(NC)"

# ==================== Utilities ====================
clean: ## Clean all generated files and caches
	@echo "$(YELLOW)🧹 Cleaning project...$(NC)"
	rm -rf dist/ build/ *.egg-info .coverage htmlcov/ .pytest_cache/
	rm -rf $(FRONTEND_DIR)/build $(FRONTEND_DIR)/dist
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete
	find . -type f -name ".DS_Store" -delete
	@echo "$(GREEN)✅ Project cleaned!$(NC)"

version: ## Show version information
	@echo "$(CYAN)ℹ️  TrendsPro Version Information$(NC)"
	@echo "  Version: $(VERSION)"
	@echo "  Python: $$($(PYTHON) --version)"
	@echo "  Node.js: $$(node --version)"
	@echo "  Docker: $$($(DOCKER) --version)"
	@echo "  Git SHA: $$(git rev-parse HEAD)"

check-deps: ## Check for outdated dependencies
	@echo "$(YELLOW)🔍 Checking dependencies...$(NC)"
	$(POETRY) show --outdated
	cd $(FRONTEND_DIR) && $(NPM) outdated
	$(NPM) outdated

backup: ## Create full project backup
	@echo "$(YELLOW)💾 Creating backup...$(NC)"
	tar -czf backup_$(shell date +%Y%m%d_%H%M%S).tar.gz \
		--exclude=node_modules \
		--exclude=.venv \
		--exclude=dist \
		--exclude=build \
		--exclude=htmlcov \
		--exclude=__pycache__ \
		.
	@echo "$(GREEN)✅ Backup created!$(NC)"

# ==================== CI/CD ====================
ci: quality test ## Run CI pipeline locally
	@echo "$(GREEN)✅ CI pipeline passed!$(NC)"

cd-staging: docker-build docker-push deploy-staging ## CD pipeline for staging

cd-production: docker-build docker-push deploy-production ## CD pipeline for production

release: ## Create a new release
	@echo "$(CYAN)📦 Creating release...$(NC)"
	@read -p "Version (current: $(VERSION)): " version; \
	git tag -a $$version -m "Release $$version"; \
	git push origin $$version; \
	echo "$(GREEN)✅ Release $$version created!$(NC)"

# ==================== Shortcuts ====================
i: install ## Shortcut for install
f: format ## Shortcut for format
l: lint ## Shortcut for lint
t: test ## Shortcut for test
d: dev ## Shortcut for dev
b: docker-build ## Shortcut for build
c: clean ## Shortcut for clean

# ==================== Special Targets ====================
all: clean install quality test docker-build ## Run everything

check: format lint test ## Run all checks

quick: format test-unit ## Quick check (format + unit tests)

.DEFAULT_GOAL := help

# Prevent Make from trying to remake the Makefile
Makefile: ;

# Always execute these targets
.PHONY: $(shell grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk '{print $$1}' | sed 's/://g')