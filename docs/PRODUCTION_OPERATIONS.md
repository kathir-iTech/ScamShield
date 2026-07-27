# Production Operations Guide

## Deployment Guide

### Prerequisites

- Docker & Docker Compose (recommended)
- Python 3.12+ (for bare-metal deployment)
- Tesseract OCR engine (for image analysis)
- At least 1 GB RAM, 2 CPU cores

### Docker Deployment (Recommended)

```bash
# Build and start all services
docker compose up --build -d

# Check health
curl http://localhost:8000/health

# View logs
docker compose logs -f backend
```

### Bare-Metal Deployment

```bash
# Install system dependencies
apt-get install tesseract-ocr tesseract-ocr-eng

# Install Python dependencies
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env for your environment

# Start server
uvicorn main:app --host 0.0.0.0 --port 8000 --workers 2 --limit-concurrency 100
```

### Environment Profiles

| Profile | Debug | Auth | Log Format | Rate Limit | JWT TTL |
|---|---|---|---|---|---|
| `development` | on | off | text | 200/min | 1h |
| `testing` | off | off | text | 200/min | 1h |
| `staging` | off | on | json | 100/min | 30min |
| `production` | off | on | json | 60/min | 15min |
| `local` | on | off | text | 500/min | 24h |

Set via `SCAMSHIELD_ENVIRONMENT`.

---

## Monitoring Guide

### Health Endpoints

| Endpoint | Method | Purpose |
|---|---|---|
| `/health` | GET | Detailed health (dependencies, checks, uptime) |
| `/ready` | GET | Readiness probe (model loaded, config valid) |
| `/live` | GET | Liveness probe (simple alive check) |
| `/version` | GET | Service name, version, environment |
| `/metrics` | GET | Request metrics, system stats, latency percentiles |

### Health Response Format

```json
{
  "status": "pass",
  "service": "ScamShield",
  "version": "1.0.0",
  "environment": "production",
  "checks": [
    {"name": "ml_model", "status": "pass"},
    {"name": "jwt_secret", "status": "pass"}
  ],
  "dependencies": {
    "model": "loaded",
    "vectorizer": "loaded",
    "config": "valid"
  }
}
```

### Metrics Response Format

```json
{
  "total_requests": 1000,
  "successful_requests": 980,
  "failed_requests": 20,
  "active_requests": 5,
  "auth_failures": 3,
  "rate_limit_events": 10,
  "pipeline_failures": 2,
  "average_latency_ms": 145.2,
  "p50_latency_ms": 120.0,
  "p95_latency_ms": 350.0,
  "system": {
    "memory": {"total_gb": 8.0, "available_gb": 3.2, "percent_used": 60.0},
    "cpu": {"percent": 25.0},
    "process": {"memory_mb": 120.5, "threads": 8}
  }
}
```

### Prometheus Integration

The `/metrics` endpoint returns JSON. Use a Prometheus custom collector or
scrape and transform via a sidecar. Example prometheus.yml:

```yaml
scrape_configs:
  - job_name: 'scamshield'
    metrics_path: '/metrics'
    static_configs:
      - targets: ['backend:8000']
```

---

## Logging Guide

### Configuration

| Variable | Default | Production |
|---|---|---|
| `SCAMSHIELD_LOG_LEVEL` | INFO | INFO |
| `SCAMSHIELD_LOG_FORMAT` | text | json |
| `SCAMSHIELD_LOG_OUTPUT` | stdout | both |
| `SCAMSHIELD_LOG_FILE` | (empty) | /var/log/scamshield/app.log |

### JSON Log Format

```json
{
  "timestamp": "2026-07-26T12:00:00+00:00",
  "level": "INFO",
  "logger": "scamshield",
  "message": "Request completed",
  "request_id": "abc-123",
  "correlation_id": "abc-123",
  "duration_ms": 45.2,
  "status_code": 200,
  "method": "POST",
  "path": "/analyze/text",
  "user_id": "user_123"
}
```

### Logged Fields

- `request_id` — unique per request (UUID v4)
- `correlation_id` — from `X-Correlation-ID` header or same as request_id
- `duration_ms` — request processing time
- `status_code` — HTTP response status
- `method` — HTTP method
- `path` — request path
- `user_id` — authenticated user (empty for anonymous)
- `error_type` — exception class name (on errors)

### Never Logged

- Raw message text or OCR output
- Analysis results or predictions
- JWT tokens or API keys
- Passwords or secrets
- Full Credit card numbers (masked as `<CARD>`)
- Phone numbers (masked as `<PHONE>`)
- Email addresses (masked as `<EMAIL>`)

---

## Health Endpoints Reference

### /live — Liveness Probe

```json
{"status": "alive"}
```

Simple process-alive check. Use for container orchestration liveness probes.

### /ready — Readiness Probe

```json
{"status": "READY"}
```

Returns `NOT READY` with errors if:
- ML model is not loaded
- Configuration is invalid
- Required services are not initialised

### /health — Detailed Health

Returns comprehensive health with dependency checks, system metrics,
and configuration summary. Use for monitoring dashboards.

### /version — Service Info

```json
{
  "service": "ScamShield",
  "version": "1.0.0",
  "environment": "production"
}
```

---

## Docker Compose Reference

### Services

| Service | Image | Port | Health Check |
|---|---|---|---|
| backend | `scamshield-backend` | 8000 | `/health` every 30s |
| frontend | `scamshield-frontend` | 80 | HTTP check every 30s |

### Resource Limits

| Service | Memory | CPU |
|---|---|---|
| backend | 1 GB max | 1.0 max |
| frontend | 128 MB max | 0.25 max |

### Security

- `no-new-privileges: true` — prevents privilege escalation
- `cap_drop: ALL` — drops all Linux capabilities
- `cap_add: [NET_BIND_SERVICE]` — only allows binding to ports
- `read_only: true` — read-only root filesystem
- `tmpfs` mounts — writable temp directories
- `security_opt` — no new privileges

### Volumes

- `model-data` — persistent ML model storage (backend)
- `./backend/data:/app/data:ro` — read-only dataset mount

---

## Incident Response Checklist

### 1. Detection

- Check `/health` and `/ready` endpoints
- Review metrics for anomalies (latency spikes, error rate increase)
- Check logs for error patterns

### 2. Triage

- Is the ML model loaded? (Check `/ready`)
- Is there a configuration error? (Check startup logs)
- Are resources exhausted? (Check `/metrics` system stats)
- Is rate limiting being triggered? (Check `rate_limit_events`)

### 3. Common Incidents

| Symptom | Likely Cause | Action |
|---|---|---|
| 429 responses | Rate limit exceeded | Check client behaviour; adjust limit |
| 504 responses | Request timeout | Check downstream services; increase timeout |
| Model not loaded | Missing/corrupt model file | Check `models/` directory; retrain |
| High memory usage | Memory leak | Restart container; monitor trends |
| Auth failures | Invalid/missing JWT secret | Verify `SCAMSHIELD_JWT_SECRET` |

### 4. Recovery

- Restart individual service: `docker compose restart backend`
- Full restart: `docker compose down && docker compose up -d`
- Rollback: `docker compose up -d --build` with previous image tag

---

## Production Checklist

- [ ] `SCAMSHIELD_ENVIRONMENT=production`
- [ ] `SCAMSHIELD_AUTH_ENABLED=true`
- [ ] `SCAMSHIELD_JWT_SECRET` set to a strong random value
- [ ] `SCAMSHIELD_CORS_ORIGINS` set to specific origins
- [ ] `SCAMSHIELD_LOG_FORMAT=json`
- [ ] `SCAMSHIELD_LOG_OUTPUT=both`
- [ ] `SCAMSHIELD_LOG_FILE` set to writable path
- [ ] ML model and vectorizer files present in `models/`
- [ ] Nginx or reverse proxy in front with TLS termination
- [ ] Rate limiting configured at reverse proxy (30 req/s recommended)
- [ ] Docker resource limits configured (1 GB RAM, 1 CPU)
- [ ] Health checks configured in orchestrator
- [ ] Log aggregation set up (ELK, Datadog, etc.)
- [ ] Monitoring alerts configured (latency > 5s, error rate > 5%)
- [ ] Backup strategy for model files
- [ ] Secrets rotation procedure documented
- [ ] Dependencies scanned for CVEs
