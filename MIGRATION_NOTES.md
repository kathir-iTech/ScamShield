# Migration Notes — ScamShield v1.0.0

## Upgrading from v0.x (Pre-Release)

### Breaking Changes

1. **API Endpoint Structure**
   - Old: `/analyze` → New: `/api/v1/analyze/text`
   - Old: `/analyze-image` → New: `/api/v1/analyze/image`
   - Old: `/health` → New: `/api/v1/health` (legacy still works)

2. **Response Format**
   - `prediction` field now returns `"scam"` or `"safe"` (was `"scam"` or `"legitimate"`)
   - New required field: `reasoning_family` and `reasoning_subfamily`
   - `confidence_breakdown` now includes per-stage contributions

3. **Configuration**
   - Renamed env vars:
     - `MODEL_FILE` → `MODEL_PATH`
     - `TESSERACT_BIN` → `TESSERACT_CMD`
   - New required env vars: `CORS_ORIGINS`, `CONNECTOR_CACHE_TTL`

4. **Docker Compose**
   - `docker-compose.yml` restructured with health checks
   - Frontend now uses Nginx (was direct Vite dev server)
   - Backend uses Gunicorn + Uvicorn workers

### Migration Steps

```bash
# 1. Backup your .env
cp .env .env.backup

# 2. Update .env with new variables
cp .env.example .env

# 3. Rebuild containers
docker compose down
docker compose build --no-cache
docker compose up -d

# 4. Verify migration
curl http://localhost:8000/api/v1/health
```

### Rollback

```bash
git checkout v0.9.0
docker compose down
docker compose up -d
```
