# Operations Guide

## Monitoring Checklist

### Daily Checks

| Check | Command | Expected |
|---|---|---|
| All containers running | `docker compose ps` | `Up` status on all services |
| Health endpoint | `curl -s http://localhost:8000/health \| jq .` | `status: "healthy"` |
| Readiness | `curl -s http://localhost:8000/ready \| jq .` | `status: "READY"` |
| Liveness | `curl -s http://localhost:8000/live \| jq .` | `status: "alive"` |
| Metrics | `curl -s http://localhost:8000/metrics \| jq .` | No error fields |
| Disk usage | Check `disk_usage` field in health | Free space > 20% |
| Error rate | `curl -s http://localhost:8000/metrics` | `failed_requests` not growing |

### Weekly Checks

| Check | Action |
|---|---|
| Log review | `docker compose logs --tail=200 backend` |
| Error pattern analysis | `docker compose logs backend \| grep -i error \| tail -50` |
| Performance trends | Compare `average_latency_ms` and `p95_latency_ms` over time |
| Model file integrity | Verify `models/model.joblib` and `models/vectorizer.joblib` exist |

### Monthly Checks

| Check | Action |
|---|---|
| Certificate expiry | Check TLS certs if using HTTPS |
| Dependency updates | Review `pip-audit` and `npm audit` output |
| Backup restore test | Verify backup restoration process |
| Log rotation | Verify log files are rotating correctly |

## Incident Response

### Severity Levels

| Level | Definition | Response Time |
|---|---|---|
| CRITICAL | Service down or data loss | Immediate |
| HIGH | Degraded performance | < 15 minutes |
| MEDIUM | Non-critical feature broken | < 1 hour |
| LOW | Cosmetic issue | < 24 hours |

### Incident Response Checklist

1. **Detect**
   - Monitoring alert or user report received
   - Note the time, symptoms, and affected users

2. **Triage**
   - Check `/live` endpoint — is the process alive?
   - Check `/health` endpoint — what's the status?
   - Check `/ready` endpoint — is the service ready?
   - Check `docker compose ps` — are all containers running?

3. **Diagnose**
   - `./scripts/diagnostics.sh` — collect system diagnostics
   - `docker compose logs --tail=200 backend` — recent backend logs
   - `docker compose logs --tail=100 frontend` — recent frontend logs
   - Check disk and memory via health endpoint

4. **Mitigate**
   - Restart single service: `docker compose restart backend`
   - Full restart: `./scripts/restart.sh`
   - Rollback: `./scripts/rollback.sh <previous-version>`

5. **Resolve**
   - Apply fix and verify via health endpoint
   - Monitor for 5 minutes after resolution
   - Update incident log

6. **Post-Mortem**
   - Document root cause and resolution steps
   - Update runbooks
   - Schedule follow-up if needed

### Common Incidents

| Symptom | Likely Cause | Action |
|---|---|---|
| Health check fails | Model files missing | Restore from backup, retrain model |
| Readiness shows NOT READY | Configuration error | Check env vars, check logs |
| Frontend returns 502 | Backend unreachable | `docker compose restart backend` |
| Slow responses | Resource exhaustion | Check metrics, increase resources |
| OCR failures | Tesseract unavailable | Verify Tesseract installation |
| High error rate | Invalid input patterns | Check logs for error types |

## Backup Verification

```bash
# Backup model and data
tar -czf backup-$(date +%Y%m%d).tar.gz backend/models/ backend/data/

# Verify backup integrity
tar -tzf backup-$(date +%Y%m%d).tar.gz > /dev/null && echo "Backup OK"

# Restore from backup
tar -xzf backup-YYYYMMDD.tar.gz
docker compose restart backend
```

## Health Verification

```bash
# Quick health check
./scripts/health.sh

# Full diagnostics
./scripts/diagnostics.sh

# Version info
./scripts/version.sh

# Verify all endpoints
curl -s http://localhost:8000/health | jq .
curl -s http://localhost:8000/ready | jq .
curl -s http://localhost:8000/live | jq .
curl -s http://localhost:8000/metrics | jq .
```

## Upgrade Checklist

1. Pull latest images
2. Backup current data and models
3. Deploy new version: `docker compose up -d`
4. Wait for health checks to pass
5. Verify `/health` returns new `build_version`
6. Run a test analysis
7. Check frontend loads correctly
8. Monitor for 5 minutes post-upgrade

## Rollback Checklist

1. Identify previous stable version tag
2. `docker compose down`
3. Update image tags in `docker-compose.yml` to previous version
4. `docker compose up -d`
5. Verify health checks pass
6. Verify frontend loads correctly
7. Log the rollback reason and trigger
