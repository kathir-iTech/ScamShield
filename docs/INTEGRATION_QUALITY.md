# Integration Quality Report

**Date**: 2026-07-26

---

## 1. Data Flow Analysis

### 1.1 Primary Flow: Text Analysis

```
User Input → Router (analyze.py) → Orchestrator (12 stages) → Response
```

**Stage breakdown** (`orchestrator.py`):
1. ML Classification → `prediction`, `confidence`
2. Rules Engine → `rule_label`, `rule_score`, `reasons`, `detected_indicators`
3. Intelligence/Entity Extraction → `entities`, `entity_summary`, `entity_risk`
4. Explanation Service → `explanation`
5. Evidence Service → `supporting_evidence`, `conflicting_evidence`
6. Reasoning Service → `reasoning_family`, `reasoning_primary_evidence`, `reasoning_dominant_evidence_chain`
7. Assessment Service → `assessment_score`, `assessment_band`, `assessment_confidence`
8. Refinement Service → `review_required`, `manual_review_reason`
9. Report Service → `investigation_report`
10. Business Logic → `business_reason`, `technical_reason`, `recommended_action`
11. Risk Calculation → `risk_breakdown`, `risk_level`, `decision_score`
12. Threat Intelligence → (through connector framework)

### 1.2 Investigation Flow

```
Multi-artefact input → Investigation Service
  → For each artefact: Orchestrator.analyze_text()
  → Entity merging (cross-artefact dedup)
  → Timeline construction
  → Campaign detection
  → Relationship graph building
  → Global risk computation
  → Report generation
```

---

## 2. Service Integration Points

| Source Service | Consumed By | Integration Method | Risk |
|---|---|---|---|
| `ml_service.py` | Orchestrator | Direct function call | Low |
| `rules.py` | `rules_service.py` → Orchestrator | Direct import | Low |
| `intelligence_service.py` | Orchestrator | `analyze()` function | Low |
| `explanation_service.py` | Orchestrator | Direct function call | Low |
| `evidence_service.py` | Orchestrator | Direct function call | Low |
| `reasoning_service.py` | Orchestrator | Direct function call | Low |
| `assessment_service.py` | Orchestrator | Direct function call | Low |
| `refinement_service.py` | Orchestrator | Direct function call | Low |
| `knowledge_service.py` | Orchestrator | Direct function call | Low |
| `report_service.py` | Orchestrator | `generate_report()` | Low |
| `connector/manager.py` | `threat_intelligence_service.py` | Fusion engine | Medium |
| `ocr.py` | `ocr_service.py` → Image analysis | System call/import | Medium |
| `predict.py` | `ml_service.py` | Direct import | Low |

---

## 3. Error Handling

| Service | Error Handling Approach | Coverage |
|---|---|---|
| Orchestrator | Stage-level try/except | Partial — some stages may raise unhandled |
| Intelligence Service | Per-extractor exception catching | Good |
| Connectors | Custom exception hierarchy (`exceptions.py`) | Good |
| Report Service | No explicit error handling | **Weak** |
| Investigation Service | Input validation + empty handling | Good |
| Frontend API | Axios interceptor catches 4xx/5xx | Good |

### 3.1 Error Propagation

- Backend errors → HTTP 422 (Pydantic validation) or 500 (unhandled)
- Frontend shows toast notification via `use-toast` hook
- No structured error response schema for all error types
- No retry logic for transient connector failures (beyond HTTPX defaults)

---

## 4. Data Consistency

| Concern | Status |
|---|---|
| Entity types consistent across services | **No** — strings like "phone", "phone_indian", "phone_international" used inconsistently |
| Risk levels consistent | Yes — HIGH/MEDIUM/LOW used throughout |
| Prediction labels consistent | Yes — "scam"/"safe" used throughout |
| Category names consistent | Uses core constants |
| Result dictionary shape | **Fragile** — services add keys to a shared dict; key name collisions are possible |

---

## 5. Integration Test Coverage

| Integration Point | Test File | Coverage |
|---|---|---|
| Full 12-stage pipeline | `tests/integration/test_pipeline.py` | Basic flow tested |
| API → Router → Orchestrator | Via integration tests | Partial |
| Connector → Fusion Engine | `tests/unit/test_threat_intelligence_fusion.py` | Good |
| OCR → Pipeline | **No tests** | **None** |
| Frontend → Backend API | `frontend/src/test/services/` | Mock-based, partial |
| Investigation → Orchestrator | Partial in investigation tests | Light |

---

## 6. Strengths

- **Sequential pipeline is well-defined**: Clear order of operations with each stage enriching a shared result dict
- **Connector framework is extensible**: Adding new threat intel sources requires minimal integration work
- **Investigation module is self-contained**: Dataclass-based result with clear transformation steps
- **Frontend API layer is clean**: Single `api.ts` with interceptors, typed service functions

---

## 7. Weaknesses

- **No event-driven integration**: All flows are synchronous request-response. Long investigations block the HTTP worker
- **No service mesh or circuit breaker**: Connector failures can cascade
- **Result dict is untyped**: Services communicate through a plain dictionary (`Dict[str, Any]`) — no schema contract between stages
- **No integration contract testing**: No Pact or contract tests between frontend and backend
- **No health check for internal services**: OCR (Tesseract) dependency is not validated at startup
- **Cross-service entity type inconsistency**: String-based entity types risk misalignment

---

## 8. Recommendations

1. **Add typed result contracts** — use dataclasses or TypedDict for pipeline stage outputs
2. **Add circuit breaker** to connector calls (e.g., `pybreaker`)
3. **Add startup validation** for all external dependencies (Tesseract, model files)
4. **Add async task queue** for investigations (Celery/Redis or FastAPI BackgroundTasks)
5. **Add integration contract tests** between frontend types and backend schemas
6. **Standardize entity type enums** across all services
7. **Add health check endpoints** per external dependency
8. **Add structured logging with correlation IDs** for request tracing across services
