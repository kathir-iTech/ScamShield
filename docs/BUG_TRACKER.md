# Bug Tracker — ScamShield RC2

> Generated: 2026-07-31
> Branch: main (commit b789ef9)
> Status: Active

---

## Legend

| Severity | Meaning |
|----------|---------|
| Critical | Blocks release, production-breaking |
| High | Severe issue, must fix before release |
| Medium | Important issue, fix if time permits |
| Low | Cosmetic, fix on backlog |

| Status | Meaning |
|--------|---------|
| Open | Not yet addressed |
| In Progress | Being worked on |
| Verified | Fix applied and tested |
| Wont Fix | Deferred / not applicable |
| Won't Reproduce | False positive investigation |

---

## Open Bugs

### BUG-001: Pre-existing Safe Text Decision Score Too High
- **Severity:** Medium
- **Component:** Backend — Pipeline confidence engine
- **Steps:**
  1. Run integration test `test_pipeline_safe_detection`
  2. Observe safe text gets decision score of 15 (should be low)
- **Expected:** Safe text gets LOW decision score
- **Actual:** Safe text gets HIGH decision score
- **Status:** Open — Pre-existing, not caused by RC2 changes
- **Owner:** ML Engineering
- **Notes:** This may indicate calibration issues in the confidence engine for clearly legitimate messages.

### BUG-002: Pre-existing PredictionLogger File Persistence Failure
- **Severity:** Medium
- **Component:** Backend — ML Ops — PredictionLogger
- **Steps:**
  1. Run unit test `test_file_persistence`
  2. Observe assertion failure on empty directory state
- **Expected:** File persistence works correctly from initial state
- **Actual:** Assertion `False` fails on empty directory check
- **Status:** Open — Pre-existing, not caused by RC2 changes
- **Owner:** ML Ops
- **Notes:** May need a fixture reset or directory cleanup between test runs.

---

## Verified Fixed (RC1)

### BUG-F01: Probability Inversion in Benchmark Safe Predictions
- **Severity:** Critical
- **Status:** Verified Fixed
- **Commit:** c7f7af9
- **File:** `benchmarks/v2/scripts/models.py:181-191`
- **Root Cause:** Safe predictions had `probabilities["safe"]` and `probabilities["scam"]` swapped
- **Fix:** Use raw `probs[0]`/`probs[1]` directly instead of computing from confidence
- **Regression:** `benchmarks/tests/test_probability_inversion.py` (3 tests)

### BUG-F02: Threshold Optimization on Test Set (Data Leakage)
- **Severity:** High
- **Status:** Verified Fixed
- **Commit:** c7f7af9
- **File:** `benchmarks/v2/scripts/run_gamma_benchmark.py:97-106`
- **Root Cause:** Optimal threshold computed using X_test/y_test
- **Fix:** Use X_train/y_train for threshold tuning
- **Regression:** None needed (benchmark scripts are offline)

### BUG-F03: Duplicate Exception Hierarchies
- **Severity:** Medium
- **Status:** Verified Fixed
- **Commit:** c7f7af9
- **File:** `backend/domains/shared/exceptions.py`
- **Root Cause:** `domains/shared/exceptions.py` duplicated 22 classes from `core/exceptions.py`
- **Fix:** Replaced with imports from `core.exceptions`, keeping only `DomainError` and `NotFoundError`
- **Regression:** `tests/unit/test_pipeline_exceptions.py::TestC3ExceptionDeduplication` (4 tests)

### BUG-F04: Token Issuance Has Zero Authentication
- **Severity:** Critical
- **Status:** Verified Fixed
- **Commit:** c7f7af9
- **File:** `backend/routers/auth.py:61-80`
- **Root Cause:** `POST /auth/token` issued JWTs without any client credential
- **Fix:** Added `CLIENT_API_KEY` requirement; auth returns 401 without valid key
- **Regression:** `tests/security/test_auth.py::TestC4TokenRequiresClientKey` (3 tests)

### BUG-F05: Token Revocation Has No Authorization
- **Severity:** High
- **Status:** Verified Fixed
- **Commit:** c7f7af9
- **File:** `backend/routers/auth.py:200-214`
- **Root Cause:** `POST /auth/revoke` allowed anyone to revoke any token
- **Fix:** Added `Depends(require_auth)` dependency
- **Regression:** Included in C-4 regression test

### BUG-F06: Rate Limiter Fails Open When Redis Is Down
- **Severity:** Critical
- **Status:** Verified Fixed
- **Commit:** c7f7af9
- **File:** `backend/core/abuse.py:106-153`
- **Root Cause:** Redis failures silently allowed all requests (returned permissive defaults)
- **Fix:** Changed to fail-closed (deny, block, zero capacity) with structured error logging
- **Regression:** `tests/security/test_abuse.py::TestC6RedisFailClosed` (3 tests) + updated `tests/unit/test_scalability.py::TestRedisSlidingWindowRateLimiter::test_redis_failure_fails_closed`

### BUG-F07: K8s Missing tmpfs and Model Files
- **Severity:** Critical
- **Status:** Verified Fixed
- **Commit:** c7f7af9
- **Files:** `k8s/backend-deployment.yaml`, `backend/.dockerignore`
- **Root Cause:** No writable `/tmp` volume; `*.joblib` excluded from Docker image; `readOnlyRootFilesystem: true` with no writable paths
- **Fix:** Added `emptyDir` for `/tmp`; removed `*.joblib` from `.dockerignore`
- **Regression:** K8s YAML validation

### BUG-F08: No Deployment Stage in CI/CD
- **Severity:** Medium
- **Status:** Verified Fixed
- **Commit:** c7f7af9
- **File:** `.github/workflows/release.yml`
- **Root Cause:** Release workflow built images but never deployed
- **Fix:** Added deploy job for staging environment using kubectl
- **Regression:** CI pipeline validation

### BUG-F09: README and API Docs Outdated
- **Severity:** Medium
- **Status:** Verified Fixed
- **Commit:** c7f7af9
- **Files:** `README.md`, `docs/API_REFERENCE.md`
- **Root Cause:** Badges (244 tests → 820+, 83.3% → 95.1%), API paths had `/api/v1/` prefix
- **Fix:** Updated badges and rewrote API reference with correct paths
- **Regression:** Documentation review

### BUG-F10: No TypeScript Strict Mode
- **Severity:** Medium
- **Status:** Verified Fixed
- **Commit:** c7f7af9
- **File:** `frontend/tsconfig.app.json`
- **Root Cause:** No `"strict": true` in compiler options
- **Fix:** Added `"strict": true`
- **Regression:** `npm run build` succeeds

---

## RC2 Blockers Fixed

### BUG-RC2-01: Frontend Build Failure (@sentry/core)
- **Severity:** Critical
- **Status:** Verified Fixed
- **Commit:** b789ef9
- **File:** `frontend/package.json`
- **Root Cause:** `@sentry/react` v10+ requires `@sentry/core` which was not explicitly listed
- **Fix:** Added `"@sentry/core": "^10.68.0"` as explicit dependency

### BUG-RC2-02: K8s Secret Env Var Mismatch
- **Severity:** Critical
- **Status:** Verified Fixed
- **Commit:** b789ef9
- **File:** `k8s/secrets.yaml`
- **Root Cause:** Secret keys (`JWT_SECRET`, `ADMIN_API_KEY`) don't match backend env vars (`SCAMSHIELD_JWT_SECRET`, `SCAMSHIELD_ADMIN_API_KEY`)
- **Fix:** Renamed all keys to `SCAMSHIELD_*` prefix; added `SCAMSHIELD_CLIENT_API_KEY`

### BUG-RC2-03: .env.example Uses Non-Prefixed Variables
- **Severity:** High
- **Status:** Verified Fixed
- **Commit:** b789ef9
- **File:** `.env.example`
- **Root Cause:** Root `.env.example` used non-prefixed names (`MODEL_PATH`, `CORS_ORIGINS`, etc.) that don't match actual backend env vars
- **Fix:** Completely rewritten with `SCAMSHIELD_*` prefix matching all active backend settings

### BUG-RC2-04: Gitleaks Non-Blocking in CI
- **Severity:** High
- **Status:** Verified Fixed
- **Commit:** b789ef9
- **File:** `.github/workflows/ci.yml`
- **Root Cause:** `continue-on-error: true` on Gitleaks step allowed secrets to pass CI
- **Fix:** Removed `continue-on-error: true` — Gitleaks now blocks CI on secret detection

### BUG-RC2-05: Fail-Open Test Uses Wrong Assertion
- **Severity:** Medium
- **Status:** Verified Fixed
- **Commit:** b789ef9
- **File:** `backend/tests/unit/test_scalability.py`
- **Root Cause:** Test `test_redis_failure_falls_open` asserted old (insecure) fail-open behavior
- **Fix:** Renamed to `test_redis_failure_fails_closed` and updated assertions to verify deny-on-failure behavior

---

## QA Validation Blockers Fixed

### BUG-RC2-06: Frontend Container Crash (tmpfs Permission Denied)
- **Severity:** Critical
- **Status:** Verified Fixed
- **File:** `docker-compose.yml`
- **Root Cause:** tmpfs mounts for `/var/cache/nginx` and `/var/run` were root-owned (`drwxr-xr-x root:root`), but container runs as `appuser` (uid 1000) — nginx failed at startup with `mkdir() "/var/cache/nginx/client_temp" failed (13: Permission denied)`, causing crash loop
- **Fix:** Mounted tmpfs with `uid=1000,gid=1000`
- **Regression:** `docker compose up` — frontend container starts, serves HTTP 200, healthcheck passes

### BUG-RC2-07: API Proxy 404 via Nginx (/api prefix not stripped)
- **Severity:** Critical
- **Status:** Verified Fixed
- **File:** `frontend/nginx.conf`
- **Root Cause:** `location /api/` used `proxy_pass http://backend;` which forwards the full URI (`/api/analyze/text`) unchanged, but backend routes live at root (`/analyze/text`) — every proxied API call returned 404
- **Fix:** Added trailing slash: `proxy_pass http://backend/;` (strips the `/api/` prefix)
- **Regression:** `POST /api/analyze/text` via nginx returns 200 — scam sample `is_scam=true` (conf=0.910), legit sample `prediction=safe`

### BUG-RC2-08: Frontend Healthcheck Always Fails (localhost → IPv6)
- **Severity:** High
- **Status:** Verified Fixed
- **Files:** `docker-compose.yml`, `frontend/Dockerfile`
- **Root Cause:** Healthcheck used `wget http://localhost:80/`; `localhost` resolves to `::1`, but nginx listens on IPv4 only (`listen 80;` — the ipv6-by-default entrypoint script can't modify the conf as non-root `appuser`). Every healthcheck failed with "Connection refused" → container perpetually `unhealthy` (crash-looping restart policies would be useless)
- **Fix:** Healthcheck now targets `http://127.0.0.1:80/` in both compose and Dockerfile
- **Regression:** `docker compose ps` shows `scamshield-frontend Up (healthy)`

---

## Summary

| Category | Count |
|----------|-------|
| Open Bugs | 2 |
| Fixed (RC1) | 10 |
| Fixed (RC2) | 5 |
| Fixed (QA Validation) | 3 |
| **Total** | **20** |
