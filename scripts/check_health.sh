#!/bin/bash

#
# Health Check Script for AI Agent Orchestration Platform
#
# Checks health of all services
#

set -e

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

API_URL="${API_URL:-http://localhost:8000}"
TIMEOUT=5

echo -e "${BLUE}╔════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║  AI Agent Platform - Health Check             ║${NC}"
echo -e "${BLUE}╚════════════════════════════════════════════════╝${NC}"
echo ""

check_service() {
    local name=$1
    local url=$2
    local start_time=$(date +%s%3N)

    if response=$(curl -s -f -m $TIMEOUT "$url" 2>/dev/null); then
        local end_time=$(date +%s%3N)
        local duration=$((end_time - start_time))
        echo -e "${GREEN}✓${NC} $name ${BLUE}(${duration}ms)${NC}"
        return 0
    else
        echo -e "${RED}✗${NC} $name ${RED}(Failed)${NC}"
        return 1
    fi
}

# Check main services
echo "Checking services..."
echo "-------------------"

FAILURES=0

check_service "API Gateway      " "$API_URL/health" || ((FAILURES++))
check_service "Registry Service " "$API_URL/registry/health" || ((FAILURES++))
check_service "Marketplace      " "$API_URL/marketplace/health" || ((FAILURES++))
check_service "Orchestrator     " "$API_URL/orchestrator/health" || ((FAILURES++))

echo ""
echo "Checking infrastructure..."
echo "--------------------------"

# Check if running in Docker Compose
if command -v docker-compose &> /dev/null && docker-compose ps &> /dev/null; then
    POSTGRES_STATUS=$(docker-compose ps postgres 2>/dev/null | grep -c "Up" || echo "0")
    REDIS_STATUS=$(docker-compose ps redis 2>/dev/null | grep -c "Up" || echo "0")
    RABBITMQ_STATUS=$(docker-compose ps rabbitmq 2>/dev/null | grep -c "Up" || echo "0")

    [ "$POSTGRES_STATUS" = "1" ] && echo -e "${GREEN}✓${NC} PostgreSQL" || (echo -e "${RED}✗${NC} PostgreSQL" && ((FAILURES++)))
    [ "$REDIS_STATUS" = "1" ] && echo -e "${GREEN}✓${NC} Redis" || (echo -e "${RED}✗${NC} Redis" && ((FAILURES++)))
    [ "$RABBITMQ_STATUS" = "1" ] && echo -e "${GREEN}✓${NC} RabbitMQ" || (echo -e "${RED}✗${NC} RabbitMQ" && ((FAILURES++)))
fi

# Check if running in Kubernetes
if command -v kubectl &> /dev/null && kubectl get namespace agent-platform &> /dev/null; then
    echo ""
    echo "Kubernetes Pods:"
    kubectl get pods -n agent-platform | grep -E "NAME|Running|Error|CrashLoop" || true
fi

echo ""
echo "================================"

if [ $FAILURES -eq 0 ]; then
    echo -e "${GREEN}All services healthy! ✓${NC}"
    exit 0
else
    echo -e "${RED}$FAILURES service(s) unhealthy ✗${NC}"
    exit 1
fi
