# ScamShield Master Audit — Report 07: Roadmap

**Date:** 2026-07-26

All recommendations are based on findings from this audit. No invented features.

---

## Immediate (Weeks 1-2)

### R1. Add Authentication Layer
**Why:** API is fully open. Cannot deploy to any public endpoint without auth.  
**What:** Add API key authentication (simple `X-API-Key` header check) with middleware.  
**Expected impact:** Critical security fix — enables safe deployment.  
**Effort:** 2-3 days  
**Priority:** **CRITICAL**

### R2. Fix CORS Configuration
**Why:** `allow_origins=["*"]` is a security risk.  
**What:** Change to explicit allowed origins or remove CORS for same-origin deployments.  
**Expected impact:** Security fix.  
**Effort:** 30 minutes  
**Priority:** **CRITICAL**

### R3. Remove `continue-on-error` from Security Scans
**Why:** Pip-audit and npm audit results are ignored.  
**What:** Remove `continue-on-error: true` from CI workflows. Fix any actual vulns.  
**Expected impact:** CI will catch dependency vulnerabilities.  
**Effort:** 1-2 hours  
**Priority:** **HIGH**

### R4. Fix Assessment Accuracy Metric
**Why:** `assessment_accuracy: 0.0` means the metric or dataset is broken — misleading evaluation.  
**What:** Investigate why assessment_band never matches expected values. Fix metric calculation or correct dataset.  
**Expected impact:** Accurate evaluation results.  
**Effort:** 1 day  
**Priority:** **HIGH**

---

## Short Term (Weeks 3-6)

### R5. Eliminate Useless Service Wrappers
**Why:** `ml_service.py` (7 lines), `rules_service.py` (27 lines), `ocr_service.py` (11 lines) add zero value. They are pass-throughs that add maintenance overhead.  
**What:** Import directly from source modules. Delete wrapper files.  
**Expected impact:** Reduced file count, less confusion.  
**Effort:** 1 hour  
**Priority:** **MEDIUM**

### R6. Eliminate Duplicate Constants
**Why:** `rules.py` redefines lists of banks, payment apps, government refs, urgency words, money phrases — all duplicating `core/constants.py`.  
**What:** Import from constants instead of redefining.  
**Expected impact:** Single source of truth for all patterns.  
**Effort:** 1 day  
**Priority:** **HIGH**

### R7. Decompose Largest Service Files
**Why:** `knowledge_service.py` (826 lines), `refinement_service.py` (701 lines), `investigation_service.py` (696 lines), `reasoning_service.py` (646 lines) are too large.  
**What:** Split each into 2-3 smaller files by concern.  
**Expected impact:** Improved maintainability, testability.  
**Effort:** 4-5 days  
**Priority:** **HIGH**

### R8. Add E2E Tests for Critical Flows
**Why:** No E2E tests exist. User-facing flows (analyze text → view result, investigate → view timeline) are untested.  
**What:** Add Playwright tests for 3-5 critical user flows.  
**Expected impact:** Confidence in frontend functionality.  
**Effort:** 3-4 days  
**Priority:** **HIGH**

### R9. Add OCR Tests
**Why:** OCR path has zero tests. Image analysis is a key feature.  
**What:** Add mock-based and integration tests for OCR service.  
**Expected impact:** OCR reliability.  
**Effort:** 1-2 days  
**Priority:** **HIGH**

### R10. Add Training Dataset to Repository
**Why:** `train.py` exists but no training dataset is committed. Model training is not reproducible.  
**What:** Add the training CSV or a representative subset. Document training procedure.  
**Expected impact:** Reproducible ML pipeline.  
**Effort:** 1 day  
**Priority:** **HIGH**

---

## Medium Term (Weeks 7-12)

### R11. Improve ML Accuracy
**Why:** 72.8% accuracy and 61.7% FPR are too low for production.  
**What:** Hyperparameter tuning (grid search), try ensemble methods (Random Forest, XGBoost), add class weighting for imbalance. Consider DistilBERT for better semantic understanding.  
**Expected impact:** Target 85%+ accuracy, <20% FPR.  
**Effort:** 2-3 weeks  
**Priority:** **HIGH**

### R12. Add Monitoring Stack
**Why:** No monitoring, no alerting. Production blind spot.  
**What:** Add Prometheus + Grafana with prebuilt dashboards. Add alert rules for error rate, latency, throughput.  
**Expected impact:** Operational visibility.  
**Effort:** 3-5 days  
**Priority:** **MEDIUM**

### R13. Add Secrets Management
**Why:** API keys in `.env` file is a security risk.  
**What:** Migrate to Docker secrets or HashiCorp Vault for production. Keep `.env` for development.  
**Expected impact:** Secure key storage.  
**Effort:** 1-2 days  
**Priority:** **HIGH**

### R14. Add Response Caching
**Why:** Repeated analysis of the same text runs the full pipeline each time.  
**What:** Add in-memory cache (LRU, TTL-based) keyed by text hash. Skip pipeline if cached.  
**Expected impact:** 10-50x speedup for repeated queries.  
**Effort:** 1 day  
**Priority:** **MEDIUM**

### R15. Add Async Processing for Investigations
**Why:** Multi-artefact investigation runs the pipeline n times synchronously. Blocks worker for n × 200ms.  
**What:** Use FastAPI BackgroundTasks or Celery for investigations. Return investigation_id immediately, poll for results.  
**Expected impact:** Non-blocking investigations.  
**Effort:** 3-5 days  
**Priority:** **MEDIUM**

### R16. Add Pagination to Investigation Response
**Why:** Relationship graph limited to 30 nodes/40 edges. Timeline limited to 50 events. Large investigations will hit these limits silently.  
**What:** Add pagination parameters and return total counts.  
**Expected impact:** Scalability for large investigations.  
**Effort:** 1 day  
**Priority:** **MEDIUM**

---

## Long Term (Weeks 13+)

### R17. Build Consumer-Facing Interface
**Why:** Product has no consumer touchpoint. Users cannot easily use it.  
**What:** Build one of: WhatsApp bot, Telegram bot, Android SMS forwarder, or browser extension.  
**Expected impact:** Real users can use the product.  
**Effort:** 4-8 weeks  
**Priority:** **MEDIUM**

### R18. Add Active Learning Loop
**Why:** Model is static — no improvement from production data.  
**What:** Add "was this analysis correct?" feedback mechanism. Store feedback for periodic retraining.  
**Expected impact:** Continuous improvement of accuracy.  
**Effort:** 2-3 weeks  
**Priority:** **LOW**

### R19. Add Internationalization
**Why:** India-specific only. Cannot expand globally.  
**What:** Extract India-specific patterns to config, add locale system.  
**Expected impact:** Global market potential.  
**Effort:** 4-6 weeks  
**Priority:** **LOW**

### R20. Add Audit Trail
**Why:** No record of who analyzed what. No compliance readiness.  
**What:** Log all analysis requests with user ID (once auth exists), timestamp, text hash, result.  
**Expected impact:** Compliance, forensics.  
**Effort:** 1 week  
**Priority:** **LOW**

---

## Roadmap Summary

| Phase | Timeline | Items | Effort |
|-------|----------|-------|--------|
| Immediate | Weeks 1-2 | R1-R4 (4 items) | 5-7 days |
| Short Term | Weeks 3-6 | R5-R10 (6 items) | 10-13 days |
| Medium Term | Weeks 7-12 | R11-R16 (6 items) | 15-25 days |
| Long Term | Weeks 13+ | R17-R20 (4 items) | 10-16 weeks |
