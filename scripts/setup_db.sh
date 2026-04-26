#!/bin/bash

#
# Database Setup Script for AI Agent Orchestration Platform
#
# Initializes PostgreSQL database with schema and optional seed data
#

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m'

log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

# Database configuration
DB_HOST="${DB_HOST:-localhost}"
DB_PORT="${DB_PORT:-5432}"
DB_NAME="${DB_NAME:-agent_platform}"
DB_USER="${DB_USER:-platform_admin}"
DB_PASSWORD="${DB_PASSWORD:-changeme_postgres_password}"

log_info "Setting up database: $DB_NAME on $DB_HOST:$DB_PORT"

# Check if PostgreSQL is available
if ! command -v psql &> /dev/null; then
    log_error "psql command not found. Please install PostgreSQL client."
    exit 1
fi

# Create database if it doesn't exist
log_info "Creating database if not exists..."
PGPASSWORD=$DB_PASSWORD psql -h $DB_HOST -p $DB_PORT -U $DB_USER -d postgres -c "CREATE DATABASE $DB_NAME;" 2>/dev/null || log_info "Database already exists"

# Apply schema
log_info "Applying database schema..."
PGPASSWORD=$DB_PASSWORD psql -h $DB_HOST -p $DB_PORT -U $DB_USER -d $DB_NAME -f "$PROJECT_ROOT/database/schema.sql"

log_success "Schema applied successfully!"

# Optionally load seed data
read -p "Load seed data? (y/N): " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    log_info "Loading seed data..."
    PGPASSWORD=$DB_PASSWORD psql -h $DB_HOST -p $DB_PORT -U $DB_USER -d $DB_NAME -f "$PROJECT_ROOT/database/seed.sql"
    log_success "Seed data loaded!"
fi

# Verify setup
log_info "Verifying database setup..."
TABLE_COUNT=$(PGPASSWORD=$DB_PASSWORD psql -h $DB_HOST -p $DB_PORT -U $DB_USER -d $DB_NAME -t -c "SELECT COUNT(*) FROM information_schema.tables WHERE table_schema='public';" | tr -d ' ')

log_success "Database setup complete! Tables created: $TABLE_COUNT"
