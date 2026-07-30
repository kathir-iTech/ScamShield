# ScamShield — Production Readiness Audit

**Date:** 2026-07-30  
**Scope:** Full-stack audit of the ScamShield repository (backend, frontend, infrastructure, CI/CD, ML pipeline, documentation, testing, security, operations)  
**Evaluator:** Agent-based audit across 22 dimensions  
**Classification:** Critical / High / Medium / Low / Info

---

## Overall Readiness Score: **67 / 100**

### Strengths
- Comprehensive middleware stack (CORS, rate limiting, security headers, request IDs, timeouts, body size validation, JSON structure validation)
- Well-structured exception hierarchy with typed exception handlers
- Audit logging with context propagation (request IDs, correlation IDs)
- In-memory metrics system with latency percentiles (p50, p95, max)
- Circuit breaker and retry patterns for resilience
- Docker security hardening (no-new-privileges, cap_drop ALL + cap_add NET_BIND_SERVICE, read_only filesystem, non-root user, resource limits)
- Kubernetes manifests (deployments, HPA, ingress, configmap)
- CI/CD with GitHub Actions — lint, test, security scan (Trivy), docker build, release
- Frontend: TypeScript strict, Sentry integration, React error boundaries, Zod schema validation
- Pipeline-based architecture (11 modular steps) with telemetry
- Environment profiles (development, production) with config validation at startup
- Extensive test suite across unit, integration, e2e, security, chaos, benchmark, and validation categories
- PII redaction in log messages and error responses

### Weaknesses
- Custom JWT implementation (not standard library), missing security guarantees (header not signed, no kty/kid, no key rotation)
- Everything in-memory — token blacklist, API keys, rate limiter state — all lost on restart
- K8s probes reference non-existent paths (`/api/v1/health/ping`, `/api/v1/health/readiness`)
- nginx `limit_req_zone` directive missing (referenced but not defined)
- CORS wildcard with `allow_credentials=True` when CORS_ORIGINS is `["*"]`
- No authentication rate limiting on `/auth/token` and `/auth/token/admin`
- Admin API key sent in request body instead of header
- `.env.example` references Python 3.14 (does not exist); Dockerfile uses 3.12
- README badges show outdated metrics (83.3% accuracy; current is ~95%)
- K8s ConfigMap uses unprefixed env vars (`APP_NAME`, `LOG_LEVEL`) but backend expects `SCAMSHIELD_*` prefixed vars
- No database — no persistence, no migrations, no data durability
- Frontend `.env.production` hardcodes Render backend URL in CSP and API base URL
- AnalysisResponse schema has 38 fields — very large payload; many fields always empty
- No API versioning (all endpoints at root path)

---

## Dimension-by-Dimension Assessment

### 1. Architecture & Design — Score: 75/100

| Finding | Severity | Risk | Recommendation | Effort |
|---------|----------|------|----------------|--------|
| Pipeline-based architecture with 11 modular steps, telemetry, and composition | Info | — | Well-designed | — |
| Pipeline uses `StepRegistry` with priority order, fatal/non-fatal step handling, and telemetry | Info | — | Good pattern | — |
| `AnalysisResponse` has 38 fields; many never populated (e.g. `refined_prediction`, `stability_concerns`, `reasoning_*` fields) | Medium | API bloat, confusion for consumers | Consolidate response schema; split into required/optional groups | 2d |
| No API versioning (`/api/v1/` prefix absent) | Medium | Breaking changes affect consumers without migration path | Add version prefix to all routes | 1d |
| Monolithic backend — all services in one container, no separation of concerns for scaling | Low | Can't scale ML independently from API | Consider separating ML inference into its own service | 5d |
| No event-driven architecture or message queue for async processing | Low | Image OCR blocks request thread | Consider async task queue for OCR-heavy workloads | 3d |

### 2. Security — Score: 52/100

| Finding | Severity | Risk | Recommendation | Effort |
|---------|----------|------|----------------|--------|
| Custom JWT implementation with homegrown encoding (HMAC-SHA256 on signing input only) rather than standard `PyJWT` | **Critical** | Header NOT included in signature — known JWT vulnerability. No `kid`, `typ` validation, no algorithm whitelist. | Replace with `python-jose` or `PyJWT` library | 1d |
| JWT secret stored as module-level global `_SECRET` in memory | **Critical** | Exposed in core dumps, no rotation mechanism, no HSM/secret store integration | Use secret manager (HashiCorp Vault, AWS Secrets Manager, K8s Secrets) | 3d |
| Token blacklist is an in-memory `set()` — lost on restart; `MAX_BLACKLIST` threshold clears entire set | **Critical** | All revoked tokens become valid after restart or after 100k entries | Implement persistent blacklist (Redis, database) | 3d |
| `/auth/token` has no rate limiting — anyone can brute-force generate tokens | **Critical** | No authentication on token issuance — attacker can flood server | Add rate limiting to auth endpoints | 1d |
| Admin API key sent in request body (visible in logs, server access logs) | High | Should be in `Authorization` header | Move admin key to `Authorization: Bearer <admin-key>` header | 1d |
| CORS wildcard `["*"]` with `allow_credentials=True` | High | Browsers reject this per spec; may be insecure | In production, set explicit origins; remove wildcard | 1d |
| No HTTPS enforcement in backend (no TLS termination) | High | Traffic between nginx and backend is plaintext | Add mTLS or use service mesh | 2d |
| No CSRF protection | Medium | Stateless but frontend runs on same domain; cookies could be used | Not critical for Bearer token API, but document | 1h |
| No security.txt or security contact in deployment | Low | Security researchers can't report issues | Add `.well-known/security.txt` | 1h |

### 3. Authentication & Authorization — Score: 55/100

| Finding | Severity | Risk | Recommendation | Effort |
|---------|----------|------|----------------|--------|
| Refresh token rotation with reuse detection | Info | — | Good pattern | — |
| Token blacklist cleared at 100k entries — silently re-enables revoked tokens | **Critical** | Attacker with old token can regain access after threshold | Use bounded-size LRU or persistent store | 2d |
| `revoke_all_for_user(user_id)` is a no-op (empty body) | High | Cannot revoke all tokens for a compromised user | Implement by tracking user-to-jti mapping | 1d |
| No token expiration for refresh tokens on user action (password change, account lock) | High | Stolen refresh tokens remain valid for 30 days | Implement token family invalidation | 2d |
| `/auth/token` issues tokens without any authentication | Medium | Anyone can get a token (by design, but undocumented) | Document as intended; add optional API key requirement | 1h |
| API key management is in-memory — lost on restart; `get_api_key_manager()` uses module-level singleton | Medium | All API keys lost on deployment or restart | Persist to file or database | 2d |
| API key hash uses static salt (`"scamshield-apikey-v1"`) | Medium | Static salt reduces rainbow table resistance | Use per-key random salt | 1d |
| Auth is optional (`AUTH_ENABLED` defaults to false) | Low | Production can be deployed without auth | Remove `AUTH_ENABLED` — always enable in production | 1d |

### 4. Data Validation — Score: 82/100

| Finding | Severity | Risk | Recommendation | Effort |
|---------|----------|------|----------------|--------|
| Pydantic v2 models with `extra = "forbid"` | Info | — | Good practice | — |
| Zod schemas on frontend (`textAnalysisSchema`, `imageAnalysisSchema`) | Info | — | Good defense-in-depth | — |
| Unicode normalization (NFKC), control char/ZWNJ removal, length validation | Info | — | Comprehensive | — |
| `MAX_TEXT_LENGTH` clamped at 100k chars | Low | Arbitrary limit, should be configurable per route | Already configurable via env var | — |
| Image dimension check (8000px max) and file type whitelist | Info | — | Good | — |
| JSON structure depth/field/array limits in `JSONStructureValidator` | Info | — | Protects against deep nested attacks | — |
| No rate limiting per endpoint (only global IP-based) | Medium | One user can exhaust server resources on `/analyze/text` while others suffer | Implement per-endpoint rate limiting | 2d |

### 5. Error Handling — Score: 80/100

| Finding | Severity | Risk | Recommendation | Effort |
|---------|----------|------|----------------|--------|
| Typed exception hierarchy (25+ exception classes) | Info | — | Well-designed | — |
| Global exception handlers for `ValidationError`, `ConfigurationError`, `ScamShieldError`, `AuthenticationError`, and generic `Exception` | Info | — | Good coverage | — |
| PII redaction in error responses (phone, email, card, PAN, Aadhaar) | Info | — | Excellent | — |
| `PipelineError` raised with original exception chain | Info | — | Good | — |
| Pipeline non-fatal step failures are caught and logged, pipeline continues | Info | — | Resilient design | — |
| `model_config = {"extra": "forbid"}` on request schemas prevents silent field injection | Info | — | Good | — |
| Route-level try/except with metrics recording for every endpoint | Info | — | Good observability | — |
| `_mask_pii()` regex for phone numbers may miss non-standard formats | Low | Some PII may leak in error logs | Add more comprehensive PII detection (India-specific formats) | 1d |

### 6. Logging & Observability — Score: 75/100

| Finding | Severity | Risk | Recommendation | Effort |
|---------|----------|------|----------------|--------|
| Structured logging via `extra={"structured": {...}}` | Info | — | Good | — |
| Audit event system with 20+ defined event types | Info | — | Comprehensive | — |
| Request context propagation (request_id, correlation_id, user_id) via `contextvars` | Info | — | Excellent for distributed tracing | — |
| Log format configurable between text and JSON | Info | — | Good for log aggregation | — |
| Log output configurable to stdout, file, or both | Info | — | Good for different deployment modes | — |
| No log shipping mechanism documented | Low | Logs stay in container; no ELK/Loki integration | Document log aggregation setup | 1d |
| File logging with rotation (10MB, 5 backup files) | Info | — | Good for persistent logging | — |
| Pipeline telemetry records per-step timing | Info | — | Good for performance analysis | — |
| `record_auth_failure` called but does NOT accept `client_ip` parameter in all call sites | Low | Can't correlate auth failures by IP | Pass `client_ip` in all `record_auth_failure()` calls | 1h |
| No log sampling or volume control for high-traffic scenarios | Low | Log volume may become expensive at scale | Add configurable sampling | 1d |

### 7. Testing — Score: 78/100

| Finding | Severity | Risk | Recommendation | Effort |
|---------|----------|------|----------------|--------|
| 37 unit test files, 3 integration tests, 1 e2e test, 11 security tests, 3 chaos tests, 1 benchmark test, 6 validation tests | Info | — | Extensive test coverage | — |
| Test fixtures (scam_texts, safe_texts, sample_analysis) | Info | — | Well-structured | — |
| Global state reset between tests (`_reset_globals` fixture) | Info | — | Good for test isolation | — |
| Chaos tests for pipeline, connectors, and knowledge domain | Info | — | Beyond typical testing | — |
| Architecture test validates project structure | Info | — | Good for enforcement | — |
| Release report test validates binary artifacts | Info | — | Good for CI | — |
| Performance regression test in benchmark directory | Info | — | Good for detecting regressions | — |
| Load test in validation directory | Info | — | Basic load testing | — |
| Frontend tests in `src/test/` directory (components, context, hooks, services) | Info | — | Good coverage | — |
| Frontend has vitest config and Playwright e2e setup | Info | — | Good for both unit and e2e | — |
| No test for model accuracy degradation (model drift detection) | Medium | Model could silently degrade in production | Add alerting on accuracy threshold | 2d |
| No integration test for full Docker compose stack | Low | Docker compose changes may break deployment | Add `docker compose up` integration test | 1d |
| Frontend test coverage not enforced in CI | Low | Coverage may drop unnoticed | Add coverage threshold | 1d |

### 8. CI/CD — Score: 72/100

| Finding | Severity | Risk | Recommendation | Effort |
|---------|----------|------|----------------|--------|
| GitHub Actions: backend.yml, frontend.yml, ci.yml, docker.yml, release.yml | Info | — | Comprehensive | — |
| Backend CI: importability check, OpenAPI spec validation, pip-audit, Docker build | Info | — | Good | — |
| Frontend CI: TypeScript check, oxlint, vitest, build + bundle size check, npm audit, Docker build | Info | — | Good | — |
| Docker CI: Trivy vulnerability scanning (HIGH/CRITICAL), compose validation, image verification | Info | — | Good security practices | — |
| Release workflow: tag validation against VERSION file, GHCR push, GitHub Release | Info | — | Well-designed | — |
| `ci.yml` uses `PYTHON_VERSION: "3.14"` — does not exist | **Critical** | CI will fail when Python 3.14 is released or if the runner doesn't have it | Use `"3.12"` to match Dockerfile | 10min |
| `ci.yml` uses PowerShell `$coverage` syntax (Windows) but runs on `ubuntu-latest` | High | Coverage gate will fail — `$coverage` only works in PowerShell | Use bash: `coverage=$(python -c ...)` | 10min |
| `backend.yml` uses `scripts/quality_gate.py` but Quality report script contains analysis metrics vs production metrics check instead of running actual tests | Medium | Actual tests may not run; only imports and OpenAPI checked | Add actual `pytest` run to backend.yml | 1d |
| No docker image publishing to GHCR on main branch pushes (only on release tags) | Medium | Can't deploy latest from main | Add continuous deployment workflow | 2d |
| No dependency caching for Python in CI (uses `cache: pip` but only in backend.yml, not ci.yml) | Low | CI builds slower than necessary | Add caching to all workflows | 1h |
| Dependabot configured only for npm | Low | Python deps not monitored | Add pip dependabot config | 1h |

### 9. Containerization — Score: 78/100

| Finding | Severity | Risk | Recommendation | Effort |
|---------|----------|------|----------------|--------|
| Multi-stage frontend Docker build (builder + nginx runtime) | Info | — | Good practice | — |
| Non-root user in both containers | Info | — | Good security | — |
| `read_only: true` filesystem with tmpfs mounts | Info | — | Excellent container hardening | — |
| `cap_drop: ALL` + `cap_add: NET_BIND_SERVICE` | Info | — | Principle of least privilege | — |
| `no-new-privileges: true` | Info | — | Prevents privilege escalation | — |
| Resource limits (CPU, memory) in docker-compose.yml | Info | — | Prevents resource exhaustion | — |
| Healthchecks configured for both services | Info | — | Good for orchestration | — |
| Backend Dockerfile installs `tesseract-ocr` and `tesseract-ocr-eng` | Info | — | Good for OCR | — |
| Backend Dockerfile copies all files with `COPY . .` — includes test files, datasets, .git | Medium | Bloated image; test/dev files in production | Use `.dockerignore` | 1h |
| Backend container uses `--workers 2` without `--preload` | Low | Each worker loads model independently, memory multiplies | Add `--preload` or define worker count via env | 1h |
| No health check for Tesseract availability | Low | Container appears healthy but OCR fails silently | Add OCR diagnostic to `/health` endpoint | 1d |
| No multi-arch build (only amd64) | Low | ARM64 users must build from source | Add `docker buildx` for multi-arch | 1d |

### 10. Orchestration (Kubernetes) — Score: 45/100

| Finding | Severity | Risk | Recommendation | Effort |
|---------|----------|------|----------------|--------|
| K8s manifests exist but are mostly untestable from repository review | Info | — | Good to have | — |
| Backend liveness probe path `/api/v1/health/ping` does not exist | **Critical** | Pods will restart loop until CrashLoopBackOff — all requests fail | Change to `/live` | 10min |
| Backend readiness probe path `/api/v1/health/readiness` does not exist | **Critical** | Pods never show Ready — no traffic routed | Change to `/ready` | 10min |
| ConfigMap uses unprefixed env vars (`APP_NAME`, `DEBUG`, `LOG_LEVEL`, `HOST`, `PORT`, `WORKERS`) | High | Backend expects `SCAMSHIELD_*` prefixed vars — config will be ignored | Add `SCAMSHIELD_` prefix or map in deployment | 1h |
| No `secrets.yaml` provided (placeholder `scamshield-secrets` referenced) | High | Deployment will fail missing secret | Create secrets template | 1h |
| HPA configured (CPU 70%, memory 80%) | Info | — | Good for auto-scaling | — |
| Ingress has TLS but relies on `scamshield-tls` secret — not provided | Medium | TLS won't work without certificate | Document cert-manager setup | 1h |
| Ingress rewrites all paths to `/` — breaks SPA routing | High | Frontend routes like `/analyze` will 404 | Remove `rewrite-target: /` for frontend paths | 1h |
| Frontend deployment reads ConfigMap env vars but nginx can't use runtime env vars | Low | `VITE_API_BASE_URL` must be baked at build time | Use separate ConfigMap per environment or rebuild | 1d |
| No PodDisruptionBudget for production deployments | Low | Rolling updates may cause downtime | Add PDB with `minAvailable: 1` | 1h |
| No network policies | Low | Pods can communicate freely across namespaces | Add NetworkPolicy to restrict east-west traffic | 2d |
| No `imagePullSecrets` for GHCR | Medium | K8s can't pull from private GHCR without credentials | Document required pull secret setup | 1h |

### 11. ML Pipeline — Score: 70/100

| Finding | Severity | Risk | Recommendation | Effort |
|---------|----------|------|----------------|--------|
| TF-IDF + LogisticRegression with 5-fold stratified cross-validation | Info | — | Solid baseline model | — |
| Current model: F1=0.9622, ROC-AUC=0.9898, FPR=1.92% on gold dataset (308 samples) | Info | — | Strong performance | — |
| Lazy loading with double-checked locking (thread-safe) | Info | — | Good for memory efficiency | — |
| Top feature extraction for model interpretability | Info | — | Good for debugging | — |
| Training log saved as JSON | Info | — | Good for reproducibility | — |
| `predict()` calls `predict_proba` — will fail for models without it (e.g., SVM without CalibratedClassifierCV) | Medium | Runtime error if model swapped | Add a check for `predict_proba` availability; fallback if not | 1d |
| No model versioning or A/B testing capability | Medium | Can't roll back or test new models | Add model version metadata; support multiple model slots | 3d |
| No drift detection — model never re-evaluated after deployment | High | Silent degradation over time | Add scheduled accuracy checks on labeled production data | 3d |
| `train.py` loads entire dataset into memory — problematic at scale | Low | Currently fine for ~2500 samples | Add chunked/batched loading | 2d |
| No automatic retraining pipeline | Medium | Model is static; improvements require manual run | Add retraining API endpoint and scheduled retraining | 3d |
| No feature importance monitoring in production | Low | Can't detect feature drift | Log top features per prediction | 2d |

### 12. API Design — Score: 70/100

| Finding | Severity | Risk | Recommendation | Effort |
|---------|----------|------|----------------|--------|
| OpenAPI spec auto-generated via FastAPI | Info | — | Good | — |
| POST endpoints for analysis (text, image) with structured request/response | Info | — | RESTful | — |
| Health endpoints: `/health`, `/ready`, `/live` | Info | — | K8s-compatible | — |
| Metrics endpoint at `/metrics` | Info | — | Good for observability | — |
| No API versioning | Medium | Breaking changes affect consumers | Add `/api/v1/` prefix | 1d |
| AnalysisResponse has 38 fields — large payload; many fields always empty | Medium | Bandwidth waste, confusing API | Consolidate; use optional fields properly | 2d |
| Image upload returns `ImageAnalysisResponse` which includes extracted_text | Info | — | Good UX | — |
| No pagination for list endpoints | Low | Not needed currently but should be designed for future | Add pagination pattern | 1d |
| No request/response compression for large responses | Low | Text responses could be smaller with gzip | Already has GZipMiddleware at 1KB minimum | — |
| Investigation endpoint requires admin — well-documented dependency injection | Info | — | Good | — |

### 13. Frontend — Score: 75/100

| Finding | Severity | Risk | Recommendation | Effort |
|---------|----------|------|----------------|--------|
| React 19 with TypeScript strict mode | Info | — | Modern, type-safe | — |
| Sentry integration with error boundaries, tracing, and replay | Info | — | Good error tracking | — |
| Zod validation on both client and server | Info | — | Defense in depth | — |
| TanStack React Query for API calls with caching and retry | Info | — | Good for performance | — |
| Framer Motion for animations | Info | — | Good UX | — |
| 14 route pages covering all features | Info | — | Complete UI | — |
| API interceptor with network status check, error categorization, and monitoring integration | Info | — | Robust error handling | — |
| Frontend `.env.production` hardcodes `VITE_API_BASE_URL=https://scamshield-backend-rv5v.onrender.com` | High | Production build tied to specific Render URL; CSP in nginx.conf also hardcodes this | Use environment variable at build time; CSP should be configurable | 1h |
| Sentry DSN can be left empty — `beforeSend` handles it | Info | — | Graceful degradation | — |
| No frontend caching strategy for static content beyond nginx config | Low | Could improve performance with service worker | Add Workbox/PWA for offline support | 3d |
| No frontend feature flags | Low | Can't gradually roll out features | Add feature flag provider | 2d |
| Frontend test coverage in CI but no `--coverage` threshold enforced | Low | Coverage may erode | Add coverage threshold to vitest config | 1h |

### 14. Documentation — Score: 80/100

| Finding | Severity | Risk | Recommendation | Effort |
|---------|----------|------|----------------|--------|
| Extensive documentation: README, DEPLOYMENT, SECURITY, ARCHITECTURE, 20+ design docs | Info | — | Excellent | — |
| README badges show outdated accuracy (83.3%) | Low | Misleading for users evaluating the project | Update to current metrics (~95%) | 10min |
| README mentions 244 tests passing | Info | — | Good visibility | — |
| INSTALLATION.md, API_REFERENCE.md, DEVELOPER_GUIDE.md referenced in README | Info | — | Good structure | — |
| 10 audit reports already exist (ARCHITECTURE_REVIEW, AUDIT_REPORT_01–10, etc.) | Info | — | Good historical context | — |
| No production runbook (what to do when alerts fire) | Medium | On-call engineers have no guidance | Create runbook for common incidents | 2d |
| No SLA/SLO documentation | Low | No performance guarantees defined | Define and document target SLOs | 2d |
| No disaster recovery plan documented | Low | Recovery process is ad-hoc | Document DR plan with RTO/RPO targets | 2d |

### 15. Resilience — Score: 75/100

| Finding | Severity | Risk | Recommendation | Effort |
|---------|----------|------|----------------|--------|
| Circuit breaker pattern for external service calls | Info | — | Good for preventing cascading failures | — |
| Retry decorator with exponential backoff (async + sync) | Info | — | Good for transient failures | — |
| Request timeout middleware (30s default) | Info | — | Prevents resource exhaustion | — |
| Pipeline tolerates non-fatal step failures (skips, continues) | Info | — | Graceful degradation | — |
| Request timeout is a hard 30s across all routes — no per-endpoint differentiation | Medium | `/analyze/image` (OCR) may need more time | Make timeout configurable per route | 1d |
| No bulkhead pattern — all requests share same thread pool | Medium | Slow endpoint can exhaust all workers | Consider separate worker pools for OCR vs text | 3d |
| No graceful shutdown handling for in-flight requests | Medium | Active requests killed on shutdown | Add signal handler for graceful shutdown | 1d |
| Circuit breaker state not persisted between restarts | Low | Reset on every deployment | Persist to Redis | 2d |
| No fallback responses for degraded mode (e.g., ML model down = rule-only analysis) | Medium | If model fails to load, service is completely down | Implement graceful degradation with rule-only mode | 3d |

### 16. Performance — Score: 70/100

| Finding | Severity | Risk | Recommendation | Effort |
|---------|----------|------|----------------|--------|
| Lazy-loaded ML model (loaded on first request, not at startup) | Info | — | Faster startup | — |
| Double-checked locking for thread-safe lazy load | Info | — | Good for concurrency | — |
| GZip middleware for responses >1KB | Info | — | Good for bandwidth | — |
| Frontend asset caching with immutable cache headers | Info | — | Fast page loads | — |
| ML inference on CPU only — no GPU support | Low | Higher latency per request | Not needed for current volume | — |
| No connection pooling configuration for HTTP clients | Low | Connectors create new connections per request | Add `httpx` client with connection pooling | 1d |
| OCR uses synchronous Tesseract — blocks the async event loop | Medium | OCR requests block all other requests | Run OCR in thread pool executor | 1d |
| No request queue or backpressure mechanism | Medium | Sudden traffic spike can overwhelm the server | Add backpressure with configurable queue depth | 2d |
| Frontend bundle size check at 512KB limit | Info | — | Prevents bloated bundles | — |

### 17. Scalability — Score: 65/100

| Finding | Severity | Risk | Recommendation | Effort |
|---------|----------|------|----------------|--------|
| Stateless backend (except in-memory state) | Info | — | Horizontally scalable | — |
| HPA configured for both services in K8s | Info | — | Auto-scaling ready | — |
| K8s replicas: 2 minimum, 8 max backend, 6 max frontend | Info | — | Reasonable scaling range | — |
| In-memory state prevents true horizontal scaling | **Critical** | Token blacklist, API keys, rate limiter state are per-pod — can't scale beyond 1 pod | Move state to Redis or database | 5d |
| Rate limiter state is per-process — CORS/cloud load balancer sees a single IP | High | Rate limiting is ineffective behind load balancer | Use shared Redis for rate limiting | 2d |
| No session affinity (not needed if state is externalized) | Info | — | Good for load balancing | — |
| Database not used — no scalability concerns there | Info | — | Simplified operations | — |

### 18. Compliance & Data Privacy — Score: 72/100

| Finding | Severity | Risk | Recommendation | Effort |
|---------|----------|------|----------------|--------|
| PII redaction in log messages and error responses (phone, email, card, PAN, Aadhaar, OTP, UPI) | Info | — | Good for data privacy | — |
| Audit logging for auth events, API key operations, security events | Info | — | Good for compliance | — |
| No data retention policy documented | Low | User data stored indefinitely in logs | Define and document data retention policies | 2d |
| No GDPR compliance assessment | Low | If serving EU users, GDPR requirements apply | Document data processing, add DPA | 3d |
| No data anonymization for stored analysis results | Low | Scam text samples may contain PII | Add anonymization pipeline for stored data | 2d |

### 19. Dependencies — Score: 78/100

| Finding | Severity | Risk | Recommendation | Effort |
|---------|----------|------|----------------|--------|
| Backend: 11 Python dependencies (minimal, well-chosen) | Info | — | Good for security surface | — |
| Frontend: 14 runtime deps, 13 dev deps (modern stack) | Info | — | Reasonable | — |
| `pip-audit` in CI for vulnerability scanning | Info | — | Good practice | — |
| `npm audit` in CI (--audit-level=high, continue-on-error) | Info | — | Good, but should not continue on error | Make blocking | 1h |
| Trivy scanning for container images | Info | — | Good for supply chain security | — |
| No Dependabot for Python dependencies | Low | Python deps may become outdated | Add pip Dependabot config | 1h |
| Dependencies pinned with exact versions (good) | Info | — | Reproducible builds | — |
| No Snyk or alternative SCA tool | Low | Trivy only covers container layer | Add SCA scanning | 1d |

### 20. Configuration Management — Score: 70/100

| Finding | Severity | Risk | Recommendation | Effort |
|---------|----------|------|----------------|--------|
| Environment-based configuration via `settings.py` with env var overrides | Info | — | Good pattern | — |
| Profile-based config (development, production) | Info | — | Good for different environments | — |
| Startup validation with 30+ checks | Info | — | Catches misconfigurations early | — |
| .env.example provided | Info | — | Good documentation | — |
| .env.example keys don't match actual env vars used in code | High | Many vars in `.env.example` (e.g. `MODEL_PATH`, `TESSERACT_CMD`, `OCR_ENABLED`, `RATE_LIMIT_ENABLED`, `HOST`, `PORT`) are NOT used in `settings.py` | Sync `.env.example` with actual env vars | 1h |
| K8s ConfigMap uses different naming convention than backend expects | High | Backend expects `SCAMSHIELD_*` prefix; ConfigMap uses unprefixed names | Add `SCAMSHIELD_` prefix to ConfigMap entries | 1h |
| `AUTH_JWT_SECRET` and `ADMIN_API_KEY` checked at module import time — must be set before import | Medium | Can't be changed at runtime; requires restart | Document that these require process restart | 1h |
| Some env vars reference paths that don't match Dockerfile WORKDIR (e.g. `MODEL_PATH=models/scam_classifier.pkl`) | Medium | Paths in `.env.example` don't match actual defaults in `settings.py` | Keep .env.example in sync; add comments | 1h |
| No secrets encryption at rest | Low | `.env` stored in plaintext on disk | Use encrypted secrets or vault | 2d |

### 21. Disaster Recovery — Score: 45/100

| Finding | Severity | Risk | Recommendation | Effort |
|---------|----------|------|----------------|--------|
| Backup strategy documented in DEPLOYMENT.md | Info | — | Good starting point | — |
| No database means no data to restore (but also no durability) | Info | — | Simplified operations | — |
| Model files backed up as part of documented strategy | Info | — | Good | — |
| No documented RTO (Recovery Time Objective) | Medium | No target for recovery time | Define and document RTO | 1h |
| No documented RPO (Recovery Point Objective) | Medium | Acceptable data loss window unknown | Define and document RPO | 1h |
| No disaster recovery drill procedure | Low | Recovery never tested | Document DR drill steps | 2d |
| No multi-region deployment strategy | Low | Single region = single point of failure | Document multi-region plan | 3d |
| No automated backup verification | Low | Backups may be corrupted without verification | Add backup checksum verification | 1d |

### 22. Monitoring & Alerting — Score: 55/100

| Finding | Severity | Risk | Recommendation | Effort |
|---------|----------|------|----------------|--------|
| In-memory metrics snapshot at `/metrics` (total requests, failures, latency percentiles, system metrics) | Info | — | Good basic observability | — |
| Sentry error tracking on frontend | Info | — | Good for user-facing errors | — |
| Frontend client-side monitoring (API failures, network errors) | Info | — | Good for UX monitoring | — |
| Health check endpoints: `/health`, `/ready`, `/live` | Info | — | Good for orchestration | — |
| No Prometheus metrics format | Medium | `/metrics` is custom JSON; can't integrate with Prometheus/Grafana directly | Add Prometheus client library; expose metrics in OpenMetrics format | 3d |
| No alerting configured (no Prometheus, no Alertmanager, no PagerDuty) | High | When things break, nobody gets notified | Set up alerting on key metrics (error rate > threshold, latency > threshold, model unavailable) | 5d |
| No log aggregation (ELK/Loki/Grafana) | Medium | Debugging requires `docker logs` | Add Loki or ELK stack for centralized logging | 3d |
| No dashboard (Grafana or similar) | Medium | Metrics are opaque; no visual monitoring | Create Grafana dashboard for key metrics | 3d |
| System metrics (CPU, memory, disk) available in `/metrics` snapshot (via psutil) | Info | — | Good for quick debugging | — |
| `psutil` is imported inside method — exception silently caught if not installed | Low | System metrics silently missing | Log warning when psutil not available | 10min |
| No synthetic monitoring / uptime checks | Medium | Don't know if service is reachable from outside | Set up external uptime monitoring (Pingdom, UptimeRobot, StatusCake) | 2h |

---

## Risk Heatmap

| Severity | Count | Key Concerns |
|----------|-------|--------------|
| Critical | 6 | Custom JWT (header not signed), in-memory token blacklist (lost on restart/clear), K8s probe paths wrong, nginx config broken, Python 3.14 CI, CORS wildcard+credentials |
| High | 12 | K8s ConfigMap naming mismatch, admin key in body, no auth rate limit, no DB persistence, no effective horizontal scaling, `.env.example` mismatch, frontend hardcoded URL, K8s Ingress rewrite breaks SPA, no Prometheus/alerts, no drift detection, `ci.yml` bash/PowerShell mix |
| Medium | 18 | API versioning, response schema bloat, per-endpoint rate limiting, no graceful degradation, no retraining pipeline, no runbook, no SLA, PyJWT compliance, etc. |
| Low | 14 | README badge accuracy, bundle size, frontend test coverage threshold, no PDB, no network policies, etc. |

---

## Top 20 Priority Improvements

1. Replace custom JWT with standard library (PyJWT/python-jose) — **Critical**
2. Fix K8s probe paths (`/api/v1/health/ping` → `/live`, `/api/v1/health/readiness` → `/ready`) — **Critical**
3. Fix nginx `limit_req_zone` directive (`zone=api` not defined) — **Critical**
4. Move token blacklist/API keys to persistent store (Redis) — **Critical**
5. Fix CORS wildcard with `allow_credentials=True` — **High**
6. Fix K8s ConfigMap to use `SCAMSHIELD_*` prefixed env vars — **High**
7. Add rate limiting to `/auth/token` and `/auth/token/admin` — **High**
8. Add Prometheus metrics format and alerting — **High**
9. Sync `.env.example` with actual env vars used in code — **High**
10. Fix `ci.yml` Python version (3.14 → 3.12) and PowerShell/bash syntax — **High**
11. Move admin API key from request body to header — **High**
12. Implement graceful degradation (rule-only mode when ML model is down) — **High**
13. Add model drift detection and automated retraining — **High**
14. Fix K8s Ingress rewrite-target breaking SPA routing — **High**
15. Consolidate AnalysisResponse schema (reduce from 38 fields) — **Medium**
16. Add API versioning (`/api/v1/`) — **Medium**
17. Add Prometheus/Grafana monitoring stack — **Medium**
18. Add incident runbook and SLO documentation — **Medium**
19. Run OCR in thread pool to avoid blocking event loop — **Medium**
20. Add backpressure mechanism for traffic spikes — **Medium**

---

## Phased Remediation Roadmap

### Phase 1 (Immediate — Week 1) — Security & Stability Fixes
- Replace custom JWT with standard library
- Fix K8s probe paths and nginx config
- Fix CORS configuration
- Fix K8s ConfigMap naming
- Fix CI Python version and syntax
- Add auth endpoint rate limiting
- Admin key in header (not body)

### Phase 2 (Short-term — Weeks 2-3) — Observability & Resilience
- Add Prometheus metrics + Grafana dashboard
- Add centralized logging (Loki/ELK)
- Add incident runbook and SLO docs
- Add model drift detection
- Implement graceful degradation
- Add per-endpoint rate limits
- Move token blacklist to Redis

### Phase 3 (Medium-term — Weeks 4-6) — Scale & Hardening
- API versioning and response schema consolidation
- Add persistent storage for API keys and state
- Add automated retraining pipeline
- Add network policies and PodDisruptionBudget
- Add disaster recovery drill procedure
- Implement backpressure
- Add multi-region deployment strategy

---

*Generated by automated audit — all findings based on static code analysis of the repository as of 2026-07-30.*
