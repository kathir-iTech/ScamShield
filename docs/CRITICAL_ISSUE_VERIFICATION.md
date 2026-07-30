# Critical Issue Verification Report

> Generated: 2026-07-31
> Context: Independent engineering review of ScamShield codebase
> Verdicts: Confirmed / Partially Valid / False Positive

---

## C-1: Benchmark Probability Inversion Bug

**Status:** CONFIRMED

**Location:** `benchmarks/v2/scripts/models.py:181–191`

**Evidence:**
```python
# Line 181-190 (broken)
probs = self.model.predict_proba(vec)[0]       # e.g. [0.95, 0.05]
pred = 1 if probs[1] >= self.threshold else 0  # pred=0 (safe)
confidence = float(probs[1]) if pred == 1 else float(probs[0])  # confidence=0.95
return {
    "prediction": "scam" if pred == 1 else "safe",
    "confidence": confidence,
    "probabilities": {"safe": float(1 - confidence), "scam": float(confidence)},
    # For safe pred: {"safe": 0.05, "scam": 0.95}  ← INVERTED
}
```

When `pred == 0` (safe): `confidence = probs[0]` (safe probability). The dict then computes `{"safe": 1 - confidence, "scam": confidence}` = `{"safe": 1 - probs[0], "scam": probs[0]}` = `{"safe": probs[1], "scam": probs[0]}`. The safe and scam probabilities are **swapped**.

Compare with `_predict_embedding` at line 201 which does it correctly:
```python
"probabilities": {"safe": float(probs[0]), "scam": float(probs[1])},
```

**Impact:** The `evaluate()` function in `run_gamma_benchmark.py:41` reads `probabilities["scam"]` for ROC-AUC calculation. For every correctly classified safe sample, it gets the safe-probability instead of the scam-probability, producing near-1.0 values. This **corrupts the AUC metric** and the threshold optimization at line 100.

---

## C-2: Threshold Optimization on Test Set

**Status:** PARTIALLY VALID

**Location:** `benchmarks/v2/scripts/run_gamma_benchmark.py:97–106`

**Evidence:**
```python
# Line 94 (metrics computed BEFORE optimization — uses default threshold 0.5)
overall = evaluate(wrapper, X_test, y_test)

# Lines 97-106 (threshold tuned on test set — data leakage)
opt_probas = []
for t in X_test:
    r = wrapper.predict(t)
    opt_probas.append(r.get("probabilities", {}).get("scam", 0.5))
best_f1, best_thresh = 0.0, 0.5
for th in np.linspace(0.1, 0.9, 81):
    p = [1 if v >= th else 0 for v in opt_probas]
    f = f1_score(y_test, p, zero_division=0)  # y_test used for tuning
    if f > best_f1:
        best_f1, best_thresh = f, th

# Line 108-112: stored alongside metrics
all_results[mtype] = {"overall": overall, ..., "optimal_threshold": float(best_thresh)}
```

**Valid part:** The `optimal_threshold` is derived from the test set, which is data leakage. This value should not be treated as independently validated. When the review says "optimal threshold is computed using test-set labels", this is **TRUE**.

**Invalid part:** The review claims "all reported benchmark F1 scores are inflated because threshold was optimized on test set." This is **FALSE**. The `overall` metrics (accuracy, precision, recall, F1, AUC) were computed at line 94 **before** the threshold optimization block. These metrics use the default threshold (0.5) and are **not** recalculated with the optimized threshold.

**Additional note:** The `opt_probas` computation at line 100 is also affected by C-1 (probability inversion), compounding the corruption of the threshold optimization.

---

## C-3: Duplicate Exception Hierarchies

**Status:** PARTIALLY VALID

**Location:** `backend/core/exceptions.py` (22 classes) vs `backend/domains/shared/exceptions.py` (24 classes)

**Evidence:**
- `core/exceptions.py`: defines `ScamShieldError` → `AuthenticationError`, `ConfigurationError`, `ValidationError`, `ServiceError`, etc. (22 classes)
- `domains/shared/exceptions.py`: defines independently a separate `ScamShieldError` → same classes + `DomainError` + `NotFoundError` (24 classes)
- These are **two separate Python class hierarchies** — a `core.exceptions.ValidationError` is NOT a `domains.shared.exceptions.ValidationError`
- All 8 import sites in application code use `from core.exceptions import ...`
- Only `domains/shared/public.py` imports from `domains.shared.exceptions`
- `domains/shared/__init__.py` is empty, so the re-exports from `public.py` are not propagated

**Valid part:** The duplication exists and is a maintenance burden. If future code imports from `domains.shared.exceptions` while the service layer raises `core.exceptions`, catch blocks will silently miss. This is a ticking time bomb.

**Invalid part:** No runtime bugs are currently caused by this duplication. The second hierarchy is effectively dead code.

---

## C-4: Token Issuance Has Zero Authentication

**Status:** CONFIRMED

**Location:** `backend/routers/auth.py:61–80`

**Evidence:**
```python
@router.post("/auth/token", response_model=TokenResponse)
def get_token(request: Request, response: Response) -> TokenResponse:
    if not settings.AUTH_ENABLED:
        raise HTTPException(status_code=404, detail="Authentication is not enabled")
    _check_rate_limit(request, _auth_limiter)   # Only rate limiting — no auth
    _add_rate_limit_headers(response, _auth_limiter, request)
    subject = f"user_{int(time.time())}"         # Trivially guessed subject
    access = create_access_token(subject=subject, role=UserRole.AUTHENTICATED)
    ...
```

No API key, password, client certificate, or any proof of identity is required. Anyone can call `curl -X POST http://localhost:8000/auth/token` and receive a valid JWT with `UserRole.AUTHENTICATED`. The only protection is rate limiting (which itself can be bypassed — see C-6).

---

## C-5: Token Revocation Has No Authorization Check

**Status:** CONFIRMED

**Location:** `backend/routers/auth.py:200–214`

**Evidence:**
```python
@router.post("/auth/revoke")
def revoke_token(request: Request, response: Response, token_data: Dict[str, str]) -> Dict:
    _check_rate_limit(request, _auth_limiter)   # Only rate limiting — no auth
    _add_rate_limit_headers(response, _auth_limiter, request)
    token = token_data.get("token", "")
    if not token:
        raise HTTPException(status_code=400, detail="token is required")
    try:
        payload = decode_token(token)
        blacklist_token(payload.jti)             # Revokes any valid token
        ...
```

No `require_auth`, `require_admin`, or any authorization decorator. No user ownership check. Anyone who knows a token's JWT can revoke it by submitting it to this endpoint. This enables trivial denial-of-service against legitimate users.

---

## C-6: Rate Limiter Fails Open When Redis Is Down

**Status:** CONFIRMED

**Location:** `backend/core/abuse.py:106–153`

**Evidence:**
```python
def is_blocked(self, client_ip, limiter_name="default"):
    try:
        r = self._connect()
        key = self._key(client_ip, limiter_name)
        return bool(r.exists(key))
    except Exception:
        return False          # Never block when Redis is down

def record_request(self, client_ip, now, limiter_name="default"):
    try:
        ...
    except Exception:
        return True           # Always allow when Redis is down

def remaining(self, client_ip, limiter_name="default"):
    try:
        ...
    except Exception:
        return self.max_requests  # Always full capacity when Redis is down
```

All three methods catch base `Exception` and return the most permissive value. The factory `create_rate_limiter()` at line 156-171 tests Redis at startup and falls back to in-memory. However, if Redis goes down **after** startup, every endpoint protected by a Redis rate limiter silently operates without rate limiting.

---

## C-7: K8s Backend Pods Will CrashLoopBackOff

**Status:** CONFIRMED

**Location:** `k8s/backend-deployment.yaml:50–67`

**Evidence:**
- Line 50: `readOnlyRootFilesystem: true`
- Lines 51-60: Security context with non-root user, no privilege escalation
- **No `volumeMounts` or `volumes` defined anywhere** in the file
- Missing writable `/tmp` (emptyDir) — Python's `tempfile`, `uvicorn`, `pip`, and many libraries need `/tmp`
- Missing model data volume (PVC or emptyDir) — `model.joblib` and `vectorizer.joblib` are excluded by `.dockerignore` (`*.joblib`), so they aren't baked into the image

**Impact:** Pods will fail at startup when:
1. Python tempfile operations fail (no writable `/tmp`)
2. Model loading fails (no model files available)
3. Uvicorn/code that needs to write temp files crashes

---

## C-8: No Deployment Stage in CI/CD

**Status:** PARTIALLY VALID

**Location:** `.github/workflows/release.yml`, `.github/workflows/ci.yml`

**Evidence:**
- `ci.yml`: Tests, lint, quality gate only — no deployment
- `release.yml`: Builds Docker images, pushes to GHCR, creates GitHub Release — no deployment step
- **No workflow has a Deploy job** targeting any environment (staging, production)

**Valid part:** The review correctly identifies that there is zero deployment automation in the CI/CD pipeline.

**Invalid part:** Classifying this as "critical" is subjective. The project provides Docker Compose and K8s manifests for manual deployment. Many projects operate without automated CD. This is a process/tooling gap, not a software defect. Additionally, deployment can be handled externally (ArgoCD, GitOps, manual kubectl apply).

---

## C-9: README Documentation Is Dangerously Outdated

**Status:** CONFIRMED

**Location:** `README.md`, `docs/API_REFERENCE.md`

**Evidence:**
1. `README.md:4` — Badge: "244 tests passing" — actual count is **820+** tests passing (all 8 phases complete)
2. `README.md:5` — Badge: "83.3% accuracy" — actual model accuracy is **95.13%** (Test Acc=0.9513)
3. `docs/API_REFERENCE.md:9` — Documents `/api/v1/analyze/text` — actual route is `/analyze/text` (no prefix)
4. `docs/API_REFERENCE.md:40` — Documents `/api/v1/analyze/image` — actual route is `/analyze/image`
5. `docs/API_REFERENCE.md:48` — Documents `/api/v1/health` — actual route is `/health`

All badge numbers and API paths are out of date and misleading.

---

## C-10: No TypeScript Strict Mode

**Status:** CONFIRMED

**Location:** `frontend/tsconfig.app.json`

**Evidence:**
```json
{
  "compilerOptions": {
    "target": "es2023",
    "skipLibCheck": true,
    "noUnusedLocals": true,
    "noUnusedParameters": true,
    "noFallthroughCasesInSwitch": true
    // NO "strict": true
    // strictNullChecks: off → null references compile
    // noImplicitAny: off → implicit any types compile
    // strictFunctionTypes: off → function subtyping unsound
    // strictBindCallApply: off → bind/call/apply unsound
    // noImplicitThis: off → this typed as any
    // alwaysStrict: off → no "use strict"
  }
}
```

Without `"strict": true`, all individual strict flags default to `false`. This allows null pointer exceptions, implicit `any` types, and unsound function type checks to pass compilation silently. The `tsconfig.node.json` has the same gap.

---

## Summary

| ID | Issue | Verdict | Fix Required? |
|----|-------|---------|---------------|
| C-1 | Probability inversion | **CONFIRMED** | Yes |
| C-2 | Threshold optimization on test set | **PARTIALLY VALID** | Yes (fix leakage) |
| C-3 | Duplicate exception hierarchies | **PARTIALLY VALID** | Yes (deduplicate) |
| C-4 | Token issuance has zero auth | **CONFIRMED** | Yes |
| C-5 | Token revocation has no auth check | **CONFIRMED** | Yes |
| C-6 | Rate limiter fails open | **CONFIRMED** | Yes |
| C-7 | K8s missing volumes | **CONFIRMED** | Yes |
| C-8 | No deployment in CI/CD | **PARTIALLY VALID** | Yes (add deploy) |
| C-9 | README/API docs outdated | **CONFIRMED** | Yes |
| C-10 | No TypeScript strict mode | **CONFIRMED** | Yes |
