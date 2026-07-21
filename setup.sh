#!/bin/bash

# Welfare Facilities DB - Automated Setup Script

set -e

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

log_info() { echo -e "${BLUE}[INFO]${NC} $1"; }
log_success() { echo -e "${GREEN}[SUCCESS]${NC} $1"; }
log_warning() { echo -e "${YELLOW}[WARNING]${NC} $1"; }
log_error() { echo -e "${RED}[ERROR]${NC} $1"; }

PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

log_info "Project directory: $PROJECT_DIR"

# Check prerequisites
log_info "Checking prerequisites..."
command -v docker >/dev/null || { log_error "docker not found"; exit 1; }
command -v docker-compose >/dev/null || { log_error "docker-compose not found"; exit 1; }

log_success "docker: $(docker --version)"
log_success "docker-compose: $(docker-compose --version)"

# Setup .env file
cd "$PROJECT_DIR"

log_info "Setting up environment variables..."
if [ ! -f backend/.env ]; then
    if [ -f backend/.env.example ]; then
        cp backend/.env.example backend/.env
        log_success "Created backend/.env from backend/.env.example"
    else
        log_error "backend/.env.example not found"
        exit 1
    fi
else
    log_info "backend/.env already exists"
fi

# Build Docker images
log_info "Building Docker Compose images..."
docker-compose build || { log_error "Docker Compose build failed"; exit 1; }
log_success "Docker Compose images built"

# Start containers
log_info "Starting containers..."
docker-compose up -d || { log_error "Failed to start containers"; exit 1; }
log_success "Containers started"

# Wait for PostgreSQL
log_info "Waiting for PostgreSQL to be ready (max 60 seconds)..."
ATTEMPT=0
while [ $ATTEMPT -lt 60 ]; do
    if docker-compose exec -T db pg_isready -U dev &>/dev/null; then
        log_success "PostgreSQL is ready"
        break
    fi
    ATTEMPT=$((ATTEMPT + 1))
    [ $((ATTEMPT % 10)) -eq 0 ] && log_info "Waiting... ($ATTEMPT/60)"
    sleep 1
done

if [ $ATTEMPT -eq 60 ]; then
    log_error "PostgreSQL startup timeout"
    log_error "Check logs: docker-compose logs db"
    exit 1
fi

# Initialize database
log_info "Initializing database..."
docker-compose exec -T backend python scripts/init_db.py || { log_error "Database initialization failed"; exit 1; }
log_success "Database initialized"

# Wait for Backend API
log_info "Waiting for Backend API (max 30 seconds)..."
ATTEMPT=0
while [ $ATTEMPT -lt 30 ]; do
    if curl -s http://localhost:8000/health >/dev/null 2>&1; then
        log_success "Backend API is ready"
        break
    fi
    ATTEMPT=$((ATTEMPT + 1))
    [ $((ATTEMPT % 5)) -eq 0 ] && log_info "Waiting... ($ATTEMPT/30)"
    sleep 1
done

if [ $ATTEMPT -eq 30 ]; then
    log_warning "Backend API health check failed"
    log_info "Check logs: docker-compose logs backend"
fi

# Final summary
echo ""
log_success "Setup complete!"
echo ""
echo -e "${BLUE}=== Service URLs ===${NC}"
echo "  Frontend:        http://localhost:5173"
echo "  Backend API:     http://localhost:8000"
echo "  API Docs:        http://localhost:8000/docs"
echo "  Prometheus:      http://localhost:9091"
echo "  Grafana:         http://localhost:3002 (admin/admin)"
echo ""
echo -e "${BLUE}=== Next Steps ===${NC}"
echo "1. Open http://localhost:5173 in your browser"
echo "2. Check API docs at http://localhost:8000/docs"
echo "3. Import CSV data (see README.md)"
echo ""

exit 0
