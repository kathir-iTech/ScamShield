# Backup & Disaster Recovery

## Overview

This document describes the backup strategy for ScamShield, covering models, datasets, configuration, and Docker volumes.

## Assets to Backup

| Asset | Location | Frequency | RTO | RPO |
|---|---|---|---|---|
| ML Models | `backend/models/`, Docker volume `model-data` | Daily | 1h | 24h |
| Datasets | `datasets/`, `backend/data/` | Weekly | 2h | 7d |
| Configuration | `.env`, `docker-compose.yml`, `k8s/*.yaml` | Per change | 30m | N/A |
| Docker Volumes | `model-data` | Daily | 1h | 24h |

## Backup Procedures

### ML Models

```bash
# Manual backup
docker run --rm -v model-data:/source -v $(pwd)/backups:/dest alpine \
  tar czf /dest/models-$(date +%Y%m%d-%H%M%S).tar.gz -C /source .

# Automated via cron (add to crontab)
# 0 2 * * * /opt/scamshield/scripts/backup-models.sh
```

### Datasets

```bash
# Backup raw and annotated datasets
tar czf backups/datasets-$(date +%Y%m%d).tar.gz \
  datasets/ \
  backend/data/
```

### Docker Volumes

```bash
# Backup model-data volume
docker run --rm -v model-data:/data -v $(pwd)/backups:/backup alpine \
  tar czf /backup/model-data-$(date +%Y%m%d-%H%M%S).tar.gz -C /data .

# List volumes
docker volume ls --filter name=scamshield
```

### Configuration

```bash
# Backup all config files
tar czf backups/config-$(date +%Y%m%d).tar.gz \
  .env \
  docker-compose.yml \
  k8s/ \
  .github/
```

## Restore Procedures

### Restore Models

```bash
# Stop services
docker compose down backend

# Restore volume
docker run --rm -v model-data:/data -v $(pwd)/backups:/backup alpine \
  tar xzf /backup/models-20260101-020000.tar.gz -C /data

# Restart
docker compose up -d backend
```

### Restore Datasets

```bash
tar xzf backups/datasets-20260101.tar.gz
cp backend/data/dataset_*.csv backend/data/
```

### Full Restore from Scratch

```bash
# 1. Restore config
tar xzf backups/config-20260101.tar.gz

# 2. Restore volumes
docker run --rm -v model-data:/data -v $(pwd)/backups:/backup alpine \
  tar xzf /backup/model-data-20260101-020000.tar.gz -C /data

# 3. Start services
docker compose up -d

# 4. Verify health
./scripts/health.sh
```

## Scheduled Backup Recommendations

Add to root crontab (`sudo crontab -e`):

```cron
# Daily model backup at 2 AM
0 2 * * * /opt/scamshield/scripts/backup-models.sh

# Weekly dataset backup on Sunday at 3 AM
0 3 * * 0 /opt/scamshield/scripts/backup-datasets.sh

# Monthly full backup on 1st at 4 AM
0 4 1 * * /opt/scamshield/scripts/backup-full.sh
```

## Retention Policy

- **Daily backups:** Keep 7 days
- **Weekly backups:** Keep 4 weeks
- **Monthly backups:** Keep 12 months
- **Pre-upgrade snapshots:** Keep until next major version

## RTO / RPO Guidelines

| Tier | Metric | Target |
|---|---|---|
| Hot (Config) | RTO | 15 min |
| | RPO | Real-time (Git) |
| Warm (Models) | RTO | 1 h |
| | RPO | 24 h |
| Cold (Datasets) | RTO | 2 h |
| | RPO | 7 d |

## Disaster Recovery Procedure

### Recovery Steps

1. **Assess** — Determine scope of failure (single service, host, or region)
2. **Provision** — Spin up replacement infrastructure
3. **Restore config** — Apply latest configuration from backup or Git
4. **Restore volumes** — Restore Docker volumes from latest backup
5. **Verify models** — Run `python -c "from predict import ModelManager; ModelManager().load()"`
6. **Start services** — `docker compose up -d`
7. **Health check** — Run `./scripts/health.sh` and verify all endpoints respond
8. **Smoke test** — Submit a test SMS/email for classification

### Failure Scenarios

| Scenario | Response |
|---|---|
| Container crash | `docker compose restart backend` |
| Corrupt model file | Restore model from latest backup |
| Full host failure | Deploy to new host, restore from backup |
| Data corruption | Restore dataset + retrain model |

### Post-Recovery

1. Run full test suite: `python -m pytest backend/tests/`
2. Run benchmark: `python -m pytest backend/tests/benchmark/`
3. Validate gold evaluation set
4. Notify stakeholders
