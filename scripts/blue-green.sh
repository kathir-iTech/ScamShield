#!/usr/bin/env bash
set -euo pipefail

# Blue/green slot switcher for the ScamShield edge (nginx) deployment.
# Usage: scripts/blue-green.sh <command> [slot]
#
# Commands:
#   up <slot>       Start the backend service for the slot (a or b)
#   health <slot>   Poll /health and /ready until healthy (non-zero on failure)
#   switch <slot>   Rewrite the active upstream and reload nginx
#   rollback        Switch back to the previous slot (no-op if there is none)
#   current         Print the active slot
#
# Environment:
#   ACTIVE_FILE       Slot state file          (default: <repo>/logs/active-slot)
#   NGINX_UPSTREAM    Upstream conf path       (default: /etc/nginx/slots/active.conf
#                                               inside NGINX_CONTAINER; a host path
#                       is used instead when the file exists locally)
#   NGINX_CONTAINER   nginx container name     (default: wary-nginx)
#   NGINX_TEST_CMD    Config test command      (default: docker exec <nginx> nginx -t)
#   NGINX_RELOAD_CMD  Reload command           (default: docker exec <nginx> nginx -s reload)
#   SLOT_A            Slot a upstream address  (default: backend:8000)
#   SLOT_B            Slot b upstream address  (default: backend-b:8000)
#   SERVICE_A         Slot a compose service   (default: backend-a, falls back to backend)
#   SERVICE_B         Slot b compose service   (default: backend-b, falls back to backend)
#   HEALTH_URL        Base URL when a slot has no specific one (default: http://localhost:8000)
#   HEALTH_URL_A      Slot a health base URL   (default: $HEALTH_URL)
#   HEALTH_URL_B      Slot b health base URL   (default: $HEALTH_URL)
#   TIMEOUT           Health poll budget in seconds (default: 60)
#   POLL_INTERVAL     Seconds between polls    (default: 2)

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"

ACTIVE_FILE="${ACTIVE_FILE:-$PROJECT_DIR/logs/active-slot}"
NGINX_UPSTREAM="${NGINX_UPSTREAM:-/etc/nginx/slots/active.conf}"
NGINX_CONTAINER="${NGINX_CONTAINER:-wary-nginx}"
NGINX_TEST_CMD="${NGINX_TEST_CMD:-docker exec $NGINX_CONTAINER nginx -t}"
NGINX_RELOAD_CMD="${NGINX_RELOAD_CMD:-docker exec $NGINX_CONTAINER nginx -s reload}"
SLOT_A="${SLOT_A:-backend:8000}"
SLOT_B="${SLOT_B:-backend-b:8000}"
SERVICE_A="${SERVICE_A:-backend-a}"
SERVICE_B="${SERVICE_B:-backend-b}"
HEALTH_URL="${HEALTH_URL:-http://localhost:8000}"
HEALTH_URL_A="${HEALTH_URL_A:-$HEALTH_URL}"
HEALTH_URL_B="${HEALTH_URL_B:-$HEALTH_URL}"
TIMEOUT="${TIMEOUT:-60}"
POLL_INTERVAL="${POLL_INTERVAL:-2}"

log() {
  echo "[blue-green] $*" >&2
}

usage() {
  sed -n '4,30p' "$0" | sed 's/^# \{0,1\}//' >&2
  exit 2
}

normalise_slot() {
  case "$1" in
    a|A|1|slot-a) echo "a" ;;
    b|B|2|slot-b) echo "b" ;;
    *)
      log "ERROR: invalid slot '$1' (expected a or b)"
      exit 2
      ;;
  esac
}

slot_server() {
  case "$1" in
    a) echo "$SLOT_A" ;;
    b) echo "$SLOT_B" ;;
  esac
}

slot_service() {
  case "$1" in
    a) echo "$SERVICE_A" ;;
    b) echo "$SERVICE_B" ;;
  esac
}

slot_health_url() {
  case "$1" in
    a) echo "$HEALTH_URL_A" ;;
    b) echo "$HEALTH_URL_B" ;;
  esac
}

other_slot() {
  case "$1" in
    a) echo "b" ;;
    b) echo "a" ;;
  esac
}

read_state() {
  # $1: key
  if [ -f "$ACTIVE_FILE" ]; then
    sed -n "s/^$1=//p" "$ACTIVE_FILE" | head -n 1
  fi
}

write_state() {
  # $1: active, $2: previous
  mkdir -p "$(dirname "$ACTIVE_FILE")"
  printf 'active=%s\nprevious=%s\n' "$1" "$2" > "$ACTIVE_FILE"
}

current_slot() {
  active="$(read_state active)"
  echo "${active:-a}"
}

read_upstream() {
  if [ -f "$NGINX_UPSTREAM" ]; then
    cat "$NGINX_UPSTREAM"
  else
    docker exec "$NGINX_CONTAINER" cat "$NGINX_UPSTREAM" 2>/dev/null || true
  fi
}

write_upstream() {
  # $1: raw file content
  if [ -f "$NGINX_UPSTREAM" ]; then
    printf '%s\n' "$1" > "$NGINX_UPSTREAM"
  else
    docker exec "$NGINX_CONTAINER" sh -c 'printf "%s\n" "$1" > "$2"' -- "$1" "$NGINX_UPSTREAM"
  fi
}

cmd_up() {
  slot="$(normalise_slot "$1")"
  service="$(slot_service "$slot")"
  if ! docker compose config --services 2>/dev/null | grep -qx "$service"; then
    log "service '$service' not defined in compose — falling back to 'backend'"
    service="backend"
  fi
  log "starting slot $slot (service: $service)"
  docker compose up -d "$service"
}

cmd_health() {
  slot="$(normalise_slot "$1")"
  base="$(slot_health_url "$slot")"
  deadline=$(( $(date +%s) + TIMEOUT ))
  log "health check for slot $slot at $base (timeout ${TIMEOUT}s)"
  while :; do
    health_ok=0
    ready_ok=0
    if curl -fsS --max-time 5 "$base/health" > /dev/null 2>&1; then
      health_ok=1
    fi
    if curl -fsS --max-time 5 "$base/ready" > /dev/null 2>&1; then
      ready_ok=1
    fi
    if [ "$health_ok" -eq 1 ] && [ "$ready_ok" -eq 1 ]; then
      log "slot $slot is healthy"
      return 0
    fi
    if [ "$(date +%s)" -ge "$deadline" ]; then
      log "ERROR: slot $slot not healthy within ${TIMEOUT}s (health=$health_ok ready=$ready_ok)"
      return 1
    fi
    sleep "$POLL_INTERVAL"
  done
}

cmd_switch() {
  slot="$(normalise_slot "$1")"
  current="$(current_slot)"
  server="$(slot_server "$slot")"
  previous_content="$(read_upstream)"

  log "switching active slot: $current -> $slot (upstream: $server)"
  write_upstream "$(printf 'upstream backend {\n    server %s;\n}' "$server")"

  if ! $NGINX_TEST_CMD > /dev/null 2>&1; then
    log "ERROR: nginx rejected the new upstream config"
    if [ -n "$previous_content" ]; then
      write_upstream "$previous_content"
      log "restored previous upstream config"
    fi
    exit 1
  fi

  if ! $NGINX_RELOAD_CMD > /dev/null 2>&1; then
    log "ERROR: nginx reload failed"
    if [ -n "$previous_content" ]; then
      write_upstream "$previous_content"
      log "restored previous upstream config"
    fi
    exit 1
  fi

  if [ "$slot" = "$current" ]; then
    write_state "$slot" "$(read_state previous)"
    log "slot $slot already active — upstream re-applied and nginx reloaded"
  else
    write_state "$slot" "$current"
    log "traffic now routed to slot $slot (previous: $current)"
  fi
}

cmd_rollback() {
  previous="$(read_state previous)"
  if [ -z "$previous" ]; then
    log "no previous slot recorded — nothing to roll back"
    return 0
  fi
  cmd_switch "$previous"
}

cmd_current() {
  slot="$(current_slot)"
  log "active slot: $slot"
  echo "$slot"
}

command="${1:-}"
[ $# -gt 0 ] || usage

case "$command" in
  up)
    [ $# -ge 2 ] || usage
    cmd_up "$2"
    ;;
  health)
    [ $# -ge 2 ] || usage
    cmd_health "$2"
    ;;
  switch)
    [ $# -ge 2 ] || usage
    cmd_switch "$2"
    ;;
  rollback)
    cmd_rollback
    ;;
  current)
    cmd_current
    ;;
  *)
    usage
    ;;
esac
