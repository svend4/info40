# AI Agent Orchestration Platform - Makefile
# Convenience commands for development, testing, and deployment

.PHONY: help install test build deploy clean docker-build docker-up docker-down k8s-deploy helm-install lint format db-setup db-migrate db-seed

# Default target
.DEFAULT_GOAL := help

##@ General

help: ## Display this help message
	@awk 'BEGIN {FS = ":.*##"; printf "\nUsage:\n  make \033[36m<target>\033[0m\n"} /^[a-zA-Z_-]+:.*?##/ { printf "  \033[36m%-20s\033[0m %s\n", $$1, $$2 } /^##@/ { printf "\n\033[1m%s\033[0m\n", substr($$0, 5) } ' $(MAKEFILE_LIST)

##@ Development

install: ## Install all dependencies
	@echo "Installing Python dependencies..."
	pip install -r requirements/base.txt
	pip install -r requirements/dev.txt
	@echo "Installing SDK..."
	cd sdk && pip install -e ".[dev]"
	@echo "Installing CLI tool..."
	pip install -e cli/
	@echo "✓ All dependencies installed"

install-sdk: ## Install SDK only
	cd sdk && pip install -e ".[dev]"

install-cli: ## Install CLI tool only
	pip install -e cli/

run-registry: ## Run Registry Service locally
	cd api/registry_service && uvicorn main:app --reload --port 8001

run-marketplace: ## Run Marketplace Service locally
	cd api/marketplace_service && uvicorn main:app --reload --port 8002

run-orchestrator: ## Run Orchestrator Service locally
	cd api/orchestrator_service && uvicorn main:app --reload --port 8003

run-gateway: ## Run API Gateway locally
	cd api/api_gateway && uvicorn main:app --reload --port 8000

run-all: ## Run all services locally (requires tmux or multiple terminals)
	@echo "Starting all services..."
	@echo "Note: Use docker-compose for easier multi-service management"
	docker-compose up

##@ Testing

test: ## Run all tests
	pytest tests/ -v --cov=. --cov-report=html --cov-report=term

test-unit: ## Run unit tests only
	pytest tests/unit/ -v

test-integration: ## Run integration tests only
	pytest tests/integration/ -v

test-e2e: ## Run end-to-end tests only
	pytest tests/e2e/ -v

test-sdk: ## Run SDK tests
	cd sdk && pytest -v

test-coverage: ## Generate test coverage report
	pytest tests/ --cov=. --cov-report=html
	@echo "Coverage report generated in htmlcov/index.html"

load-test: ## Run load tests with Locust
	locust -f tests/load/locustfile.py --host=http://localhost:8000

##@ Code Quality

lint: ## Run linting on all Python code
	@echo "Running flake8..."
	flake8 api/ workers/ sdk/ cli/ tests/ examples/ --max-line-length=120 --exclude=venv,__pycache__
	@echo "Running pylint..."
	pylint api/ workers/ sdk/agent_platform_sdk/ --disable=C0111,R0903

format: ## Format code with black
	black api/ workers/ sdk/ cli/ tests/ examples/ --line-length=120

format-check: ## Check code formatting without changes
	black api/ workers/ sdk/ cli/ tests/ examples/ --line-length=120 --check

type-check: ## Run type checking with mypy
	mypy api/ workers/ sdk/agent_platform_sdk/ --ignore-missing-imports

##@ Docker

docker-build: ## Build all Docker images
	@echo "Building Docker images..."
	docker-compose build
	@echo "✓ All images built"

docker-build-registry: ## Build Registry Service image
	docker build -f docker/registry_service/Dockerfile -t agent-platform/registry-service:latest .

docker-build-marketplace: ## Build Marketplace Service image
	docker build -f docker/marketplace_service/Dockerfile -t agent-platform/marketplace-service:latest .

docker-build-orchestrator: ## Build Orchestrator Service image
	docker build -f docker/orchestrator_service/Dockerfile -t agent-platform/orchestrator-service:latest .

docker-build-gateway: ## Build API Gateway image
	docker build -f docker/api_gateway/Dockerfile -t agent-platform/api-gateway:latest .

docker-build-worker: ## Build Agent Worker image
	docker build -f docker/agent_worker/Dockerfile -t agent-platform/agent-worker:latest .

docker-up: ## Start all services with Docker Compose
	docker-compose up -d
	@echo "✓ All services started"
	@echo "API Gateway: http://localhost:8000"
	@echo "Registry Service: http://localhost:8001"
	@echo "Marketplace Service: http://localhost:8002"
	@echo "Orchestrator Service: http://localhost:8003"

docker-down: ## Stop all Docker services
	docker-compose down

docker-logs: ## View logs from all containers
	docker-compose logs -f

docker-ps: ## List running containers
	docker-compose ps

docker-clean: ## Remove all containers, images, and volumes
	docker-compose down -v --rmi all
	@echo "✓ All Docker resources cleaned"

##@ Database

db-setup: ## Initialize database schema
	@echo "Setting up database..."
	chmod +x scripts/setup_db.sh
	./scripts/setup_db.sh
	@echo "✓ Database initialized"

db-seed: ## Seed database with sample data
	@echo "Seeding database..."
	PGPASSWORD=postgres psql -h localhost -U postgres -d agent_platform -f database/seed.sql
	@echo "✓ Database seeded"

db-reset: ## Reset database (drop and recreate)
	@echo "Resetting database..."
	PGPASSWORD=postgres psql -h localhost -U postgres -c "DROP DATABASE IF EXISTS agent_platform;"
	PGPASSWORD=postgres psql -h localhost -U postgres -c "CREATE DATABASE agent_platform;"
	@$(MAKE) db-setup
	@$(MAKE) db-seed
	@echo "✓ Database reset complete"

db-migrate: ## Run database migrations (placeholder for future migrations)
	@echo "Running migrations..."
	@echo "Note: Migration system not yet implemented"

db-shell: ## Open PostgreSQL shell
	PGPASSWORD=postgres psql -h localhost -U postgres -d agent_platform

##@ Kubernetes

k8s-deploy: ## Deploy to Kubernetes using manifests
	@echo "Deploying to Kubernetes..."
	kubectl apply -f kubernetes/namespace.yaml
	kubectl apply -f kubernetes/
	@echo "✓ Deployed to Kubernetes"

k8s-delete: ## Delete Kubernetes resources
	kubectl delete -f kubernetes/

k8s-status: ## Check Kubernetes deployment status
	kubectl get pods -n agent-platform
	kubectl get services -n agent-platform

k8s-logs: ## View logs from Kubernetes pods
	kubectl logs -n agent-platform -l app=api-gateway --tail=100 -f

k8s-port-forward: ## Port forward API Gateway
	kubectl port-forward -n agent-platform svc/api-gateway 8000:8000

##@ Helm

helm-install: ## Install with Helm (development)
	@echo "Installing with Helm..."
	helm install agent-platform helm/agent-platform \
		--create-namespace \
		--namespace agent-platform \
		--values helm/agent-platform/values.yaml
	@echo "✓ Helm release installed"

helm-install-prod: ## Install with Helm (production)
	helm install agent-platform helm/agent-platform \
		--create-namespace \
		--namespace agent-platform \
		--values helm/agent-platform/values-production.yaml

helm-upgrade: ## Upgrade Helm release
	helm upgrade agent-platform helm/agent-platform \
		--namespace agent-platform \
		--values helm/agent-platform/values.yaml

helm-uninstall: ## Uninstall Helm release
	helm uninstall agent-platform --namespace agent-platform

helm-status: ## Check Helm release status
	helm status agent-platform --namespace agent-platform

helm-lint: ## Lint Helm chart
	helm lint helm/agent-platform

helm-template: ## Render Helm templates
	helm template agent-platform helm/agent-platform --values helm/agent-platform/values.yaml

##@ Deployment Scripts

deploy-docker: ## Deploy with Docker Compose (via script)
	chmod +x scripts/deploy.sh
	./scripts/deploy.sh docker-compose development

deploy-k8s: ## Deploy to Kubernetes (via script)
	chmod +x scripts/deploy.sh
	./scripts/deploy.sh kubernetes development

deploy-helm: ## Deploy with Helm (via script)
	chmod +x scripts/deploy.sh
	./scripts/deploy.sh helm development

deploy-prod: ## Deploy to production with Helm
	chmod +x scripts/deploy.sh
	./scripts/deploy.sh helm production

health-check: ## Run health checks on all services
	chmod +x scripts/check_health.sh
	./scripts/check_health.sh

##@ Monitoring

prometheus-up: ## Start Prometheus locally
	docker run -d --name prometheus -p 9090:9090 \
		-v $(PWD)/monitoring/prometheus/prometheus.yml:/etc/prometheus/prometheus.yml \
		prom/prometheus

grafana-up: ## Start Grafana locally
	docker run -d --name grafana -p 3000:3000 \
		-e GF_SECURITY_ADMIN_PASSWORD=admin \
		grafana/grafana

monitoring-up: ## Start Prometheus and Grafana
	@$(MAKE) prometheus-up
	@$(MAKE) grafana-up
	@echo "✓ Monitoring stack started"
	@echo "Prometheus: http://localhost:9090"
	@echo "Grafana: http://localhost:3000 (admin/admin)"

monitoring-down: ## Stop monitoring containers
	docker stop prometheus grafana || true
	docker rm prometheus grafana || true

##@ Examples

example-register: ## Run agent registration example
	python examples/01_agent_registration.py

example-orchestrate: ## Run task orchestration example
	python examples/02_task_orchestration.py

example-marketplace: ## Run marketplace example
	python examples/03_marketplace_interaction.py

run-examples: ## Run all examples
	@$(MAKE) example-register
	@$(MAKE) example-orchestrate
	@$(MAKE) example-marketplace

##@ Documentation

docs-serve: ## Serve documentation locally (if using mkdocs)
	@echo "Documentation files available in project root"
	@echo "- README.md"
	@echo "- AI_AGENT_ORCHESTRATION.md"
	@echo "- PROJECT_SUMMARY.md"
	@echo "- use-cases/*.md"

docs-view: ## Open main documentation
	@if command -v xdg-open > /dev/null; then \
		xdg-open AI_AGENT_ORCHESTRATION.md; \
	elif command -v open > /dev/null; then \
		open AI_AGENT_ORCHESTRATION.md; \
	else \
		echo "Please open AI_AGENT_ORCHESTRATION.md manually"; \
	fi

##@ Cleanup

clean: ## Clean build artifacts and cache files
	@echo "Cleaning build artifacts..."
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name "*.egg-info" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".mypy_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete
	find . -type f -name "*.pyo" -delete
	find . -type f -name ".coverage" -delete
	rm -rf htmlcov/
	rm -rf dist/
	rm -rf build/
	@echo "✓ Cleaned build artifacts"

clean-docker: ## Clean Docker resources
	@$(MAKE) docker-clean

clean-all: ## Clean everything (build artifacts, Docker, etc.)
	@$(MAKE) clean
	@$(MAKE) clean-docker
	@echo "✓ All resources cleaned"

##@ CI/CD

ci-test: ## Run tests as in CI pipeline
	pytest tests/ -v --cov=. --cov-report=xml --cov-report=term

ci-lint: ## Run linting as in CI pipeline
	flake8 api/ workers/ sdk/ cli/ tests/ --max-line-length=120 --exclude=venv,__pycache__
	black api/ workers/ sdk/ cli/ tests/ --line-length=120 --check

ci-build: ## Build as in CI pipeline
	@$(MAKE) docker-build

ci-all: ## Run full CI pipeline locally
	@$(MAKE) ci-lint
	@$(MAKE) ci-test
	@$(MAKE) ci-build
	@echo "✓ CI pipeline completed successfully"

##@ Utilities

version: ## Show version information
	@echo "AI Agent Orchestration Platform"
	@echo "Version: 1.0.0"
	@echo "Python: $$(python --version)"
	@echo "Docker: $$(docker --version)"
	@echo "Kubernetes: $$(kubectl version --client --short 2>/dev/null || echo 'not installed')"
	@echo "Helm: $$(helm version --short 2>/dev/null || echo 'not installed')"

env-check: ## Check if required tools are installed
	@echo "Checking environment..."
	@command -v python >/dev/null 2>&1 || { echo "✗ Python not installed"; exit 1; }
	@command -v docker >/dev/null 2>&1 || { echo "✗ Docker not installed"; exit 1; }
	@command -v docker-compose >/dev/null 2>&1 || { echo "✗ Docker Compose not installed"; exit 1; }
	@echo "✓ Python installed: $$(python --version)"
	@echo "✓ Docker installed: $$(docker --version)"
	@echo "✓ Docker Compose installed: $$(docker-compose --version)"
	@command -v kubectl >/dev/null 2>&1 && echo "✓ kubectl installed" || echo "⚠ kubectl not installed (optional)"
	@command -v helm >/dev/null 2>&1 && echo "✓ Helm installed" || echo "⚠ Helm not installed (optional)"
	@echo "✓ Environment check complete"

quick-start: ## Quick start: build and run everything
	@echo "Starting quick start..."
	@$(MAKE) env-check
	@$(MAKE) install
	@$(MAKE) db-setup
	@$(MAKE) db-seed
	@$(MAKE) docker-build
	@$(MAKE) docker-up
	@$(MAKE) health-check
	@echo ""
	@echo "✓ Quick start complete!"
	@echo ""
	@echo "Services running:"
	@echo "  API Gateway:      http://localhost:8000"
	@echo "  Registry Service: http://localhost:8001"
	@echo "  Marketplace:      http://localhost:8002"
	@echo "  Orchestrator:     http://localhost:8003"
	@echo ""
	@echo "Next steps:"
	@echo "  make run-examples    # Run example scripts"
	@echo "  make test            # Run tests"
	@echo "  make monitoring-up   # Start Prometheus/Grafana"

.PHONY: all
all: clean install test build ## Run clean, install, test, and build
