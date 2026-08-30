# Engineering Decisions

## Architecture

### Layered Service Architecture
The analysis pipeline follows a strict sequential architecture:

1. **ML Prediction** (predict.py/ml_service.py) — TF-IDF + Logistic Regression classifier
2. **Rule Engine** (rules.py/rules_service.py) — Heuristic keyword/pattern detection
3. **Explanation Service** — Category classification, indicator detection, severity calculation
4. **Threat Intelligence** — Entity extraction (18 types: URLs, phones, emails, UPI IDs, etc.)
5. **Evidence Engine** — Evidence correlation, conflict detection, confidence/risk breakdown
6. **Assessment Engine** — Unified 0-100 risk score from 6 weighted components
7. **Report Generator** — 15-section investigation report with timeline and guidance

### Design Principles
- **No external dependencies**: All analysis is offline, no APIs or LLMs
- **No database**: Stateless, single-request analysis
- **No authentication**: Internal API, not exposed to public
- **No frontend**: API-only service

## Configuration & Constants

### Centralized Constants (`core/constants.py`)
All string literals, risk levels, assessment bands, category definitions, entity types, stopwords, indicator patterns, and correlation rules are centralized in one file.

### Configurable Settings (`config/settings.py`)
Thresholds, weights, limits, file types, and other tunable values are in settings.py, loaded via environment variables where applicable.

### Rationale
- Single source of truth prevents duplication across services
- Easy to audit and update values
- Environment variables for deployment-specific tuning

## Exception Hierarchy (`core/exceptions.py`)
```
ScamShieldError (base)
├── ConfigurationError → ModelLoadError
├── ValidationError → EmptyTextError, TextTooLongError, InvalidImageError, PathTraversalError
├── ImageExtractionError → OCRProcessingError
├── ServiceError → MLServiceError, RulesServiceError, IntelServiceError, EvidenceServiceError, AssessmentError, ReportError
└── FileAccessError → DatasetNotFoundError
```

### Why structured exceptions?
- Clear error taxonomy helps API consumers handle specific failures
- Internal errors map to generic 500 responses (no stack trace leakage)
- Validation errors return 400 with user-friendly messages

## Middleware

### Request ID Middleware
- Generates UUID4 per request for log correlation
- Logs method, path, status code, and processing time
- Sets X-Request-ID response header

### Why not trace logging?
- Request IDs provide enough correlation without distributed tracing overhead
- The service is single-process and stateless

## Service Hardening

### Performance
- Regex patterns compiled once at module load (not per-call)
- Frozen sets for O(1) membership tests
- Deduplication using sets before list construction

### Security
- Input text length limited to 10,000 characters
- File upload limited to 10 MB, validated by content type
- Image analysis uses temporary files (deleted after processing)
- No eval/exec, no shell injection vectors
- Path traversal prevention via suffix extraction

### Type Safety
- All public functions have complete type hints
- Pydantic models for API request/response validation
- Return types documented

## Testing Strategy

### Unit Tests
- Each service tested in isolation with controlled inputs
- Edge cases: empty strings, missing fields, boundary values
- All 18 entity extractors tested individually

### Integration Tests
- Full pipeline test with 15 scam + 15 safe examples
- Response model validation against Pydantic schemas
- Field completeness verification

### Determinism
- All tests produce deterministic results
- No random seeds, no external state
- Test data is static and versioned

## Backward Compatibility

### Preserved Behavior
- ML model, training, prediction logic unchanged
- Rule engine keywords and scoring identical
- OCR extraction unchanged
- All response field names and types preserved
- Assessment scores and report format identical
- Evidence correlation and conflict detection unchanged

### Changed
- Hardcoded strings moved to constants.py
- Regex compilation moved to module level
- Settings extracted to config/settings.py
- Validation and error handling added
- Logging enhanced with request IDs
- Test suite replaced validation scripts

## Phase 3 Architecture Refinements

### Orchestrator Pipeline Formalization
- `AnalysisResult` dataclass replaces the untyped `Dict[str, object]` — all 34 response fields are typed and documented
- `_run_pipeline()` provides stage-based error isolation; each step has a named try/except block
- Pipeline steps are self-contained functions (`_step_ml`, `_step_rules`, etc.) for readability and testability

### Evidence Engine Refactoring
- `IndicatorHandler` registry (`_INDICATOR_RISK_RULES`, `_ENTITY_RISK_RULES`, `_CORRELATION_RISK_RULES`) replaces 32 repeated if-elif chains in `build_risk_breakdown`
- `EvidenceCollector` class replaces the `add_evidence` closure for cleaner evidence accumulation
- `_DECISION_LEVEL_CUTOFFS` and `_PRIORITY_CUTOFFS` tuple lists replace if-elif ladders with data-driven lookups
- Inline import (`from config.settings import ...`) moved from function body to module level

### Entity Extraction Optimization
- `extract_shortened_urls` and `extract_suspicious_tlds` no longer called in `analyze()` — `extract_urls` already reclassifies these URL types
- `risk_counts` removed (populated but never consumed)
- Entity risk assignment unified — assigned once in `analyze()` via `ENTITY_RISK_MAP` lookup

### Category Detection Optimization
- Category keyword regexes pre-compiled at module load in `_CATEGORY_REGEXES` instead of per-call compilation (~180 regexes per `detect_category()` invocation)

### String Constant Hygiene
- All `"high"`, `"low"`, `"SAFE"`, `"Unknown Scam"`, `"VERY LOW"` string literals in business logic replaced with `core/constants` references (`RISK_HIGH`, `RISK_LOW`, `DECISION_SAFE`, `UNKNOWN_CATEGORY`, `SEVERITY_VERY_LOW`)
- `rules.py` no longer duplicates `SUSPICIOUS_TLD`, `KNOWN_SHORTENERS`, `SCAM_KEYWORDS` — imports from `core/constants` instead

### Test Improvements
- `tests/conftest.py` provides shared fixtures (`scam_texts`, `safe_texts`, `sample_analysis`) used by integration tests
- 18 repetitive entity extractor tests replaced by 2 parameterized tests (`test_entity_extractors`, `test_extract_url_specialized`)
- Decision level tests (5→10) and severity tests expanded via `@pytest.mark.parametrize`
- Ad-hoc `_test_*.py` scripts removed (logic covered by pytest suite)
- 106 tests pass (expanded from 95 through parameterization)
