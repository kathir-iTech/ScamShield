# Production Operations Guide

## Deployment Guide

### Prerequisites

- Docker & Docker Compose (recommended)
- Python 3.12+ (for bare-metal deployment)
- Tesseract OCR engine (for image analysis)
- At least 1 GB RAM, 2 CPU cores

### Docker Deployment (Recommended)

```bash
# Validate the compose file first
docker compose config -q

# Build and start all services (backend, frontend, nginx, redis, prometheus, grafana)
docker compose up --build -d

# Check health through the edge proxy
curl http://localhost/health
curl http://localhost:8000/health

# View logs
docker compose logs -f backend
```

`.env` is optional: compose starts without it (`env_file` is `required: false`).
Copy `.env.example` to `.env` to override defaults.

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

`/metrics` serves Prometheus text exposition format. The root compose stack runs
Prometheus (`127.0.0.1:9090`) and Grafana (`127.0.0.1:3000`) with the scrape
config in `backend/monitoring/prometheus/prometheus.yml`:

```yaml
scrape_configs:
  - job_name: 'scamshield'
    metrics_path: '/metrics'
    static_configs:
      - targets: ['backend:8000']
  - job_name: 'prometheus'
    static_configs:
      - targets: ['localhost:9090']
  - job_name: 'grafana'
    static_configs:
      - targets: ['grafana:3000']
```

Alert rules live in `backend/monitoring/prometheus/alert-rules.yml`
(see the Alert Runbook below). Grafana is provisioned automatically:

- Datasource: `backend/monitoring/grafana/provisioning/datasources/prometheus.yml`
  (uid `prometheus`, default, non-editable)
- Dashboard provider: `backend/monitoring/grafana/provisioning/dashboards/dashboards.yml`
  (folder `ScamShield`, refresh 30s)
- Dashboard JSON: `backend/monitoring/grafana/dashboard.json`

The same files back the standalone stack in
`backend/monitoring/docker-compose.monitoring.yml` (superseded by the root
compose file; kept for standalone use on the `scamshield` network).

---

## Logging Guide

### Log locations

| Source | Location |
|---|---|
| Backend/frontend/nginx/redis/prometheus/grafana containers | `docker compose logs <service>` (json-file driver, 10 MB x 3 rotated) |
| Application log file (if `SCAMSHIELD_LOG_FILE` set) | e.g. `/var/log/scamshield/app.log` |
| Prediction audit log | container path `/app/logs/predictions` (best-effort under `read_only`) |
| Rollback events | `logs/rollback.log` |
| Active blue-green slot state | `logs/active-slot` |

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

| Service | Image | Published Port | Health Check |
|---|---|---|---|
| backend | `wary-backend:latest` | `8000:8000` | `/health` (python urllib) every 30s |
| frontend | `wary-frontend:latest` | expose `80` only | HTTP check every 30s |
| nginx | `nginx:1.27-alpine` | `80:80`, `443:443` | HTTP check on `/` every 30s |
| redis | `redis:7-alpine` | none (internal) | `redis-cli ping` every 10s |
| prometheus | `prom/prometheus:v2.53.0` | `127.0.0.1:9090` | `/-/healthy` every 30s |
| grafana | `grafana/grafana:11.0.0` | `127.0.0.1:3000` | `/api/health` every 30s |

All services attach to the named network `scamshield`.
`frontend` no longer publishes port 80 — the edge `nginx` container is the
single entry point.

Image tags are overridable for blue-green/registry deploys:
`BACKEND_IMAGE` (default `wary-backend:latest`), `FRONTEND_IMAGE`
(default `wary-frontend:latest`).

### Resource Limits

| Service | Memory | CPU |
|---|---|---|
| backend | 1 GB max | 1.0 max |
| frontend | 128 MB max | 0.25 max |
| nginx | 128 MB max | 0.25 max |
| redis | 128 MB max | 0.25 max |
| prometheus | 512 MB max | 0.5 max |
| grafana | 256 MB max | 0.3 max |

### Security

- `no-new-privileges: true` — prevents privilege escalation
- `cap_drop: ALL` — drops all Linux capabilities
- `cap_add: [NET_BIND_SERVICE]` — only allows binding to ports (backend, frontend, nginx)
- `read_only: true` — read-only root filesystem
- `tmpfs` mounts — writable temp directories
- `security_opt` — no new privileges
- JSON logging driver — 10 MB x 3 files rotation per container

### Volumes

- `model-data` — persistent ML model storage (backend `/app/models`)
- `analysis-data` — writable dataset/DB mount (backend `/app/data`; seeded from
  the image, replaces the previous read-only `./backend/data` bind so the SQLite
  DB and prediction logs are writable)
- `redis-data` — Redis persistence (`/data`, RDB save every 60s)
- `prometheus_data` — Prometheus TSDB
- `grafana_data` — Grafana state (users, dashboards cache)

### Configuration

- `backend` reads `SCAMSHIELD_REDIS_URL` (default `redis://redis:6379/0`),
  `SCAMSHIELD_CACHE_TTL` (default `300`), `SCAMSHIELD_CACHE_MAXSIZE` (default `1024`).
- Grafana admin credentials: `GRAFANA_ADMIN_USER` / `GRAFANA_ADMIN_PASSWORD`
  (defaults `admin`/`admin` — override in production).

---

## Edge Proxy (nginx)

`wary-nginx` is the only published entry point (ports 80 and 443).

### Routes

| Path | Target | Notes |
|---|---|---|
| `/` and static assets | frontend | nested asset locations add `expires` caching |
| `/api/*` | backend | prefix stripped (`/api/analyze/text` → `/analyze/text`), rate limited |
| `/docs`, `/openapi.json` | backend | Swagger UI |
| `/health`, `/ready`, `/live` | backend | exact match, not rate limited, access log off |
| `/metrics` | frontend | intentionally not exposed at the edge |

Shared server blocks live in `nginx/routes.conf` (mounted at
`/etc/nginx/routes.conf`); `nginx/default.conf` holds the rate-limit zones, the
slot include and the port-80 server.

### Rate limiting and headers

- Zones: `api` 30 r/s (burst 20, nodelay), `static` 100 r/s
- Throttled responses return **429** (`limit_req_status 429`)
- `client_max_body_size 20m` (image uploads up to 10 MB)
- Forwards `Host`, `X-Real-IP`, `X-Forwarded-For`, `X-Forwarded-Proto`,
  `X-Request-ID` (edge-generated)
- Security headers + CSP on every response

### TLS

Out of the box the edge serves HTTP only — no certificate material ships in the
repository. Port 443 is published and becomes active once you add TLS:

1. Put your certificate material in `nginx/certs/` (mounted read-only at
   `/etc/nginx/certs`). Files matching `nginx/certs/*.conf` are included at the
   http level, so add a `nginx/certs/tls.conf`:

```nginx
server {
    listen 443 ssl;
    http2 on;
    server_name example.com;

    ssl_certificate     /etc/nginx/certs/cert.pem;
    ssl_certificate_key /etc/nginx/certs/key.pem;
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers HIGH:!aNULL:!MD5;
    ssl_prefer_server_ciphers on;
    ssl_session_cache shared:SSL:10m;
    ssl_session_timeout 10m;

    add_header Strict-Transport-Security "max-age=63072000; includeSubDomains; preload" always;

    include /etc/nginx/routes.conf;
}
```

2. Validate and reload:

```bash
docker compose exec wary-nginx nginx -t
docker compose exec wary-nginx nginx -s reload
```

An empty `nginx/certs/` directory is valid: the wildcard include matches
nothing and the stack runs HTTP-only.

---

## Caching

`services.orchestrator` configures the analysis cache at import from the
environment:

| Variable | Default | Meaning |
|---|---|---|
| `SCAMSHIELD_CACHE_TTL` | 300 | Entry lifetime in seconds |
| `SCAMSHIELD_CACHE_MAXSIZE` | 1024 | Max entries (LRU eviction beyond this) |
| `SCAMSHIELD_REDIS_URL` | (empty) | Redis URL; empty falls back to in-process memory |

- With no Redis URL the cache is an in-process bounded LRU/TTL cache
  (`core/cache.py`, thread-safe).
- With a Redis URL entries are JSON-serialised in Redis with a
  `scamshield:cache:` prefix. Every Redis error fails open: reads count as
  misses, writes are dropped — analysis is never blocked by cache trouble.
- The async path `analyze_text_async(text)` checks the cache, runs
  `analyze_text` in a worker thread on a miss, and stores the result.
- Cache statistics (hits, misses, evictions, size, maxsize) are exposed under
  `observability.cache` in the diagnostics payload.

---

## Blue-Green Deployment

Two backend slots are switched at the nginx edge by `scripts/blue-green.sh`.
The active upstream lives in `nginx/slots/active.conf` (mounted into the nginx
container); the script rewrites it, validates with `nginx -t`, reloads nginx,
and records state in `logs/active-slot` (`active=` / `previous=` lines).

```bash
bash scripts/blue-green.sh up a          # start slot a service
bash scripts/blue-green.sh health a      # poll /health and /ready until healthy
bash scripts/blue-green.sh switch b      # route traffic to slot b (validated reload)
bash scripts/blue-green.sh current       # print active slot
bash scripts/blue-green.sh rollback      # switch back to the recorded previous slot
```

Defaults: slot a → `backend:8000`, slot b → `backend-b:8000`, health base URL
`http://localhost:8000` (override per slot with `HEALTH_URL_A` / `HEALTH_URL_B`).
If compose does not define `backend-a`/`backend-b` (plain dev stack), `up`
falls back to the `backend` service, so the script is safe to run locally.

### CI/CD workflow (`.github/workflows/deploy.yml`)

- **build** — on pushes to `main` touching backend/frontend/nginx/compose paths
  (and manual runs), builds and pushes images to GHCR.
- **deploy** — gated on the repository variable `ENABLE_BLUE_GREEN_DEPLOY=true`;
  starts the idle slot, runs the pre-switch health gate, switches traffic,
  re-checks health, and auto-rolls back on failure.
- **verify** — re-checks the active slot and the public `DEPLOY_URL`.
- **rollback** — manual `workflow_dispatch` with `action=rollback`; switches to
  the opposite of `vars.ACTIVE_SLOT`.

Repository variables: `ENABLE_BLUE_GREEN_DEPLOY`, `ACTIVE_SLOT` (`a`/`b`),
`DEPLOY_URL`, `HEALTH_URL_A`, `HEALTH_URL_B`.

For a two-slot host, add a deploy-only override file (validated with
`docker compose -f docker-compose.yml -f docker-compose.bluegreen.yml config -q`).
Slot a stays the plain `backend` service (matching the script default
`SLOT_A=backend:8000`); slot b is a second instance without a host port:

```yaml
# docker-compose.bluegreen.yml
services:
  backend-b:
    extends:
      file: docker-compose.yml
      service: backend
    container_name: wary-backend-b
    ports: !override []
```

---

## Alert Runbook (Prometheus)

Rules: `backend/monitoring/prometheus/alert-rules.yml` (11 alerts, evaluated
every 30s).

| Alert | Severity | Fires when | First action |
|---|---|---|---|
| HighErrorRate | critical | 5xx ratio > 5% for 5m | Check backend logs; roll back if a deploy introduced it |
| HighLatency | warning | P95 latency > 2s for 5m | Check load, ML/OCR stages; scale backend |
| HighMemoryUsage | warning | Process RSS > 0.8 GiB for 5m | Restart backend; investigate leak trends |
| HighCPUUsage | warning | Process CPU > 80% for 5m | Check traffic spikes; add capacity |
| RateLimitSpike | warning | Rate-limit events > 100/min for 5m | Identify abusive client; verify limits |
| HighRateLimit429 | warning | HTTP 429 responses > 100/min for 5m | Same as above; edge limits return 429 |
| AuthFailureSpike | critical | Auth failures > 10/min for 5m | Check JWT secret rotation; possible brute force |
| ModelNotLoaded | critical | Model status not loaded for 1m | Check `models/` volume; restart backend |
| PipelineFailureSpike | warning | Pipeline failures > 10/min for 5m | Check step telemetry in logs |
| OcrBottleneck | warning | OCR P95 > 5s for 5m | Check image sizes; OCR queue depth |
| InstanceDown | critical | `up{job="scamshield"}` absent for 1m | Restart container; check orchestrator health |

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
- Blue-green switch/rollback: `bash scripts/blue-green.sh switch <slot>` /
  `bash scripts/blue-green.sh rollback`
- Version rollback: `./scripts/rollback.sh <version>`

---

## Production Checklist

- [ ] `SCAMSHIELD_ENVIRONMENT=production`
- [ ] `SCAMSHIELD_AUTH_ENABLED=true`
- [ ] `SCAMSHIELD_JWT_SECRET` set to a strong random value
- [ ] `SCAMSHIELD_CORS_ORIGINS` set to specific origins
- [ ] `SCAMSHIELD_LOG_FORMAT=json`
- [ ] `SCAMSHIELD_LOG_OUTPUT=both`
- [ ] `SCAMSHIELD_LOG_FILE` set to writable path
- [ ] `SCAMSHIELD_CACHE_TTL` / `SCAMSHIELD_CACHE_MAXSIZE` sized for traffic
- [ ] `SCAMSHIELD_REDIS_URL` points at managed Redis for shared cache/rate limits
- [ ] ML model and vectorizer files present in `models/`
- [ ] Edge nginx in front (shipped) with TLS certificates in `nginx/certs/`
- [ ] Rate limiting configured at edge (shipped: 30 r/s api, 100 r/s static, 429)
- [ ] Docker resource limits configured (all six services limited)
- [ ] Health checks configured in orchestrator
- [ ] Log aggregation set up (ELK, Datadog, etc.)
- [ ] Prometheus/Grafana reachable; alert rules reviewed (Alert Runbook above)
- [ ] `ENABLE_BLUE_GREEN_DEPLOY` repository variable set to run deploy workflow
- [ ] Backup strategy for model files
- [ ] Secrets rotation procedure documented
- [ ] Dependencies scanned for CVEs
