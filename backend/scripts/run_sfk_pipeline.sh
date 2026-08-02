#!/usr/bin/env bash
# WAM NET 障害福祉サービス等情報公表 — download → import pipeline
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
BACKEND_DIR="$(dirname "$SCRIPT_DIR")"
YEARMONTH="${1:-}"
TMP_DIR="${TMPDIR:-/tmp}/sfk_csv_${YEARMONTH:-auto}"

cd "$BACKEND_DIR"

# Calculate default yearmonth if not given (3-month lag)
if [ -z "$YEARMONTH" ]; then
  python3 -c "
from datetime import date
t = date.today()
m, y = t.month - 3, t.year
if m <= 0: m += 12; y -= 1
print(f'{y}{m:02d}')
" | read -r YEARMONTH || true
  YEARMONTH=$(python3 -c "
from datetime import date
t = date.today()
m, y = t.month - 3, t.year
if m <= 0: m += 12; y -= 1
print(f'{y}{m:02d}')
")
fi

TMP_DIR="/tmp/sfk_csv_${YEARMONTH}"

echo "=== SFK Pipeline: ${YEARMONTH} ==="
echo "Step 1: Download CSVs from WAM NET"
python3 "$SCRIPT_DIR/download_sfk_csv.py" "$YEARMONTH" "$TMP_DIR"

CSV_COUNT=$(find "$TMP_DIR" -name "*.csv" 2>/dev/null | wc -l)
if [ "$CSV_COUNT" -eq 0 ]; then
  echo "❌ No CSV files found in $TMP_DIR"
  exit 1
fi
echo "  → ${CSV_COUNT} CSV files ready"

echo ""
echo "Step 2: Import CSVs to database"
python3 "$SCRIPT_DIR/import_sfk_csv.py" "$TMP_DIR"

echo ""
echo "Step 3: Cleanup temp files"
rm -rf "$TMP_DIR"

echo ""
echo "✓ Pipeline complete for yearmonth=${YEARMONTH}"
