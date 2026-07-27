# ScamShield Master Audit — Report 04: Technical Debt

**Date:** 2026-07-26

All debt identified from repository inspection only. Ranked by severity.

---

## Critical Debt

### C1. No Authentication Layer
**File:** `backend/main.py:52`  
**Evidence:** `allow_origins=["*"]` and no auth middleware. Any deployed instance is fully open.  
**Risk:** Unauthenticated access to analysis API  
**Effort:** 2-3 days to add API key or JWT auth  
**Impact:** Security  

### C2. `.env` Secrets Management
**File:** `docker-compose.yml:20`, `config/settings.py:125`  
**Evidence:** `SAFE_BROWSING_API_KEY` loaded from `os.getenv(".env")`. No vault/secret store.  
**Risk:** API key exposure in CI logs, docker inspect  
**Effort:** 1 day to integrate Docker secrets or vault  
**Impact:** Security  

### C3. CORS Wildcard
**File:** `backend/main.py:52`  
**Evidence:** `allow_origins=["*"]`  
**Risk:** Any website can make requests to the API  
**Effort:** 30 minutes to restrict to known origins  
**Impact:** Security  

### C4. Security Scans in CI Use `continue-on-error: true`
**Files:** `.github/workflows/backend.yml:100`, `.github/workflows/frontend.yml:126`  
**Evidence:** `continue-on-error: true` on `pip-audit` and `npm audit`  
**Risk:** Vulnerable dependencies will not fail CI  
**Effort:** 5 minutes to remove flag  
**Impact:** Security/Quality  

---

## High Debt

### H1. `ml_service.py` is a 7-Line No-Op Wrapper
**File:** `backend/services/ml_service.py` (7 lines)  
**Evidence:** Contains only `from predict import predict` and re-exports. Zero added value.  
**Risk:** Maintenance overhead, misleading abstraction  
**Effort:** 10 minutes to eliminate and import directly  
**Impact:** Maintainability  

### H2. `rules_service.py` is a 27-Line Pass-Through
**File:** `backend/services/rules_service.py` (27 lines)  
**Evidence:** Every function is `return _rules.function_name(text)`. Does nothing except re-export.  
**Risk:** Same as H1  
**Effort:** 10 minutes  
**Impact:** Maintainability  

### H3. `ocr_service.py` is a 6-Line Pass-Through
**File:** `backend/services/ocr_service.py` (11 lines)  
**Evidence:** Same pattern — just wraps `ocr.py` functions.  
**Risk:** Same as H1  
**Effort:** 5 minutes  
**Impact:** Maintainability  

### H4. `knowledge_service.py` — 826 Lines with 300+ Line Function
**File:** `backend/services/knowledge_service.py` (826 lines)  
**Evidence:** `enrich_analysis()` is a single function exceeding 300 lines. Hard to test, reason about, or modify.  
**Risk:** Maintenance difficulty, bug-prone  
**Effort:** 2 days to split into smaller functions  
**Impact:** Maintainability  

### H5. `evidence_service.py` — Monolithic `build_evidence()`
**File:** `backend/services/evidence_service.py` (445 lines)  
**Evidence:** `build_evidence()` handles evidence collection, correlation, conflict detection, confidence breakdown, risk breakdown, priority assignment — all in one function.  
**Risk:** Hard to test individual behaviors  
**Effort:** 1 day to decompose  
**Impact:** Maintainability  

### H6. Duplicate Data Between `rules.py` and `core/constants.py`
**File:** `backend/rules.py:36,57,85,105,115,131`  
**Evidence:** `rules.py` redefines `urgency_words`, `money_phrases`, `suspicious_keywords_in_url`, `india_banks`, `payment_apps`, `govt_refs` — all of which exist in `core/constants.py`.  
**Risk:** Constants drift — updating one file but not the other causes bugs  
**Effort:** 1 day to eliminate duplicates and import from constants  
**Impact:** Correctness  

### H7. `refinement_service.py` — 701 Lines with Complex Lambda Rules
**File:** `backend/services/refinement_service.py` (701 lines)  
**Evidence:** 13 refinement rules defined as lambdas in a list. Logic is hard to follow, debug, and test. Rules use string matching on assessment bands.  
**Risk:** Difficulty validating correctness, high cognitive load  
**Effort:** 2 days to refactor rule definitions  
**Impact:** Maintainability  

### H8. `reasoning_service.py` — 646 Lines with Graph Construction
**File:** `backend/services/reasoning_service.py` (646 lines)  
**Evidence:** Evidence graph construction, family classification, and chain extraction all in one file.  
**Risk:** Complex interactions between subsystems  
**Effort:** 2 days to split into graph builder + family classifier  
**Impact:** Maintainability  

### H9. `asdict()` Called Multiple Times Per Request
**File:** `backend/services/orchestrator.py:152,172,184,198,214,224,239,243,257,265`  
**Evidence:** `asdict(result)` is called in every `_step_*` function to convert the AnalysisResult dataclass to a dict. This serializes all 90+ fields each time, even fields not needed by that stage.  
**Risk:** Unnecessary CPU overhead per request  
**Effort:** 1 day to pass only required fields as parameters  
**Impact:** Performance  

### H10. `Unused ocr_metadata Parameter
**File:** `backend/services/intelligence_service.py:324`  
**Evidence:** `analyze(text, ocr_metadata=None)` — the parameter exists but is never passed or used.  
**Risk:** Dead parameter, misleading API  
**Effort:** 5 minutes  
**Impact:** Maintainability  

---

## Medium Debt

### M1. Empty Directories
- `frontend/src/features/dashboard/` — empty
- `frontend/src/assets/` — empty
- `frontend/src/styles/` — empty

### M2. `assessment_accuracy: 0.0` in Evaluation
**File:** `evaluation/reports/validation_v1/metrics.json:11`  
**Evidence:** Assessment band accuracy is 0.0 across 511 samples. Either the metric is calculated incorrectly, or the expected assessment_band values in the dataset don't match any actual outputs. Either way, this metric is broken.  
**Risk:** Misleading evaluation results  
**Effort:** 1 day to fix metric or validate dataset  

### M3. `frontend/src/test/setup.ts` is 1 Line
**File:** `frontend/src/test/setup.ts`  
**Evidence:** Contains only `import '@testing-library/jest-dom'` — no global mocks, no MSW setup. Tests that make API calls will hit real endpoints.  
**Risk:** Flaky tests, network-dependent  

### M4. Service Wrapper Pattern Inconsistency
Some services have wrappers (ml_service, rules_service, ocr_service — all useless), others are imported directly (intelligence_service, evidence_service). No consistent pattern.

### M5. Dashboard Feature Module is Empty
**File:** `frontend/src/features/dashboard/`  
**Evidence:** Empty directory. Dashboard page likely imports from elsewhere or has no feature-specific code.

### M6. Toast Counter is Module-Level
**File:** `frontend/src/hooks/use-toast.ts:9`  
**Evidence:** `let toastId = 0` at module level — not ref-based. Works but violates React patterns.

---

## Low Debt

### L1. Mixed Entity Type Strings
Entity types are raw strings (`"url"`, `"phone"`, `"upi_id"`) throughout `intelligence_service.py`, `evidence_service.py`, `investigation_service.py`. No enum. Risk of typos.

### L2. `List[Dict]` Return Types
Multiple service functions return `List[Dict]` instead of typed dataclasses. Reduces IDE support and makes refactoring harder.

### L3. 17 UI Components but No Storybook
No visual testing or component explorer.

### L4. No Pre-commit Hooks
No `.pre-commit-config.yaml` — formatting and linting not enforced locally.

### L5. No Conventional Commits
Commit history not reviewed, but no commitlint or standard enforced.

---

## Debt Summary

| Severity | Count | Estimated Effort |
|----------|-------|-----------------|
| Critical | 4 | 3-4 days |
| High | 10 | 10-15 days |
| Medium | 6 | 3-5 days |
| Low | 5 | 1-2 days |
| **Total** | **25** | **~17-26 days** |
