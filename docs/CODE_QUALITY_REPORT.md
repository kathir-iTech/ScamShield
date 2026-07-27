# Code Quality Report

**Date**: 2026-07-26

---

## 1. Overall Assessment

The codebase is well-structured with consistent patterns, clear naming, and good separation of concerns. Python backend follows PEP 8 conventions. TypeScript frontend uses strict mode. There are areas of tech debt concentrated in specific files.

---

## 2. Python Backend Quality

### 2.1 Strengths
- Type hints used consistently across all services
- Dataclasses for structured data (investigation_service.py, connectors/models.py)
- Consistent import ordering
- Docstrings on public functions
- Pydantic schemas for API validation
- Service layer separation with single responsibility

### 2.2 Issues Found

**Critical:**
- `backend/core/constants.py` (18,000+ lines): Single-file megaconstant. Contains data that should be in JSON/YAML config files or split across domain modules.

**Major:**
- `backend/rules.py` (~360 lines): Flat file with 18 pattern-matching functions. No abstraction layer — every function is a standalone `check_*` function returning `Tuple[int, List[str]]`. Adding a new rule means adding a new function and manually integrating it.
- `backend/predict.py`: ML prediction logic mixed with model loading. No clear separation between training/prediction.
- Magic strings: Entity types like `"url"`, `"domain"`, `"phone"` are used as raw strings throughout intelligence_service.py rather than enum constants.
- Error handling: Some functions catch broad `Exception`/`ValueError` without logging.

**Minor:**
- Inconsistent use of `List[Dict]` vs typed `List[Entity]` — many functions return untyped dicts
- Several service files exceed 300 lines (investigation_service.py: 696, report_service.py: 434, intelligence_service.py: 382)
- `_` prefix naming convention for private functions is used inconsistently
- No pre-commit hooks configured for linting/formatting

### 2.3 Duplication
- Entity extraction logic in `intelligence_service.py` has repeated patterns (seen-set dedup pattern appears ~20 times)

---

## 3. TypeScript/React Frontend Quality

### 3.1 Strengths
- TypeScript strict mode enabled (0 errors)
- `@tanstack/react-query` for server state management
- Lazy-loaded routes with Suspense boundaries
- Feature-based directory organization
- Consistent component naming

### 3.2 Issues Found

**Major:**
- **No state management library**: Only React Query for server state. Client state (toast, navigation) is managed with raw `useState`. No Zustand/Redux/Jotai for complex client state.
- **Incomplete test coverage**: `frontend/src/test/` has directories for components, hooks, services, etc., but actual test files are minimal relative to the component count.
- **No error boundaries in feature components**: Only one `error-boundary.tsx` exists — not applied per-page.

**Minor:**
- `use-toast.ts` uses a module-level `let toastId = 0` counter (not React-ref based)
- CSS/styling approach is unclear (imports suggest Tailwind or custom CSS)
- No storybook or visual testing
- No bundle analysis configuration

---

## 4. Tech Debt Quantification

| Category | Severity | Effort to Fix |
|---|---|---|
| Split constants.py | Critical | 2-3 days |
| Abstract rules engine | Major | 1-2 days |
| Add enum types for entities | Major | 1 day |
| Add pre-commit/linting | Major | 2 hours |
| Improve test coverage (frontend) | Major | 2-3 days |
| Improve test coverage (backend) | Medium | 1-2 days |
| Add OpenAPI codegen | Medium | 1 day |
| Replace magic strings | Medium | 1 day |
| Add error boundary per route | Minor | 2 hours |
| Standardize dedup pattern | Minor | 1 hour |
| Add state management | Minor | 1 day |

**Estimated total tech debt: ~2-3 weeks** for a single developer.

---

## 5. Recommendations

1. **Split constants.py** — highest ROI refactor
2. **Add pre-commit** with ruff/black/isort/mypy
3. **Enforce typing** — replace `List[Dict]` with typed models
4. **Add mypy strict** to CI pipeline
5. **Extract rules engine** into pluggable pattern
6. **Add gerkin tests or integration contract tests**
7. **Introduce OpenAPI-to-TypeScript code generation**
