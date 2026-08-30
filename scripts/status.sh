#!/usr/bin/env bash
set -euo pipefail

echo "╔═══════════════════════════════════════════════╗"
echo "║           Kaaval — Service Status              ║"
echo "╚═══════════════════════════════════════════════╝"

BASE_URL="${1:-http://localhost:8000}"
FRONTEND_URL="${2:-http://localhost:80}"

echo ""
echo "━━━ Backend Health ━━━"
if health=$(curl -sf "$BASE_URL/health" 2>/dev/null); then
  echo "$health" | python -m json.tool 2>/dev/null || echo "$health"
else
  echo "FAIL: Cannot reach $BASE_URL/health"
fi

echo ""
echo "━━━ Backend Readiness ━━━"
if ready=$(curl -sf "$BASE_URL/ready" 2>/dev/null); then
  echo "$ready" | python -m json.tool 2>/dev/null || echo "$ready"
else
  echo "FAIL: Cannot reach $BASE_URL/ready"
fi

echo ""
echo "━━━ Backend Liveness ━━━"
if live=$(curl -sf "$BASE_URL/live" 2>/dev/null); then
  echo "$live" | python -m json.tool 2>/dev/null || echo "$live"
else
  echo "FAIL: Cannot reach $BASE_URL/live"
fi

echo ""
echo "━━━ Backend Metrics ━━━"
if metrics=$(curl -sf "$BASE_URL/metrics" 2>/dev/null); then
  echo "$metrics" | python -m json.tool 2>/dev/null || echo "$metrics"
else
  echo "FAIL: Cannot reach $BASE_URL/metrics"
fi

echo ""
echo "━━━ Frontend ━━━"
if frontend_status=$(curl -sf -o /dev/null -w "%{http_code}" "$FRONTEND_URL" 2>/dev/null); then
  echo "Frontend: HTTP $frontend_status"
else
  echo "FAIL: Cannot reach $FRONTEND_URL"
fi

echo ""
echo "━━━ Docker Containers ━━━"
if command -v docker &>/dev/null; then
  docker compose ps 2>/dev/null || docker ps --filter "name=kaaval" --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}" 2>/dev/null || echo "Docker not available"
else
  echo "Docker not available"
fi
