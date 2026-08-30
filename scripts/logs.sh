#!/usr/bin/env bash
set -euo pipefail

SERVICE="${1:-}"

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"

cd "$PROJECT_DIR"

if [ -z "$SERVICE" ]; then
  echo "Usage: $0 {backend|frontend}"
  echo ""
  echo "Examples:"
  echo "  $0 backend    # Show backend logs (follow)"
  echo "  $0 frontend   # Show frontend logs (follow)"
  echo "  $0 backend --tail=100  # Last 100 lines"
  exit 1
fi

case "$SERVICE" in
  backend|frontend)
    shift
    docker compose logs --follow "$@" "kaaval-$SERVICE"
    ;;
  *)
    echo "Unknown service: $SERVICE. Use 'backend' or 'frontend'."
    exit 1
    ;;
esac
