#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"

cd "$PROJECT_DIR"

echo "Wary — Health Check"
echo "========================"
echo ""

# Check backend
echo -n "Backend (port 8000) ........ "
if curl -sf http://localhost:8000/health > /dev/null 2>&1; then
  echo "HEALTHY"
  echo ""
  curl -s http://localhost:8000/health | python -m json.tool 2>/dev/null || curl -s http://localhost:8000/health
else
  echo "DOWN"
fi

echo ""

# Check frontend
echo -n "Frontend (port 80) ......... "
if curl -sf http://localhost:80/ > /dev/null 2>&1; then
  echo "HEALTHY"
else
  echo "DOWN"
fi

echo ""

# Check API through Nginx
echo -n "API via Nginx .............. "
if curl -sf http://localhost:80/api/health > /dev/null 2>&1; then
  echo "HEALTHY"
else
  echo "DOWN"
fi

echo ""

# Check Swagger docs
echo -n "Swagger docs ............... "
if curl -sf http://localhost:80/docs > /dev/null 2>&1; then
  echo "HEALTHY"
else
  echo "DOWN"
fi

echo ""

# Container status
echo "Container Status:"
docker compose ps 2>/dev/null || echo "  (docker compose not available)"
