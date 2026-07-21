#!/bin/bash

# Welfare Facilities DB - Verification Script (bash version)
# このスクリプトは、セットアップが正常に完了したかを確認します

set -e

GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

PASSED=0
FAILED=0
WARNINGS=0

check_pass() { 
    echo -e "${GREEN}✓ PASS${NC} $1"
    ((PASSED++))
}

check_fail() {
    echo -e "${RED}✗ FAIL${NC} $1"
    ((FAILED++))
}

check_warn() {
    echo -e "${YELLOW}⚠ WARN${NC} $1"
    ((WARNINGS++))
}

echo -e "${BLUE}=== Welfare Facilities DB - Setup Verification ===${NC}"
echo ""

# 1. Docker コンテナ確認
echo -e "${BLUE}1. Docker Containers${NC}"
if docker-compose ps | grep -q "welfare-db"; then
    check_pass "PostgreSQL container (welfare-db) is running"
else
    check_fail "PostgreSQL container (welfare-db) is not running"
fi

if docker-compose ps | grep -q "welfare-api"; then
    check_pass "Backend container (welfare-api) is running"
else
    check_fail "Backend container (welfare-api) is not running"
fi

if docker-compose ps | grep -q "welfare-ui"; then
    check_pass "Frontend container (welfare-ui) is running"
else
    check_fail "Frontend container (welfare-ui) is not running"
fi

echo ""

# 2. ポート確認
echo -e "${BLUE}2. Port Availability${NC}"

check_port() {
    local port=$1
    local name=$2
    if curl -s http://localhost:$port >/dev/null 2>&1 || nc -zv localhost $port 2>/dev/null; then
        check_pass "Port $port ($name) is accessible"
        return 0
    else
        check_warn "Port $port ($name) is not accessible"
        return 1
    fi
}

check_port 8000 "Backend API" || true
check_port 5173 "Frontend" || true
check_port 5433 "PostgreSQL" || true

echo ""

# 3. ヘルスチェック
echo -e "${BLUE}3. Health Checks${NC}"

if curl -s http://localhost:8000/health | grep -q "healthy"; then
    check_pass "Backend API health check"
else
    check_fail "Backend API health check"
fi

if docker-compose exec -T db pg_isready -U dev &>/dev/null; then
    check_pass "PostgreSQL is ready"
else
    check_fail "PostgreSQL is not ready"
fi

echo ""

# 4. API エンドポイント
echo -e "${BLUE}4. API Endpoints${NC}"

if curl -s http://localhost:8000/api/corporations >/dev/null 2>&1; then
    check_pass "GET /api/corporations endpoint"
else
    check_warn "GET /api/corporations endpoint not responding"
fi

echo ""

# 5.環境変数
echo -e "${BLUE}5. Environment Configuration${NC}"

if [ -f backend/.env ]; then
    check_pass "backend/.env file exists"
else
    check_fail "backend/.env file not found"
fi

if grep -q "DATABASE_URL" backend/.env; then
    check_pass "DATABASE_URL is configured"
else
    check_fail "DATABASE_URL is not configured"
fi

echo ""

# 6. ボリューム
echo -e "${BLUE}6. Docker Volumes${NC}"

if docker volume ls | grep -q "pgdata"; then
    check_pass "PostgreSQL volume (pgdata) exists"
else
    check_warn "PostgreSQL volume (pgdata) not found"
fi

echo ""

# 最終結果
echo -e "${BLUE}=== Summary ===${NC}"
echo -e "${GREEN}PASSED:  $PASSED${NC}"
if [ $FAILED -gt 0 ]; then
    echo -e "${RED}FAILED:  $FAILED${NC}"
fi
if [ $WARNINGS -gt 0 ]; then
    echo -e "${YELLOW}WARNINGS: $WARNINGS${NC}"
fi

echo ""

if [ $FAILED -eq 0 ]; then
    echo -e "${GREEN}✓ Setup verification completed successfully!${NC}"
    echo ""
    echo "Service URLs:"
    echo "  Frontend:   http://localhost:5173"
    echo "  Backend:    http://localhost:8000"
    echo "  API Docs:   http://localhost:8000/docs"
    exit 0
else
    echo -e "${RED}✗ Setup verification found issues. See above for details.${NC}"
    exit 1
fi
