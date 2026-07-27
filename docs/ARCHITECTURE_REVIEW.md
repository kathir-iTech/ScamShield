# Architecture Review Report

**Date**: 2026-07-26

---

## 1. Overall Architecture

ScamShield uses a layered service-oriented architecture:

```
Client (React SPA)
    |
Nginx Reverse Proxy
    |
FastAPI Backend
    |-- Routers (analyze.py, health.py)
    |-- Orchestrator (12-stage pipeline)
    |   |-- ML Service
    |   |-- Rules Engine
    |   |-- Intelligence Service
    |   |-- Explanation Service
    |   |-- Evidence Service
    |   |-- Reasoning Service
    |   |-- Assessment Service
    |   |-- Refinement Service
    |   |-- Report Service
    |   |-- Knowledge Service
    |   |-- OCR Service
    |   |-- Investigation Service
    |-- Connector Framework
    |   |-- Google Safe Browsing
    |   |-- Mock Connector
    |-- Core (constants, exceptions, metrics, diagnostics)
    |-- Config (settings.py)
    |-- Schemas (Pydantic)
```

---

## 2. Strengths

### 2.1 Service Separation
Each stage of the analysis pipeline is a separate service module with a single responsibility. Services communicate through the orchestrator, avoiding circular dependencies.

### 2.2 Pipeline Architecture
The 12-stage orchestration in `orchestrator.py` is well-structured: sequential stages with clear data flow. Each stage enriches a shared result dictionary.

### 2.3 Connector Framework
The connector pattern (`base.py` abstract class → `google_safe_browsing.py` / `mock.py` → `manager.py` / `registry.py`) follows a sound plugin architecture. Adding new threat intel sources requires implementing the abstract connector interface and registering it.

### 2.4 Investigation Module
`investigation_service.py` (696 lines) is a standalone, well-factored sub-system with clear data classes (dataclasses), validation, entity merging, timeline building, campaign detection, and relationship graph construction.

### 2.5 Frontend Routing
React Router setup with lazy-loaded pages, proper Suspense boundaries, and typed routes.

---

## 3. Concerns

### 3.1 Monolithic Constants File
`backend/core/constants.py` at 18,000+ lines contains all scam taxonomy, keyword lists, regex patterns, indicator maps, and configuration data. This creates:
- Poor discoverability
- Risk of merge conflicts
- Slow IDE performance
- Violation of single-responsibility principle

**Recommendation**: Split into domain-specific modules (e.g., `constants/scam_types.py`, `constants/patterns/`, `constants/indicators.py`).

### 3.2 Tight Coupling to Constants
Multiple services import directly from `core.constants` rather than through an abstraction layer. Changes to constant values or structure ripple across the entire codebase.

### 3.3 Orchestrator as God Object
`orchestrator.py` imports and coordinates 12+ services. While the pipeline is linear, the orchestrator has deep knowledge of all service internals. Adding a new pipeline stage requires modifying the orchestrator.

### 3.4 No DI/IoC Container
Services create their own dependencies or import them at module level. No dependency injection framework is used, making unit testing harder and preventing runtime reconfiguration.

### 3.5 Frontend-Backend Coupling
Frontend types (`@/types`) mirror backend Pydantic schemas but are maintained separately. No OpenAPI code generation is used, creating a manual synchronization burden.

### 3.6 No Message Queue
All analysis is synchronous HTTP request-response. Long-running investigation requests (multi-artefact) could benefit from async task queues (Celery/Redis).

---

## 4. Scaling Assessment

| Dimension | Current | Target |
|---|---|---|
| Request throughput | ~10 req/s (single process) | 100+ req/s (with workers) |
| ML inference | In-process, blocking | Separate inference service |
| Investigation | Synchronous, single node | Async task queue |
| Connector calls | Sequential per request | Parallel with circuit breaker |
| Database | None (stateless) | Optional (for persistence) |
| Frontend bundle | 363KB gzip 117KB | < 200KB target |

---

## 5. Architectural Recommendations

1. **Split constants.py** into domain modules
2. **Add OpenAPI code generation** for frontend types
3. **Introduce async task queue** for investigations
4. **Extract ML inference** to separate service
5. **Add circuit breaker** to connector framework
6. **Consider event-driven architecture** for real-time analysis
7. **Abstract config access** behind a settings facade
