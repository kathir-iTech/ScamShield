# ScamShield — Final Independent Engineering Review

**Reviewer:** Independent adversarial audit (static code analysis)
**Date:** 2026-07-31
**Scope:** Full repository — architecture, security, AI/ML, testing, DevOps, frontend, documentation, datasets
**Methodology:** All findings verified against source code. No assumptions. No hypotheticals.

---

## Executive Summary

ScamShield has substantial engineering investment but **is not production-ready** in its current state. The codebase contains **10 CRITICAL**, **23 HIGH**, **31 MEDIUM**, and **22 LOW** verifiable issues across all review dimensions. The most severe findings include a **probability inversion bug in the benchmark that invalidates all published ML metrics**, a **completely unauthenticated token issuance endpoint** (anyone can mint valid JWTs), **Kubernetes configurations that will crash on startup** (missing tmpfs under readOnlyRootFilesystem + missing PVC for models), and **a test suite whose reported pass count doesn't match reality** (three conflicting numbers: 820, 831, 920).

**Overall Engineering Score: 34/100**

### Would I approve deployment? **NO**

---

## Issue Index by Severity

| Severity | Count |
|----------|-------|
| CRITICAL | 10 |
| HIGH | 23 |
| MEDIUM | 31 |
| LOW | 22 |
| **Total** | **86** |

---

## CRITICAL ISSUES (10)

### C-1: Benchmark Probability Inversion Bug Invalidates All Published ML Metrics

**Category:** AI/ML
**Files:** `benchmarks/v2/scripts/models.py:181-190`
**Evidence:** When the model predicts "safe" (pred=0), `confidence` is set to `probs[0]` (the safe probability), but then assigned as the **scam** probability in the output dict. For every safe prediction, scam and safe probabilities are inverted. This corrupts all ROC-AUC values in the benchmark reports. Published AUC for tfidf_lr is 0.5919 (should be ~0.98). SVM AUC of 0.5000 is published without caveat (LinearSVC lacks predict_proba).
**Impact:** All model selection decisions, benchmark comparisons, and published performance metrics are built on corrupted data. The decision to use the current production model cannot be justified by these benchmarks.

### C-2: Threshold Optimization on Test Set (Data Leakage)

**Category:** AI/ML
**Files:** `benchmarks/v2/scripts/run_gamma_benchmark.py:97-106`, `run_beta_benchmark.py:97-106`
**Evidence:** The classification threshold is tuned by testing 81 candidate thresholds against the **test set labels**, then selecting the best one. All reported metrics (accuracy, precision, recall, F1) are evaluated at this test-set-optimized threshold.
**Impact:** Reported benchmark F1 scores (0.9749 embedding, 0.9711 tfidf_lr, 0.9827 tfidf_svm) are optimistically biased. Real-world performance will be materially lower.

### C-3: Duplicate Exception Hierarchies Cause Uncatchable Errors

**Category:** Architecture
**Files:** `backend/core/exceptions.py:1-106`, `backend/domains/shared/exceptions.py:1-110`
**Evidence:** Two completely separate exception class trees define identical exception types (ScamShieldError, ConfigurationError, ValidationError, ModelLoadError, etc.) with no inheritance relationship. An exception raised as `core.exceptions.ValidationError` will NOT be caught by `except domains.shared.exceptions.ValidationError`.
**Impact:** Latent production bug — domain code raising exceptions will not be caught by router-level error handlers, producing unhandled 500 errors in API responses.

### C-4: Token Issuance Has Zero Authentication

**Category:** Security
**Files:** `backend/routers/auth.py:61-80`
**Evidence:** The `POST /auth/token` endpoint accepts **no credentials** — no username, password, API key, or identity proof. It generates a subject from the current Unix timestamp (`f"user_{int(time.time())}"`). The only barrier is a rate limiter (20 req/60s default).
**Impact:** Any unauthenticated attacker can mint valid JWTs with `role: "authenticated"`. An attacker can generate hundreds of valid tokens per minute, then use them to access any authenticated endpoint.

### C-5: Token Revocation Has No Authorization Check (IDOR)

**Category:** Security
**Files:** `backend/routers/auth.py:200-214`
**Evidence:** The `POST /auth/revoke` endpoint performs no authentication or authorization. Any party (even without a token) can submit any valid JWT and have it immediately blacklisted.
**Impact:** An attacker can perform mass denial-of-service against all valid users by collecting tokens and revoking them. Every token in the system can be invalidated.

### C-6: Rate Limiter Fails Open When Redis Is Down

**Category:** Security
**Files:** `backend/core/abuse.py:106-112,117-130`
**Evidence:** Both `is_blocked()` and `record_request()` in `RedisSlidingWindowRateLimiter` catch all exceptions and return permissive values: `is_blocked` → `False` (never block), `record_request` → `True` (always allow).
**Impact:** An attacker who causes Redis to become unavailable (resource exhaustion, network flooding) completely bypasses all rate limiting.

### C-7: K8s Backend Pods Will CrashLoopBackOff (Missing tmpfs + PVC)

**Category:** DevOps/Kubernetes
**Files:** `k8s/backend-deployment.yaml:50-58`
**Evidence:** The pod spec sets `readOnlyRootFilesystem: true` but defines **no volumes** — no `tmpfs` for `/tmp`, no `PersistentVolumeClaim` for model data. Python, uvicorn, and tempfile all require writable `/tmp`. Model files (`model.joblib`, `vectorizer.joblib`) have no persistent storage.
**Impact:** Backend pods will never reach Ready state. The entire application is non-functional in Kubernetes.

### C-8: No Deployment Stage in CI/CD (100% CI, 0% CD)

**Category:** DevOps/CI/CD
**Files:** `.github/workflows/release.yml`, `.github/workflows/ci.yml`, all workflow files
**Evidence:** None of the 5 CI workflows perform any deployment to any environment. After a successful release, a human must SSH into a server and manually run `docker compose pull && docker compose up -d`.
**Impact:** Deployment is manual, error-prone, and un-audited. Lead time from commit to production is unbounded. No canary, blue-green, or rollback automation.

### C-9: README Documentation Is Dangerously Outdated

**Category:** Documentation
**Files:** `README.md:5-6,100-108`, `docs/API_REFERENCE.md:9-14`
**Evidence:** README claims 83.3% accuracy (actual: 95.13%). Claims API endpoints at `/api/v1/` prefix (actual: root-level `/analyze/text`, `/health`, etc.). Any integration built against these docs will fail with 404 errors.
**Impact:** Public face of the project understates performance by 12pp. API consumers following the docs get guaranteed production incidents.

### C-10: No TypeScript Strict Mode — Null References Compile Silently

**Category:** Frontend
**Files:** `frontend/tsconfig.app.json:2-31`, `frontend/tsconfig.node.json:2-22`
**Evidence:** `strict: true` is NOT set in either tsconfig. Missing strictNullChecks, noImplicitAny, strictFunctionTypes, etc.
**Impact:** Any type errors, potential null references, `any`-typed parameters, and unsafe function assignments compile silently. In a safety-critical scam detection app, a single null-render crash destroys user trust.

---

## HIGH ISSUES (23)

### H-1: Production .env Ships with Placeholder Secrets
**Files:** `backend/.env.production:11-12`
**Evidence:** `JWT_SECRET=change-this-to-a-strong-random-secret`, `ADMIN_API_KEY=change-this-to-a-strong-random-api-key`. No startup enforcement against these values.
**Impact:** If deployed as-is, anyone reading the public repo can forge JWTs and escalate to admin.

### H-2: API Key Hashing Uses Static Hardcoded Salt
**Files:** `backend/core/api_keys.py:157-159`
**Evidence:** `salt = "scamshield-apikey-v1"` — identical across all deployments. Single SHA-256 round with no key stretching.
**Impact:** If the in-memory hash table is leaked, precomputation attacks are feasible.

### H-3: In-Memory Token Blacklist Loses All Entries on Overflow
**Files:** `backend/core/auth/token_store.py:31-34,39-46`
**Evidence:** At 100,000 entries, `self._blacklist.clear()` wipes everything. The `ttl` parameter is accepted but ignored.
**Impact:** Every previously revoked token becomes valid again. Every used refresh token can be replayed.

### H-4: `/model/info` Exposes Internals Without Authentication
**Files:** `backend/routers/health.py:130-157`
**Evidence:** No auth guard. Exposes model version, registry, prediction stats, training metadata.
**Impact:** Attackers can fingerprint the ML model version, identify serialization format vulnerabilities, and gather business intelligence.

### H-5: `/auth/token` Creates Anonymous Sessions With No Identity Proof
**Files:** `backend/routers/auth.py:69`
**Evidence:** Subject is `f"user_{int(time.time())}"` — deterministic from timestamp.
**Impact:** No accountability. Audit logs cannot be tied to real users.

### H-6: Circular Import via timeline.py → orchestrator.py
**Files:** `backend/domains/investigation/timeline.py:3`, `services/orchestrator.py`
**Evidence:** `timeline.py` imports `analyze_text` from `services/orchestrator`, which imports from pipeline steps, which import from domains including investigation. Creates a circular dependency chain.
**Impact:** Under different import orders, can cause `ImportError` or partially-loaded modules.

### H-7: Config Wildcard Imports Destroy Traceability
**Files:** `backend/config/settings.py:4-15`
**Evidence:** 15 `from core.config.* import *` statements. No `__all__` is exhaustive. Impossible to determine where any name originates.
**Impact:** Cannot safely rename, move, or deprecate any config constant. Static analysis cannot resolve names.

### H-8: Config Executes I/O at Module Import Time
**Files:** `backend/config/settings.py` (entire file)
**Evidence:** Reads env vars, calls `os.path.isdir()`, mutates module-level names at import time.
**Impact:** Tests cannot set environment variables before settings import. Unpredictable behavior with reload.

### H-9: Drift Detector Uses Fake "Accuracy" Metric
**Files:** `backend/core/drift_detector.py:169-172`
**Evidence:** `1.0 - (scam_count / total)` is used as "accuracy," assuming 95% of predictions should be "scam."
**Impact:** Drift alerts fire spuriously when class distribution shifts. Actual accuracy degradation goes undetected.

### H-10: No Model File Integrity Verification (Pickle RCE Risk)
**Files:** `backend/predict.py:40-41`
**Evidence:** `joblib.load()` with no checksum, signature, or schema validation. Pickle-based deserialization can execute arbitrary code.
**Impact:** Corrupted model files serve garbage silently. Malicious model files achieve RCE at prediction time.

### H-11: Prediction Ring Buffer Drops Old Data (1000 Record Limit)
**Files:** `backend/core/prediction_logger.py:37`
**Evidence:** `deque(maxlen=1000)`. All monitoring depends on this buffer.
**Impact:** Drift detection operates on a rolling window of unknown size. After 1000 predictions, older data is silently lost.

### H-12: Test Count Has Three Conflicting Numbers
**Files:** `README.md:108`, `backend/VALIDATION_REPORT.md:81`, `backend/tests/validation/test_release_report.py:88-92`
**Evidence:** README claims 244, VALIDATION_REPORT claims 820/831 (both), pytest collects 920.
**Impact:** No one knows the true test baseline. False confidence in quality metrics.

### H-13: Shared Global State Leaks Between Tests
**Files:** `backend/tests/conftest.py:14-16`, `backend/tests/unit/test_ml_ops.py:189-192`
**Evidence:** Rate limiter singleton, model registry singleton, prediction logger singleton all persist across tests. Tests manually mutate `_logger_instance = None`.
**Impact:** Non-deterministic test failures depending on execution order. Flaky CI.

### H-14: Critical Test Suites Not Run in CI
**Files:** `.github/workflows/ci.yml:44-73`
**Evidence:** `tests/e2e/`, `tests/validation/`, `tests/architecture/` are NOT invoked in CI.
**Impact:** Model regression, architecture violations, and end-to-end failures go undetected.

### H-15: K8s Frontend Missing Security Context
**Files:** `k8s/frontend-deployment.yaml:20-40`
**Evidence:** No `securityContext` block. Runs as root with full capabilities.
**Impact:** Compromised frontend container has full root access to the host node.

### H-16: Docker Compose Uses `latest` Image Tag
**Files:** `docker-compose.yml:14,55`
**Evidence:** `image: scamshield-backend:latest`, `image: scamshield-frontend:latest`
**Impact:** Non-deterministic deployments. Rollback is ambiguous.

### H-17: Grafana Default Admin Credentials
**Files:** `backend/monitoring/docker-compose.monitoring.yml:45-46`
**Evidence:** `GF_SECURITY_ADMIN_PASSWORD=${GRAFANA_ADMIN_PASSWORD:-admin}`
**Impact:** Default `admin/admin` credentials will be exploited within minutes on any exposed instance.

### H-18: Backup Scripts Documented But Do Not Exist
**Files:** `docs/BACKUP.md:26,106-112`
**Evidence:** References `backup-models.sh`, `backup-datasets.sh`, `backup-full.sh`. None exist in `scripts/`.
**Impact:** Automated backup cannot run. RTO/RPO targets are unachievable.

### H-19: Sentry Telemetry Silently Broken
**Files:** `frontend/src/services/monitoring.ts:16-24`
**Evidence:** Custom raw-HTTP Sentry path sends malformed envelope format. `.catch(() => {})` swallows all errors.
**Impact:** Complete loss of client-side error telemetry. Operations blind to API failures.

### H-20: No Error Boundary in Analysis Result Page
**Files:** `frontend/src/pages/analysis-result.tsx:39-194`
**Evidence:** Accesses 40+ properties on `current.result` without null guard. No per-component ErrorBoundary.
**Impact:** Malformed analysis result crashes entire main content area. User sees blank error page.

### H-21: No CSRF Protection on API Calls
**Files:** `frontend/src/services/api.ts:7-13`
**Evidence:** No `xsrfCookieName`, `xsrfHeaderName`, or any CSRF configuration.
**Impact:** If user session cookies exist, malicious sites can make API calls.

### H-22: Gold Dataset Is Dangerously Small for Per-Category Evaluation
**Files:** `datasets/gold/GOLD_EVALUATION_REPORT.md:34-65`
**Evidence:** 308 total samples across 29 categories (~10.6 avg). Categories with 3-6 samples report F1=1.0000.
**Impact:** Per-category metrics are statistically meaningless. Real-world performance on underrepresented categories is unknown.

### H-23: No Dataset License Anywhere
**Files:** `LICENSE`, `datasets/v2/README.md`
**Evidence:** MIT license covers "Software" only. Datasets include CERT-In, RBI, NPCI, UCI data. No usage terms documented.
**Impact:** Legal risk. Enterprise adoption requires clear data provenance and licensing.

---

## MEDIUM ISSUES (31)

### M-1: `_reload_model()` Bypasses Thread Lock
**Files:** `backend/predict.py:51-55`
**Impact:** Race condition during rollback if requests are in flight.

### M-2: Distant Pipeline Steps Mutate Report Dict
**Files:** `backend/pipeline/steps/knowledge_step.py:20-26`, `connector_step.py:15-17`, `fusion_step.py:17-19`
**Impact:** Side-effect-driven architecture. Step ordering changes break report output.

### M-3: KnowledgeStep Has Inverted Dependency on ReportStep
**Files:** `backend/pipeline/steps/knowledge_step.py:10`
**Impact:** Knowledge enrichment cannot run without report generation.

### M-4: Pipeline Errors Silently Swallowed for Non-Fatal Steps
**Files:** `backend/pipeline/pipeline.py:46-56`
**Impact:** Incomplete analysis without API consumer notification.

### M-5: Mutable Default Arguments in PipelineData
**Files:** `backend/pipeline/shared.py:34-53`
**Impact:** Data corruption across pipeline steps sharing mutable references.

### M-6: Rate Limiter Hits Health Probes (Pod Restart Risk)
**Files:** `backend/main.py:203-207`
**Impact:** K8s health probes could be rate-limited under load, causing pod restart escalation.

### M-7: Module-Level State in predict.py Causes Test Pollution
**Files:** `backend/predict.py:12-15`
**Impact:** Flaky tests depending on import order.

### M-8: Refresh Token Rotation Has Race Window in Multi-Worker Deployment
**Files:** `backend/core/auth/token_store.py:39-46`, `routers/auth.py:149-163`
**Impact:** Legitimate users can have refresh tokens falsely rejected as "reused."

### M-9: JWT Missing `aud` and `iss` Verification
**Files:** `backend/core/auth/jwt.py:77-90`
**Impact:** Tokens from other services sharing the same secret would be accepted.

### M-10: K8s ConfigMap Still Missing Production Variables
**Files:** `k8s/configmap.yaml`
**Impact:** Environment config may not match what the application expects.

### M-11: No PodDisruptionBudget in K8s
**Files:** `k8s/` (missing file)
**Impact:** Node maintenance can take down both backend pods simultaneously.

### M-12: No NetworkPolicy in K8s
**Files:** `k8s/` (missing file)
**Impact:** Compromised frontend pod can directly access backend API.

### M-13: No `imagePullSecrets` for Private Registry
**Files:** `k8s/*-deployment.yaml`
**Impact:** Pod creation fails with ImagePullBackOff if images are in private GHCR.

### M-14: HighMemoryUsage Alert Expression Is Broken
**Files:** `backend/monitoring/prometheus/alert-rules.yml:31-32`
**Impact:** Alert fires at wrong threshold. Operators lose trust in monitoring.

### M-15: All Security Scans Use `continue-on-error: true`
**Files:** All `.github/workflows/*.yml`
**Impact:** Gitleaks, pip-audit, npm audit, Trivy are decorative. Secrets and vulnerabilities ship to production.

### M-16: Lint Failures Ignored in CI
**Files:** `.github/workflows/ci.yml:100,104`
**Impact:** Ruff and mypy failures never block CI. Code quality degrades unchecked.

### M-17: No Staging Environment
**Files:** All workflows (missing)
**Impact:** Production-breaking changes discovered only after deployment.

### M-18: No Image Signing or SBOM
**Files:** `.github/workflows/release.yml:87-103`
**Impact:** No provenance verification. Tampered images deploy undetected.

### M-19: Non-English Scripts Stripped by Text Cleaning
**Files:** `backend/utils/text.py:60-66`
**Impact:** Model is effectively blind to non-English scripts. 19-21% error rate on non-English.

### M-20: Entire Training Set Is Synthetic
**Files:** `datasets/v2/annotated/v2_expand_gamma.py` (and delta scripts)
**Impact:** Model has never been evaluated on organic, real-world adversarial traffic.

### M-21: Cross-Validation Contaminated by Test Set Inclusion
**Files:** `backend/train.py:133,156-168`
**Impact:** CV metrics not representative of train-only performance.

### M-22: Prediction Log Files Grow Indefinitely
**Files:** `backend/core/prediction_logger.py:39-53`
**Impact:** No rotation, no retention policy, no GDPR-compliant purging.

### M-23: No Lockstep Validation Between Model and Vectorizer
**Files:** `backend/predict.py:40-41,51-55`
**Impact:** Mismatched artifacts serve garbage predictions silently.

### M-24: `sharp` Unused Dependency (30-50MB)
**Files:** `frontend/package.json:42`
**Impact:** Adds unnecessary install time and image size.

### M-25: CSP Missing `base-uri` Directive
**Files:** `frontend/nginx.conf:23`
**Impact:** `<base>` tag injection can hijack relative URLs.

### M-26: Investigation Page Is Dead-End Placeholder
**Files:** `frontend/src/pages/investigation.tsx`
**Impact:** Navigation link labeled "Deep Dive" leads to useless screen.

### M-27: API Endpoint Documentation Wrong
**Files:** `docs/API_REFERENCE.md:9-14` vs actual routes
**Impact:** SDKs and integrations fail against documented paths.

### M-28: Version Frozen at 1.0.0 Despite Major Post-Release Work
**Files:** `VERSION`, `CHANGELOG.md`
**Impact:** Cannot distinguish original release from heavily improved current state.

### M-29: Dataset Versioning Table Is Fiction
**Files:** `datasets/v2/README.md:109-114`
**Impact:** Documented as "In progress, 0/5000 samples" when gamma has 2531.

### M-30: Non-English Samples Critically Underrepresented
**Files:** `datasets/gold/GOLD_EVALUATION_REPORT.md:71-74`
**Impact:** F1 drops from 0.9826 (en) to 0.8824 (te-en). Undermines India-specific mission.

### M-31: No Runbooks for Monitoring Stack
**Files:** `OPERATIONS.md`
**Impact:** When alert fires, operators have no guidance.

---

## LOW ISSUES (22)

L-1: `domains/reporting/models.py` is empty (dead code)
L-2: `connectors/utils.py` had unused `import re` (fixed but note)
L-3: `domains/reasoning/refinement.py` uses `logging.getLogger()` instead of structured logger
L-4: `ocr.py` opens image twice, leaking file descriptor on first open
L-5: `PipelineRunner` creates shallow copy of config dict
L-6: `SlidingWindowRateLimitMiddleware` has no path exemption pattern
L-7: Global exception handler does not log traceback (`exc_info=True` missing)
L-8: Audit logs not redacted for PII
L-9: Swagger docs blocked at nginx but accessible on backend port directly
L-10: `frontend/nginx.conf` hardcodes Render.com deployment URL in CSP
L-11: `frontend/nginx.conf` has no TLS in Docker Compose mode
L-12: `docker-compose.yml` has no user-defined network
L-13: `frontend/Dockerfile` uses `--ignore-scripts` which may skip postinstall hooks
L-14: `frontend/Dockerfile` no npm cache cleanup in builder
L-15: No `HEALTHCHECK` instruction in backend Dockerfile
L-16: `framer-motion` installed but unused (~30KB dead bundle weight)
L-17: Toast exit animations missing (UX roughness)
L-18: Inline `animationDelay` bypasses `prefers-reduced-motion`
L-19: Dependabot Docker updates on monthly schedule (should be weekly)
L-20: CHANGELOG has only one entry (v1.0.0)
L-21: `scam_dataset.csv` orphaned (original v1 data, no longer referenced)
L-22: `SECURITY.md` lacks PGP key for encrypted disclosure

---

## Answers to Specific Questions

### 1. Is ScamShield technically production-ready?

**No.** The system has fundamental architectural flaws (duplicate exception hierarchies, circular imports, unauthenticated token issuance), critical security vulnerabilities (IDOR on token revocation, rate-limiter fail-open), broken Kubernetes configurations (pods cannot start), and an ML pipeline with corrupted benchmark metrics. Deploying the current codebase to production risks:

- Complete service unavailability in Kubernetes (missing tmpfs + PVC)
- Unauthenticated access to all authenticated endpoints (no-auth token issuance)
- Silent data corruption (probability inversion bug, prediction logger ring buffer)
- Regulatory non-compliance (no dataset licensing, no log retention policy)

### 2. Would you approve deployment?

**No.** I would require the following minimum fixes before approving any production deployment:

1. Fix Kubernetes backend deployment (add tmpfs volume + PVC for models)
2. Add authentication to `/auth/token` endpoint
3. Add authorization to `/auth/revoke` endpoint
4. Fix Redis rate-limiter fail-open behavior
5. Fix benchmark probability inversion bug and re-evaluate all metrics
6. Enforce non-default secrets at startup
7. Pin Docker image tags to specific versions (not `latest`)

### 3. What are the remaining blockers?

| Blocker | Severity | Resolution |
|---------|----------|------------|
| K8s pods can't start (no tmpfs, no PVC) | CRITICAL | Add volumes to deployment manifest |
| Anyone can mint valid JWTs | CRITICAL | Add authentication to token endpoint |
| Anyone can revoke any token (IDOR) | CRITICAL | Add authorization to revoke endpoint |
| Redis failure disables all rate limiting | CRITICAL | Fix fail-open to fail-closed or fallback |
| Benchmark metrics are corrupted | CRITICAL | Fix probability inversion, re-run benchmarks |
| Placeholder secrets in production .env | HIGH | Add startup validation against known defaults |
| No deployment pipeline | HIGH | Implement CD in release workflow |
| No staging environment | HIGH | Add staging deployment to CI |
| No TypeScript strict mode | HIGH | Enable strict mode, fix all resulting errors |

### 4. What technical debt still exists?

| Debt | Estimated Effort | Areas Affected |
|------|-----------------|----------------|
| Duplicate exception hierarchies | 2-3 days | All domain and router code |
| Circular import in investigation timeline | 1 day | Domain dependency graph |
| Config wildcard imports | 2 days | Entire config layer |
| 663-line refinement.py needs decomposition | 1 day | Reasoning domain |
| 445-line evidence.py needs decomposition | 1 day | Assessment domain |
| Probability inversion in benchmark | 0.5 day | All published ML metrics |
| Threshold leakage in benchmark | 0.5 day | All published ML metrics |
| No maintainer documentation | 2 days | Full project |
| Empty `__init__.py` files (fixed but not all) | 1 day | Various packages |
| Missing type hints across 12+ files | 2 days | Various modules |
| Sentry telemetry broken | 0.5 day | Frontend monitoring |
| No CSRF protection | 1 day | Frontend API layer |
| Gold dataset too small | 1-2 weeks | Data collection + annotation |
| No real-world data validation | 1-3 months | Production data collection |

### 5. What would you refuse to deploy without fixing?

1. **Kubernetes deployment** — current manifests produce CrashLoopBackOff pods (CRITICAL)
2. **Authentication system** — token issuance with zero identity proof (CRITICAL)
3. **Token revocation** — no authorization check allows global DoS (CRITICAL)
4. **Rate limiting** — Redis failure disables all protection (CRITICAL)
5. **Secrets management** — placeholder values in .env.production (HIGH)
6. **CI/CD pipeline** — no deployment automation (HIGH)
7. **ML benchmark metrics** — corrupted by probability inversion (CRITICAL)
8. **Frontend TypeScript** — no strict mode, null reference crashes guaranteed (CRITICAL)
9. **Monitoring stack** — broken alert expressions, default Grafana credentials (HIGH)
10. **Backup/DR** — documented scripts don't exist (HIGH)

### 6. Overall engineering score out of 100

| Dimension | Score | Assessment |
|-----------|-------|------------|
| Architecture | 35/100 | Good pipeline abstraction but critical circular import and exception hierarchy defects |
| Security | 25/100 | Multiple CRITICAL auth bypasses; no CSRF; broken telemetry |
| AI/ML | 30/100 | Corrupted benchmarks, no data integrity, no real-world validation |
| Testing | 25/100 | Conflicting counts, superficial assertions, shared state, missing CI suites |
| DevOps | 30/100 | K8s non-functional, no CD pipeline, broken monitoring expressions |
| Frontend | 40/100 | No strict TypeScript, broken telemetry, no error boundaries |
| Documentation | 20/100 | Dangerously outdated metrics, wrong API paths, fictional dataset tables |
| Datasets | 35/100 | No licensing, tiny gold set, non-English underrepresented |

**Overall: 34/100**

---

## Key Recommendations (Ordered by Impact)

### Immediate (prerequisite to any production deployment)
1. Add tmpfs volume + PVC to `k8s/backend-deployment.yaml` — K8s is currently broken
2. Add authentication requirement to `POST /auth/token` — currently issues tokens to anyone
3. Add authorization requirement to `POST /auth/revoke` — currently revokes tokens for anyone
4. Fix `RedisSlidingWindowRateLimiter` fail-open — when Redis is down, rate limiting is defeated
5. Fix benchmark probability inversion in `models.py:181-190` — all published metrics are wrong
6. Add startup validation that rejects known placeholder secrets
7. Pin Docker images to specific version tags, not `latest`

### Short-term (within 2 weeks)
8. Merge duplicate exception hierarchies (`core/exceptions.py` and `domains/shared/exceptions.py`)
9. Enable TypeScript `strict: true` in both tsconfig files and fix all resulting errors
10. Implement CD in the release workflow (deploy to a staging environment)
11. Fix all monitoring alert expressions (HighMemoryUsage, ModelNotLoaded)
12. Fix Grafana default credentials and bind monitoring ports to localhost
13. Implement the three missing backup scripts documented in BACKUP.md
14. Remove `continue-on-error: true` from security scanning steps

### Medium-term (within 1 month)
15. Add `PodDisruptionBudget`, `NetworkPolicy`, `ServiceAccount`, `PersistentVolumeClaim` to K8s
16. Implement Terraform or Helm for infrastructure-as-code
17. Fix the cross-validation pipeline (CV on training split only, not full dataset)
18. Add lockstep validation between model.joblib and vectorizer.joblib
19. Add real-world non-English data to training and gold evaluation
20. Replace in-memory token blacklist overflow (`clear()`) with LRU eviction or Redis TTL
21. Add response shape validation in frontend `useAnalysisNavigation` before navigating to result page

### Long-term (within 3 months)
22. Collect real-world adversarial data and re-evaluate model
23. Implement shadow scoring for model comparison on live traffic
24. Add Helm charts for parameterized K8s deployments
25. Implement automated retraining pipeline triggered by drift detection
26. Add property-based testing for the rule engine
27. Add penetration testing for JWT alg=none, token injection, and timing attacks

---

*This review was conducted through static code analysis. No dynamic testing, penetration testing, or production traffic observation was performed. Issues identified through dynamic testing may exist beyond those listed here.*
