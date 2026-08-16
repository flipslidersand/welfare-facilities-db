#!/bin/bash
set -e

API_BASE="${API_BASE:-http://localhost:8000}"
API_KEY="${API_KEY:-changeme}"

echo "🧪 API キー統合テスト"
echo "================================"

# Color output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

test_count=0
pass_count=0

# Test helper
run_test() {
    local name=$1
    local expected_code=$2
    local method=$3
    local endpoint=$4
    local data=$5
    local extra_headers=$6

    test_count=$((test_count + 1))
    echo -e "\n${YELLOW}[${test_count}] ${name}${NC}"

    if [ -n "$data" ]; then
        response=$(curl -s -w "\n%{http_code}" -X "$method" \
            "$API_BASE$endpoint" \
            -H "X-API-Key: $API_KEY" \
            -H "Content-Type: application/json" \
            $extra_headers \
            -d "$data")
    else
        response=$(curl -s -w "\n%{http_code}" -X "$method" \
            "$API_BASE$endpoint" \
            -H "X-API-Key: $API_KEY" \
            $extra_headers)
    fi

    http_code=$(echo "$response" | tail -n1)
    body=$(echo "$response" | head -n-1)

    if [ "$http_code" = "$expected_code" ]; then
        echo -e "${GREEN}✅ Pass${NC} (HTTP $http_code)"
        pass_count=$((pass_count + 1))
        echo "$body" | jq . 2>/dev/null || echo "$body"
    else
        echo -e "${RED}❌ Fail${NC} (Expected $expected_code, got $http_code)"
        echo "$body" | jq . 2>/dev/null || echo "$body"
    fi
}

echo ""
echo "📝 1. 認証なしでアクセス（401 期待）"
test_count=$((test_count + 1))
echo -e "\n${YELLOW}[${test_count}] GET /api-keys (認証なし)${NC}"
response=$(curl -s -w "\n%{http_code}" "$API_BASE/api-keys")
http_code=$(echo "$response" | tail -n1)
body=$(echo "$response" | head -n-1)
if [ "$http_code" = "401" ]; then
    echo -e "${GREEN}✅ Pass${NC} (HTTP 401)"
    pass_count=$((pass_count + 1))
else
    echo -e "${RED}❌ Fail${NC} (Expected 401, got $http_code)"
fi

echo ""
echo "📝 2. API キー一覧取得（GET）"
run_test "GET /api-keys" "200" "GET" "/api-keys" "" ""

echo ""
echo "📝 3. API キー作成（POST）"
KEY_NAME="test-key-$(date +%s)"
run_test "POST /api-keys" "201" "POST" "/api-keys" "{\"name\":\"$KEY_NAME\"}" ""

echo ""
echo "📝 4. API キー作成（有効期限付き）"
EXPIRES_AT=$(date -u -d "+30 days" +"%Y-%m-%dT%H:%M:%S" 2>/dev/null || date -u -v+30d +"%Y-%m-%dT%H:%M:%S")
run_test "POST /api-keys (expires_at)" "201" "POST" "/api-keys" "{\"name\":\"$KEY_NAME-exp\",\"expires_at\":\"${EXPIRES_AT}Z\"}" ""

echo ""
echo "📝 5. API キー更新（PATCH）"
run_test "PATCH /api-keys/1 (名前変更)" "200" "PATCH" "/api-keys/1" "{\"name\":\"updated-key\"}" ""

echo ""
echo "📝 6. API キー更新（無効化）"
run_test "PATCH /api-keys/1 (無効化)" "200" "PATCH" "/api-keys/1" "{\"is_active\":false}" ""

echo ""
echo "📝 7. API キー削除（DELETE）"
run_test "DELETE /api-keys/1" "204" "DELETE" "/api-keys/1" "" ""

echo ""
echo "📝 8. 存在しないキー取得（404）"
run_test "PATCH /api-keys/99999" "404" "PATCH" "/api-keys/99999" "{\"name\":\"test\"}" ""

echo ""
echo "================================"
echo -e "📊 結果: ${GREEN}${pass_count}/${test_count}${NC} テスト成功"

if [ $pass_count -eq $test_count ]; then
    echo -e "${GREEN}✅ 全テスト成功！${NC}"
    exit 0
else
    echo -e "${RED}❌ テスト失敗${NC}"
    exit 1
fi
