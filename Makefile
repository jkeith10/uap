.PHONY: help install dev-setup test lint format clean run migrate docker-up docker-down

help: ## Show this help message
	@echo 'Usage: make [target]'
	@echo ''
	@echo 'Available targets:'
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-15s\033[0m %s\n", $$1, $$2}'

install: ## Install dependencies
	poetry install

dev-setup: ## Set up development environment
	poetry install
	poetry run pre-commit install
	docker-compose -f docker-compose.dev.yml up -d postgres redis
	sleep 5
	poetry run uap migrate

test: ## Run tests
	poetry run pytest -v --cov=src/uap --cov-report=html

test-unit: ## Run unit tests only
	poetry run pytest tests/unit/ -v

test-integration: ## Run integration tests only
	poetry run pytest tests/integration/ -v

test-e2e: ## Run end-to-end tests only
	poetry run pytest tests/e2e/ -v

lint: ## Run linting
	poetry run ruff check src/ tests/
	poetry run mypy src/

format: ## Format code
	poetry run black src/ tests/
	poetry run isort src/ tests/

clean: ## Clean generated files
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
	find . -type f -name "*.pyo" -delete
	find . -type d -name "*.egg-info" -exec rm -rf {} +
	find . -type d -name ".pytest_cache" -exec rm -rf {} +
	find . -type d -name ".mypy_cache" -exec rm -rf {} +
	find . -type d -name ".ruff_cache" -exec rm -rf {} +
	rm -rf htmlcov/
	rm -rf dist/
	rm -rf build/

run: ## Run UAP server
	poetry run uap serve --reload

migrate: ## Run database migrations
	poetry run uap migrate

migrate-rollback: ## Rollback last migration
	poetry run alembic downgrade -1

docker-up: ## Start all Docker services
	docker-compose -f docker-compose.dev.yml up -d

docker-down: ## Stop all Docker services
	docker-compose -f docker-compose.dev.yml down

docker-logs: ## Show Docker logs
	docker-compose -f docker-compose.dev.yml logs -f

docker-ps: ## Show Docker containers
	docker-compose -f docker-compose.dev.yml ps

demo: ## Run demo workflow
	poetry run uap demo

status: ## Check system status
	poetry run uap status

init: ## Initialize a new UAP project
	poetry run uap init

build: ## Build package
	poetry build

publish: ## Publish to PyPI
	poetry publish

docs: ## Build documentation
	cd docs && make html

docs-serve: ## Serve documentation locally
	cd docs && python -m http.server 8080

benchmark: ## Run performance benchmarks
	poetry run pytest benchmarks/ -v

security: ## Run security checks
	poetry run bandit -r src/

pre-commit: ## Run pre-commit hooks
	poetry run pre-commit run --all-files

all: clean install lint test ## Run all checks
