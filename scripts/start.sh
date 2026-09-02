#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"

cd "$PROJECT_DIR"

# Ensure .env exists
if [ ! -f ".env" ]; then
  if [ -f ".env.example" ]; then
    echo "No .env found. Copying .env.example to .env ..."
    cp .env.example .env
    echo "Edit .env with your settings before running again."
    exit 1
  else
    echo "Error: No .env or .env.example found."
    exit 1
  fi
fi

echo "Building and starting Wary ..."
docker compose up --build -d

echo "Waiting for services to become healthy ..."

# Wait for backend
echo -n "  Backend "
for i in $(seq 1 30); do
  if curl -sf http://localhost:8000/health > /dev/null 2>&1; then
    echo " healthy"
    break
  fi
  echo -n "."
  sleep 2
done

# Wait for frontend
echo -n "  Frontend "
for i in $(seq 1 30); do
  if curl -sf http://localhost:80/ > /dev/null 2>&1; then
    echo " healthy"
    break
  fi
  echo -n "."
  sleep 2
done

echo ""
echo "Wary is running:"
echo "  Frontend : http://localhost:80"
echo "  API      : http://localhost:80/api"
echo "  Docs     : http://localhost:80/docs"
echo "  Health   : http://localhost:80/health"
