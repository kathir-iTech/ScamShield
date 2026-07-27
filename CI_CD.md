# CI/CD Pipeline

## Overview

Four GitHub Actions workflows automate testing, security scanning, Docker builds, and releases:

| Workflow | Trigger | Purpose |
|---|---|---|
| `backend.yml` | Push/PR to `main` (backend paths) | Python lint, tests, security audit, Docker build check |
| `frontend.yml` | Push/PR to `main` (frontend paths) | TypeScript check, lint, tests, production build, security audit |
| `docker.yml` | Push/PR to `main` (Docker paths) | Build both images, validate compose, Trivy vulnerability scan |
| `release.yml` | Tag `v*` | Run all checks, build & push to GHCR, create GitHub Release |

## Quality Gates

### Backend
- **Import check**: All 21 Python modules must import without error
- **OpenAPI validation**: All 6 required routes must exist in the spec
- **Tests**: Pytest must pass (run via `quality_gate.py`)
- **Security**: `pip-audit --strict` scans dependencies
- **Docker**: Image must build successfully

### Frontend
- **TypeScript**: `tsc -b --noEmit` must pass
- **Lint**: `oxlint` must pass
- **Tests**: Vitest must pass
- **Build**: `npm run build` must succeed
- **Bundle size**: Total JS assets must be under 512 KB
- **Security**: `npm audit --audit-level=high`
- **Docker**: Image must build successfully

## Release Process

1. Update `VERSION` file and commit
2. Tag the release: `git tag v<VERSION> && git push origin v<VERSION>`
3. `release.yml` runs automatically:
   - Validates tag matches `VERSION` file
   - Runs all backend and frontend checks
   - Builds Docker images tagged with semver, major.minor, and commit SHA
   - Pushes images to `ghcr.io/<repo>/backend` and `ghcr.io/<repo>/frontend`
   - Creates a GitHub Release with deployment instructions

### Rollback

```bash
# Revert to previous version
docker compose down
docker compose -f docker-compose.yml pull backend:<prev-version> frontend:<prev-version>
# Update docker-compose.yml image tags, then:
docker compose up -d
```

## Local Verification

Before pushing, run the pre-commit verification script:

```bash
./scripts/verify.sh
```

This runs imports, backend tests, TypeScript check, lint, frontend tests, and production build.

## Security Scanning

| Tool | Scope | Frequency |
|---|---|---|
| `pip-audit` | Python dependencies | Every backend push/PR |
| `npm audit` | JavaScript dependencies | Every frontend push/PR |
| Trivy | Docker images (OS + language packages) | Docker-related changes |
| Gitleaks | Git history for secrets | Pre-commit (via `gitleaks detect`) |

## Artifacts

Workflows produce these artifacts (retained 7 days):
- `coverage/` — Frontend test coverage report
- `frontend-build/` — Production build output
- `trivy-reports/` — SARIF vulnerability reports
