#!/usr/bin/env bash
set -euo pipefail

echo "╔═══════════════════════════════════════════════╗"
echo "║        ScamShield — Version Information       ║"
echo "╚═══════════════════════════════════════════════╝"

BASE_URL="${1:-http://localhost:8000}"
ROOT_DIR="$(cd "$(dirname "$0")/.." && pwd)"

echo ""
echo "━━━ VERSION File ━━━"
if [ -f "$ROOT_DIR/VERSION" ]; then
  echo "  $(cat "$ROOT_DIR/VERSION")"
else
  echo "  Not found"
fi

echo ""
echo "━━━ Backend API Version ━━━"
if [ -f "$ROOT_DIR/backend/core/constants.py" ]; then
  grep "^API_VERSION" "$ROOT_DIR/backend/core/constants.py" | sed 's/.*= //; s/"//g' | while read -r v; do echo "  $v"; done
else
  echo "  constants.py not found"
fi

echo ""
echo "━━━ Running Service Version ━━━"
if health=$(curl -sf "$BASE_URL/health" 2>/dev/null); then
  echo "$health" | python3 -c "
import json, sys
data = json.load(sys.stdin)
print(f\"  Service: {data.get('service')}\")
print(f\"  API Version: {data.get('version')}\")
print(f\"  Build Version: {data.get('build_version', 'N/A')}\")
print(f\"  Uptime: {data.get('uptime_seconds', 0)}s\")
print(f\"  Startup: {data.get('startup_timestamp', 'N/A')}\")
" 2>/dev/null || echo "$health" | python -m json.tool 2>/dev/null | head -10
else
  echo "  Cannot reach $BASE_URL/health"
fi

echo ""
echo "━━━ Docker Images ━━━"
if command -v docker &>/dev/null; then
  docker images --filter "reference=scamshield*" --format "table {{.Repository}}\t{{.Tag}}\t{{.ID}}\t{{.CreatedAt}}" 2>/dev/null || echo "  No scamshield images found"
else
  echo "  Docker not available"
fi

echo ""
echo "━━━ Frontend Version ━━━"
if [ -f "$ROOT_DIR/frontend/package.json" ]; then
  grep '"version"' "$ROOT_DIR/frontend/package.json" | sed 's/.*": "//; s/",//' | while read -r v; do echo "  package.json: $v"; done
fi
if [ -f "$ROOT_DIR/frontend/dist/index.html" ]; then
  echo "  Frontend build exists"
  ls -la "$ROOT_DIR/frontend/dist/" 2>/dev/null | head -5
fi
