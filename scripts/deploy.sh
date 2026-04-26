#!/bin/bash

#
# Deploy Script for AI Agent Orchestration Platform
#
# Usage:
#   ./deploy.sh [environment] [method]
#
# Examples:
#   ./deploy.sh dev docker-compose
#   ./deploy.sh staging kubernetes
#   ./deploy.sh production helm
#

set -e  # Exit on error

# ============================================================================
# Configuration
# ============================================================================

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Default values
ENVIRONMENT="${1:-dev}"
DEPLOY_METHOD="${2:-docker-compose}"

# ============================================================================
# Helper Functions
# ============================================================================

log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

check_command() {
    if ! command -v $1 &> /dev/null; then
        log_error "$1 is not installed. Please install it first."
        exit 1
    fi
}

# ============================================================================
# Pre-flight Checks
# ============================================================================

log_info "Starting deployment for environment: $ENVIRONMENT using $DEPLOY_METHOD"

# Check required commands based on deployment method
case $DEPLOY_METHOD in
    docker-compose)
        check_command docker
        check_command docker-compose
        ;;
    kubernetes)
        check_command kubectl
        ;;
    helm)
        check_command helm
        check_command kubectl
        ;;
    *)
        log_error "Unknown deployment method: $DEPLOY_METHOD"
        echo "Supported methods: docker-compose, kubernetes, helm"
        exit 1
        ;;
esac

# ============================================================================
# Docker Compose Deployment
# ============================================================================

deploy_docker_compose() {
    log_info "Deploying with Docker Compose..."

    cd "$PROJECT_ROOT/docker"

    # Build images
    log_info "Building Docker images..."
    docker-compose build

    # Start services
    log_info "Starting services..."
    docker-compose up -d

    # Wait for services to be healthy
    log_info "Waiting for services to be ready..."
    sleep 10

    # Check health
    log_info "Checking service health..."
    docker-compose ps

    log_success "Docker Compose deployment complete!"
    log_info "Access the platform at: http://localhost:8000"
}

# ============================================================================
# Kubernetes Deployment
# ============================================================================

deploy_kubernetes() {
    log_info "Deploying to Kubernetes..."

    cd "$PROJECT_ROOT/k8s"

    # Create namespace if it doesn't exist
    log_info "Creating namespace: agent-platform..."
    kubectl create namespace agent-platform --dry-run=client -o yaml | kubectl apply -f -

    # Apply manifests in order
    log_info "Applying Kubernetes manifests..."

    # Infrastructure first
    kubectl apply -f 01-namespace.yaml
    kubectl apply -f 02-configmap.yaml
    kubectl apply -f 03-secrets.yaml
    kubectl apply -f 04-storage.yaml

    # Databases and caches
    kubectl apply -f 05-postgres.yaml
    kubectl apply -f 06-redis.yaml
    kubectl apply -f 07-rabbitmq.yaml

    # Wait for databases to be ready
    log_info "Waiting for databases to be ready..."
    kubectl wait --for=condition=ready pod -l app=postgres -n agent-platform --timeout=180s || true
    sleep 5

    # Core services
    kubectl apply -f 08-registry-service.yaml
    kubectl apply -f 09-marketplace-service.yaml
    kubectl apply -f 10-orchestrator-service.yaml

    # Agent workers
    kubectl apply -f 11-agent-sandbox.yaml

    # API Gateway and Ingress
    kubectl apply -f 12-api-gateway-ingress.yaml

    # Monitoring
    kubectl apply -f 13-monitoring.yaml

    # Wait for services to be ready
    log_info "Waiting for services to be ready..."
    kubectl wait --for=condition=ready pod -l tier=backend -n agent-platform --timeout=300s || true

    # Show status
    log_info "Deployment status:"
    kubectl get pods -n agent-platform

    log_success "Kubernetes deployment complete!"

    # Get ingress URL
    INGRESS_IP=$(kubectl get ingress -n agent-platform -o jsonpath='{.items[0].status.loadBalancer.ingress[0].ip}' 2>/dev/null || echo "pending")
    if [ "$INGRESS_IP" != "pending" ]; then
        log_info "Platform accessible at: http://$INGRESS_IP"
    else
        log_warning "Ingress IP pending. Check with: kubectl get ingress -n agent-platform"
    fi
}

# ============================================================================
# Helm Deployment
# ============================================================================

deploy_helm() {
    log_info "Deploying with Helm..."

    cd "$PROJECT_ROOT/helm"

    # Create namespace
    kubectl create namespace agent-platform --dry-run=client -o yaml | kubectl apply -f -

    # Install or upgrade Helm release
    log_info "Installing Helm chart..."

    RELEASE_NAME="agent-platform"
    VALUES_FILE="agent-platform/values.yaml"

    # Use environment-specific values if available
    if [ -f "agent-platform/values-$ENVIRONMENT.yaml" ]; then
        VALUES_FILE="agent-platform/values-$ENVIRONMENT.yaml"
        log_info "Using environment-specific values: $VALUES_FILE"
    fi

    helm upgrade --install $RELEASE_NAME ./agent-platform \
        --namespace agent-platform \
        --values $VALUES_FILE \
        --wait \
        --timeout 10m

    # Show status
    log_info "Helm release status:"
    helm status $RELEASE_NAME -n agent-platform

    log_info "Deployed resources:"
    kubectl get all -n agent-platform

    log_success "Helm deployment complete!"
}

# ============================================================================
# Post-Deployment Steps
# ============================================================================

post_deployment() {
    log_info "Running post-deployment steps..."

    case $DEPLOY_METHOD in
        docker-compose)
            # Initialize database
            log_info "Initializing database..."
            docker-compose exec -T postgres psql -U platform_admin -d agent_platform < "$PROJECT_ROOT/database/schema.sql" || log_warning "Database may already be initialized"

            # Load seed data (optional)
            if [ "$ENVIRONMENT" = "dev" ]; then
                log_info "Loading seed data..."
                docker-compose exec -T postgres psql -U platform_admin -d agent_platform < "$PROJECT_ROOT/database/seed.sql" || true
            fi
            ;;

        kubernetes|helm)
            # Run database initialization job
            log_info "Database initialization should be handled by init containers"
            ;;
    esac

    log_success "Post-deployment steps complete!"
}

# ============================================================================
# Health Check
# ============================================================================

health_check() {
    log_info "Performing health check..."

    case $DEPLOY_METHOD in
        docker-compose)
            curl -f http://localhost:8000/health || log_warning "Health check failed"
            ;;

        kubernetes|helm)
            # Port forward for health check
            kubectl port-forward -n agent-platform svc/api-gateway 8000:8000 &
            PF_PID=$!
            sleep 3
            curl -f http://localhost:8000/health || log_warning "Health check failed"
            kill $PF_PID 2>/dev/null || true
            ;;
    esac
}

# ============================================================================
# Main Execution
# ============================================================================

main() {
    log_info "Deploying AI Agent Orchestration Platform"
    log_info "Environment: $ENVIRONMENT"
    log_info "Method: $DEPLOY_METHOD"
    echo ""

    # Deploy based on method
    case $DEPLOY_METHOD in
        docker-compose)
            deploy_docker_compose
            ;;
        kubernetes)
            deploy_kubernetes
            ;;
        helm)
            deploy_helm
            ;;
    esac

    # Post-deployment
    post_deployment

    # Health check
    health_check

    echo ""
    log_success "🎉 Deployment completed successfully!"
    echo ""
    log_info "Next steps:"
    echo "  1. Check deployment status: kubectl get pods -n agent-platform"
    echo "  2. View logs: kubectl logs -f deployment/api-gateway -n agent-platform"
    echo "  3. Access API docs: http://localhost:8000/docs"
    echo "  4. Run tests: pytest tests/"
    echo ""
}

# Run main function
main

# ============================================================================
# Cleanup on exit
# ============================================================================

cleanup() {
    log_info "Cleaning up..."
}

trap cleanup EXIT
