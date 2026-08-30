# ScamShield — Deployment Guide

## System Requirements

### Minimum
- **OS**: Linux x86_64 (Ubuntu 22.04+, Debian 12+, RHEL 9+)
- **CPU**: 2 cores
- **RAM**: 2 GB
- **Disk**: 10 GB free
- **Docker**: 24.0+ and Docker Compose v2

### Recommended
- **CPU**: 4 cores
- **RAM**: 4 GB
- **Disk**: 20 GB SSD

### Software
- Docker Engine 24.0+
- Docker Compose v2 (plugin)
- curl (for health checks)

---

## Quick Start

```bash
# 1. Clone the repository
git clone <repository-url> scamshield
cd scamshield

# 2. Configure environment
cp .env.example .env
# Edit .env if needed (defaults work for most deployments)

# 3. Start the application
./scripts/start.sh

# 4. Verify health
./scripts/health.sh
```

The application will be available at:

| Service     | URL                       |
|-------------|---------------------------|
| Frontend    | http://localhost:80       |
| API         | http://localhost:80/api   |
| Swagger Docs| http://localhost:80/docs  |
| ReDoc       | http://localhost:80/redoc |
| Health      | http://localhost:80/health|

---

## Docker Compose Deployment

### Architecture

```
                   :80
User ─────────────────────────────────► Frontend (Nginx)
                                          │
                                          │ ProxyPass /api /docs /openapi.json
                                          ▼
                                   Backend (FastAPI + Uvicorn)
                                          │
                                    ┌─────┴─────┐
                                    │           │
                                  Models     Dataset
                                 (volume)   (read-only)
```

### Services

| Service  | Image                  | Port  | Base Image        |
|----------|------------------------|-------|-------------------|
| backend  | `scamshield-backend`   | 8000  | python:3.12-slim  |
| frontend | `scamshield-frontend`  | 80    | nginx:1.27-alpine |

### Volumes

| Name          | Mount            | Purpose              |
|---------------|------------------|----------------------|
| `model-data`  | `/app/models`    | ML model persistence |

### Data Directory

The backend `data/` directory (containing `scam_dataset.csv`) is mounted read-only at `/app/data`.

---

## Environment Variables

See `.env.example` for the complete list.

| Variable                     | Default  | Description                              |
|------------------------------|----------|------------------------------------------|
| `SCAMSHIELD_MAX_TEXT_LENGTH` | `10000`  | Maximum text length for analysis         |
| `SCAMSHIELD_MAX_FILE_SIZE_MB`| `10`     | Maximum image upload size in MB          |
| `VITE_API_BASE_URL`          | `/api`   | Frontend API base URL (build-time arg)   |

---

## Manual Deployment (without Docker)

### Backend

```bash
cd backend

# Create virtual environment
python -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Run with uvicorn
uvicorn main:app --host 0.0.0.0 --port 8000 --workers 4
```

### Frontend

```bash
cd frontend

# Install dependencies
npm ci

# Build for production
npm run build

# Serve with any static server
# Example with python:
cd dist
python -m http.server 3000
```

### Nginx

An Nginx configuration is provided at `frontend/nginx.conf`. To use it directly:

```bash
# Copy config
cp frontend/nginx.conf /etc/nginx/sites-available/scamshield
ln -s /etc/nginx/sites-available/scamshield /etc/nginx/sites-enabled/

# Edit the upstream backend line in the config if needed:
# Change: server backend:8000;
# To: server localhost:8000;

# Test and reload
nginx -t
systemctl reload nginx
```

---

## Backup Strategy

### What to back up
- **ML Model**: `/app/models/model.joblib` (Docker volume `model-data`)
- **Vectorizer**: `/app/models/vectorizer.joblib` (Docker volume `model-data`)
- **Dataset**: `/app/data/scam_dataset.csv` (persistent on host)
- **Environment**: `.env` file

### Backup commands

```bash
# Backup model volume
docker run --rm -v model-data:/source -v $(pwd)/backup:/dest alpine \
  cp -r /source/. /dest/

# Backup everything
tar -czf scamshield-backup-$(date +%Y%m%d).tar.gz \
  .env \
  backend/data/ \
  backend/models/
```

---

## Upgrade Process

```bash
# 1. Pull latest code
git pull

# 2. Rebuild and restart
./scripts/restart.sh

# 3. Verify
./scripts/health.sh
```

For zero-downtime upgrades (future enhancement):
- Deploy a second instance behind a load balancer
- Use rolling updates with Docker Swarm or similar

---

## Rollback Process

```bash
# 1. Revert code
git log --oneline -5
git checkout <previous-commit-hash>

# 2. Rebuild and restart
./scripts/restart.sh

# 3. Verify
./scripts/health.sh
```

To restore from a backup:

```bash
# 1. Restore model volume
docker run --rm -v $(pwd)/backup:/source -v model-data:/dest alpine \
  cp -r /source/. /dest/

# 2. Rebuild and restart
./scripts/restart.sh
```

---

## Troubleshooting

### Backend won't start

```
docker compose logs backend
```

Common causes:
- **Model files missing**: Place `model.joblib` and `vectorizer.joblib` in `backend/models/`
- **Port conflict**: Change host port in `docker-compose.yml`
- **Permission denied**: Ensure `models/` and `data/` are readable

### Frontend shows blank page

- Check the browser console for errors
- Verify `VITE_API_BASE_URL` matches the API path
- Run `./scripts/health.sh` to verify backend reachability

### API returns 502 Bad Gateway

- Nginx cannot reach the backend container
- Verify backend container is running: `docker compose ps`
- Check backend logs: `./scripts/logs.sh backend`

### React routing doesn't work after refresh

This is handled by the Nginx SPA fallback in `nginx.conf`:
```nginx
location / {
    try_files $uri $uri/ /index.html;
}
```

If deep links still fail, ensure the Nginx config is loaded correctly.

### File upload fails

- Check `client_max_body_size` in `nginx.conf` (default: 12m)
- Check `SCAMSHIELD_MAX_FILE_SIZE_MB` in `.env`
- Verify file type is in `image/jpeg, image/png, image/webp, image/bmp`

---

## Management Commands

```bash
# Start
./scripts/start.sh

# Stop
./scripts/stop.sh

# Restart
./scripts/restart.sh

# View logs (follow)
./scripts/logs.sh backend
./scripts/logs.sh frontend

# Health check
./scripts/health.sh
```

---

## Ports Reference

| Port | Service      | Protocol | Purpose                  |
|------|--------------|----------|--------------------------|
| 80   | Frontend     | HTTP     | Application UI + API     |
| 8000 | Backend      | HTTP     | Direct backend access    |

In production, place the application behind a reverse proxy on port 443 with TLS termination (e.g., using Let's Encrypt with Certbot or Caddy).

---

## Security Notes

- Both containers run as non-root users
- Filesystems are read-only (except tmpfs mounts for runtime data)
- All Linux capabilities are dropped except `NET_BIND_SERVICE`
- `no-new-privileges` security option is enabled
- Resource limits prevent CPU/memory exhaustion
- Container logs are limited to 3 × 10MB rotated files
- Backend startup validates prerequisites and logs warnings on failure
- CORS is wide open (`*`) for maximum compatibility — restrict in production
