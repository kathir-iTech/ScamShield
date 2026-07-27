# Test Coverage Report

**Date**: 2026-07-26  
**Total tests**: 244/244 passing  

---

## 1. Backend Tests

### 1.1 Unit Tests (`backend/tests/unit/`)

| File | What it tests | Completeness |
|---|---|---|
| `test_rules.py` | Rule engine functions (18 patterns) | High — covers scam/safe cases |
| `test_intelligence.py` | Entity extraction (URLs, phones, emails, UPI, etc.) | High — covers all extractors |
| `test_assessment.py` | Risk assessment scoring | Medium |
| `test_evidence.py` | Evidence collection & ranking | Medium |
| `test_explanation.py` | Explanation generation | Medium |
| `test_report.py` | Report generation logic | Medium |
| `test_connectors.py` | Connector framework | High — covers base, manager, registry |
| `test_google_safe_browsing.py` | Google SB connector | Medium — mock-based |
| `test_threat_intelligence_fusion.py` | Fusion engine | High — agreement, conflict, ranking |
| `test_hardening.py` | Production hardening checks | Medium |

### 1.2 Integration Tests (`backend/tests/integration/`)

| File | What it tests | Completeness |
|---|---|---|
| `test_pipeline.py` | Full 12-stage pipeline | Medium — covers main flow |

### 1.3 Benchmark Tests (`backend/tests/benchmark.py`)

Performance benchmark with regression assertions (100/500/1000 request batches). Includes P95 latency thresholds and memory regression checks.

### 1.4 Test Fixtures (`conftest.py`)
- 15 scam text samples
- 15 safe text samples
- `sample_analysis()` dict fixture for service-level tests

---

## 2. Frontend Tests (`frontend/src/test/`)

| Directory | Description | Completeness |
|---|---|---|
| `components/` | UI component tests | Low — minimal coverage |
| `hooks/` | Custom hook tests | Low |
| `services/` | API service tests | Low |
| `context/` | Context provider tests | Low |
| `design/` | Design system tests | Low |
| `utils/` | Utility tests | Low |
| `setup.ts` | Test setup configuration | Present |

---

## 3. Coverage Analysis

### 3.1 Backend Coverage Estimate
- **Rules engine**: ~90% — well tested with scam/safe fixtures
- **Intelligence entity extraction**: ~85% — each extractor has test cases
- **Connector framework**: ~80% — base, manager, registry, caching tested
- **Threat intelligence fusion**: ~90% — agreement, conflict, ranking all tested
- **Assessment service**: ~60% — core logic tested, edge cases light
- **Evidence service**: ~60% — basic flow tested
- **Reasoning service**: ~50% — complex reasoning chains not fully covered
- **OCR service**: ~0% — no dedicated tests
- **Investigation service**: ~30% — campaign detection tested, multi-artefact flow light
- **Report service**: ~50% — report generation tested, edge cases light
- **Knowledge service**: ~30% — basic query tested

### 3.2 Frontend Coverage Estimate
- Overall: ~20-30% of components have tests
- Critical pages (landing, analysis-result): minimal or no tests
- Hooks: use-scamshield tests present, use-toast minimal
- API service: mock-based tests present

---

## 4. Gaps

| Gap | Severity | Impact |
|---|---|---|
| No OCR service tests | High | OCR path untested |
| Investigation service under-tested | High | Critical feature with low coverage |
| Reasoning service complex paths not tested | Medium | Edge cases in classification chains |
| Frontend page tests missing | High | No E2E or integration page tests |
| No E2E tests (Playwright/Cypress) | High | No user flow validation |
| No load/stress tests | Medium | Performance regression only at unit level |
| No property-based/fuzz tests | Low | |
| No snapshot tests | Low | |

---

## 5. Recommendations

1. **Add OCR service tests** — at minimum mock-based
2. **Expand investigation tests** — multi-artefact scenarios, campaign edge cases
3. **Add reasoning service tests** — evidence chain validation
4. **Add frontend page tests** — Vitest + React Testing Library for critical pages
5. **Add E2E tests** — Playwright for critical user flows
6. **Add coverage reporting** — pytest-cov + c8/v8 for frontend
7. **Set coverage thresholds** — 70% minimum in CI
