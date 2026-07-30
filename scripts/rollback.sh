#!/usr/bin/env bash
set -euo pipefail

# ScamShield Rollback Script
# Usage: ./scripts/rollback.sh [version]
#   version: Docker image tag to roll back to (default: previous tag)

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"
LOG_FILE="$PROJECT_DIR/logs/rollback.log"

mkdir -p "$PROJECT_DIR/logs"

log() {
  echo "[$(date +%Y-%m-%d_%H:%M:%S)] $*" | tee -a "$LOG_FILE"
}

# Determine version
VERSION="${1:-previous}"
BACKEND_IMAGE="scamshield-backend:${VERSION}"
FRONTEND_IMAGE="scamshield-frontend:${VERSION}"

log "=== Rollback initiated ==="
log "Target version: ${VERSION}"

cd "$PROJECT_DIR"

# 1. Pull previous Docker image
log "Pulling backend image: ${BACKEND_IMAGE}"
docker pull "$BACKEND_IMAGE" 2>&1 | tee -a "$LOG_FILE"

log "Pulling frontend image: ${FRONTEND_IMAGE}"
docker pull "$FRONTEND_IMAGE" 2>&1 | tee -a "$LOG_FILE"

# 2. Restore previous model data from backup
BACKUP_DIR="$PROJECT_DIR/backups"
if [ -d "$BACKUP_DIR" ]; then
  LATEST_MODEL_BACKUP=$(ls -t "$BACKUP_DIR"/model-data-*.tar.gz 2>/dev/null | head -1)
  if [ -n "$LATEST_MODEL_BACKUP" ]; then
    log "Restoring model data from: $LATEST_MODEL_BACKUP"
    docker run --rm -v scamshield_model-data:/data -v "$BACKUP_DIR":/backup alpine \
      tar xzf "/backup/$(basename "$LATEST_MODEL_BACKUP")" -C /data 2>&1 | tee -a "$LOG_FILE"
    log "Model data restored"
  else
    log "WARNING: No model backup found at $BACKUP_DIR"
  fi
else
  log "WARNING: Backup directory $BACKUP_DIR does not exist"
fi

# 3. Roll back docker-compose services
log "Updating docker-compose to use ${VERSION} tag"
export SCAMSHIELD_BACKEND_TAG="${VERSION}"
export SCAMSHIELD_FRONTEND_TAG="${VERSION}"

log "Stopping services"
docker compose down 2>&1 | tee -a "$LOG_FILE"

log "Starting services with rolled-back images"
docker compose up -d 2>&1 | tee -a "$LOG_FILE"

# 4. Wait for health check
log "Waiting for backend health check..."
for i in $(seq 1 30); do
  if curl -sf http://localhost:8000/health > /dev/null 2>&1; then
    log "Backend is healthy"
    break
  fi
  if [ "$i" -eq 30 ]; then
    log "FAIL: Backend did not become healthy within timeout"
    exit 1
  fi
  sleep 2
done

log "Waiting for frontend health check..."
for i in $(seq 1 15); do
  if curl -sf http://localhost:80/ > /dev/null 2>&1; then
    log "Frontend is healthy"
    break
  fi
  if [ "$i" -eq 15 ]; then
    log "WARNING: Frontend did not become healthy within timeout"
  fi
  sleep 2
done

# 5. Verify rollback succeeded
log "Running verification..."
VERIFY_RESULT=0
"$SCRIPT_DIR/verify.sh" 2>&1 | tee -a "$LOG_FILE" || VERIFY_RESULT=$?

if [ "$VERIFY_RESULT" -eq 0 ]; then
  log "Rollback verification PASSED"
else
  log "FAIL: Rollback verification failed (exit code: $VERIFY_RESULT)"
  exit 1
fi

# 6. Log the rollback event
log "Rollback to version ${VERSION} completed successfully"
log "=== Rollback complete ==="

echo ""
echo "Rollback to ${VERSION} completed successfully."
echo "Review logs at: $LOG_FILE"
