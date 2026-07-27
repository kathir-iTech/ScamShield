# REPORT 3: CODEBASE HEALTH

## 1. Code Quality Overview

### Backend (Python)

| Metric | Value | Assessment |
|---|---|---|
| Total Python files | 120+ | Large codebase |
| Average function length | 15-30 lines | Good |
| Average class length | 80-120 lines | Good |
| Typing coverage | ~90% | **Excellent** — extensive use of type hints, Protocols, TypeVar |
| Docstring coverage | ~40% | **Partial** — ML pipeline and core well-documented; domains and tests lacking |
| Import complexity | Low | Clean separation, no circular imports found |
| Code duplication | Low | Most logic abstracted into base classes |
| Error handling coverage | ~30% | **Poor** — many `except Exception` broad catches, few specific error types |

### Frontend (TypeScript/React)

| Metric | Value | Assessment |
|---|---|---|
| Total TSX/TS files | 90+ | Large frontend |
| Component re-render hygiene | Good | Proper use of React.memo, useMemo, useCallback |
| TypeScript strictness | Strict mode | **Excellent** — `strict`, `noUncheckedIndexedAccess`, `strictNullChecks` all enabled |
| Type coverage | ~95% | **Excellent** — no `any` usage, comprehensive interfaces |
| Hook complexity | Low-Medium | Custom hooks are focused, well-typed |
| CSS approach | Tailwind + CSS vars | Consistent design token usage |
| Error boundaries | Present (basic) | `ErrorBoundary` at root but no per-feature boundaries |

## 2. Technical Debt

### Critical (fix immediately)
1. **`domain_manager.py` line 1** — Contains a raw SQL-style comment suggesting direct database access: `-- BFSM001: check if subject is repeated`. This is dead code or a copy-paste artifact.
2. **JWT `role` is client-asserted** — The `/auth/token` endpoint creates tokens with any role string. No server-side role validation.

### High (fix within 1-2 sprints)
3. **No persistence** — All investigation data, audit logs, rate limit state are in-memory. Restart loses everything.
4. **Test coverage is low** — 94 assertions across 36 tests covering ~10% of codebase. Parser tests dominate. Rule engine, pipeline, connectors, domains have nearly zero coverage.
5. **Dead code paths** — `core/calibration/`, `core/abuse/`, evaluation scripts, quality dashboard — infrastructure exists but is not wired in.
6. **Hardcoded paths** — `model.joblib` and `vectorizer.joblib` are hardcoded in `predict.py`. Should be configurable.
7. **Empty pattern/watchlist files** — Many JSON files in `knowledge/patterns/` contain empty arrays `[]`.

### Medium (fix next sprint)
8. **Broad exception handling** — `entity_extractor.py:1-50`, `predict.py`, `scoring.py` use `except Exception: return default` — swallows real errors.
9. **Frontend API error handling** — The `scamshield.ts` service has minimal error classification. Network vs. server vs. validation errors are not distinguished in the UI.
10. **Missing loading states** — Several pages (system-status, deployment-health, investigation) lack proper loading skeleton states.
11. **CSS file has dead code** — `frontend/src/index.css` contains references to multiple scrollbar themes and deprecated animation classes.
12. **Empty dependency directories** — `evaluation/dataset/` has 6 empty subdirectories (banking, crypto, delivery, government, loan, lottery) that should be removed or populated.

### Low (nice-to-have)
13. **README has some broken internal links** — Section references assume specific file paths that may not match actual structure.
14. **Docker image layers not optimized** — Single-stage build for both backend and frontend; could be multi-stage.
15. **No pre-commit hooks configured** — No linting/formatting enforcement.
16. **API version not in URL path** — All endpoints at root `/` — future breaking changes will be hard.

## 3. Code Smells

| Location | Smell | Severity |
|---|---|---|
| `pipeline_steps.py` — each step class has many responsibilities | Large class | Medium |
| `scoring.py` — single function >100 lines with nested conditionals | Long function | High |
| `evidence.py:score_evidence` — complex scoring with multiple magic numbers | Magic numbers | Medium |
| `investigation.py:detect_campaign` — 80+ lines of nested logic | Long function | Medium |
| `entity_extractor.py` — 20+ extraction methods in one class | God class | High |
| `scamshield.ts` — single file with 6 API functions + interceptors | Mixed concerns | Low |
| `App.tsx` — route definitions + providers + error boundary | Mixed concerns | Low |
| `predict.py` — many global/file-level mutable state | Module state | Medium |
| `rules.py` — 18 adjacent if/elif blocks | Sequential coupling | Medium |

## 4. Test Quality Assessment

| Test File | Type | Assertions | Quality |
|---|---|---|---|
| `test_parser.py` | Unit | ~40 | Good — thorough edge cases |
| `test_analyze.py` | Integration | ~15 | OK — covers happy path, some edge cases |
| `test_rules.py` | Unit | ~12 | OK — covers each rule pattern |
| `test_api/test_auth.py` | Integration | ~8 | Basic — no token revocation tests |
| `test_security/test_routing.py` | Unit | ~8 | Good — thorough path normalization tests |
| `test_security/test_path_traversal.py` | Unit | ~6 | OK — covers basic traversal patterns |
| `test_architecture.py` | Structure | ~5 | Good — verifies import constraints |
| Frontend `*.test.tsx` (20 files) | Unit | ~30+ | Mixed — mostly presence tests, not behavior |

**Key gaps:**
- No pipeline step tests (12 steps, 0 coverage)
- No domain service tests (assessment, knowledge, reasoning, investigation, intelligence, reporting — all untested)
- No connector tests (Google Safe Browsing, mock, manager — untested)
- No ML model tests beyond basic load
- No frontend feature tests (graph, timeline, report, investigation — untested)
- No integration tests that exercise full pipeline
- No performance/load tests

## 5. Dependency Health

### Backend (Python 3.12)

| Dependency | Version | Risk |
|---|---|---|
| fastapi | 0.115.* | Low |
| uvicorn | 0.32.* | Low |
| scikit-learn | 1.5.* | Low |
| pydantic | 2.9.* | Low |
| pyjwt | 2.9.* | Low (check for CVEs) |
| Pillow | 11.* | Low |
| pytesseract | 0.3.* | Low |
| httpx | 0.28.* | Low |
| lxml | 5.3.* | Low |
| aiofiles | 24.* | Low |
| python-multipart | 0.0.* | Low |

**Notes:** No pinned hashes, no lockfile for pip. `requirements.txt` has unpinned sub-dependencies. No dependency scanning in CI.

### Frontend (NPM)

| Dependency | Version | Risk |
|---|---|---|
| react | 19.0.* | Low |
| typescript | 6.0.* | Low (very new, less ecosystem support) |
| vite | 8.0.* | Low (very new) |
| tailwindcss | 4.0.* | Low |
| @tanstack/react-query | 5.62.* | Low |
| framer-motion | 11.* | Low |
| zustand | 5.* | Low (new major version) |
| zod | 3.* | Low |
| axios | 1.* | Low |
| recharts | 2.* | Low |

**Notes:** TypeScript 6, Vite 8, Tailwind v4, Zustand 5 are very recent major versions. Ecosystem compatibility (plugins, community resources) may be limited.
