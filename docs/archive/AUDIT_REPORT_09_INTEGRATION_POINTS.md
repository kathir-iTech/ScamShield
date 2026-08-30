# REPORT 9: INTEGRATION POINTS & DEPENDENCIES

## 1. External Service Dependencies

| Service | Status | Implementation | Failure Mode |
|---|---|---|---|
| **Google Safe Browsing** | ✅ Implemented | `connectors/google_safe_browsing.py` — v4 API via httpx | Returns None, logged, circuit breaker trips |
| VirusTotal (mock) | ⚠️ Mock only | `connectors/virustotal.py` — returns hardcoded response | N/A (never makes real calls) |
| WhoisXML (mock) | ⚠️ Mock only | `connectors/whoisxml.py` — returns hardcoded response | N/A |
| PassiveTotal (mock) | ⚠️ Mock only | `connectors/passivetotal.py` — returns hardcoded response | N/A |
| **Tesseract OCR** | ✅ Implemented | `ocr.py` — subprocess call via pytesseract | Returns error message on failure |
| ML Model | ✅ Implemented | `model.joblib` loaded at startup | Falls back to rules-only mode |

**Key gaps:**
- 3 of 4 connectors are mock implementations — not usable in production
- No connector health check (healthy = able to reach API; current health only checks if module loads)
- No degraded mode when primary connector fails (e.g., Safe Browsing down → no URL safety check at all)

## 2. Internal Dependency Graph

```
AnalyzeRouter.analyze_text()
  └── OrchestratorService.analyze_text()
        └── PipelineRunner.run()
              ├── [1] MLStep (needs: model.joblib, vectorizer.joblib)
              ├── [2] RulesStep (needs: rules.py patterns)
              ├── [3] ExplanationStep (needs: rules output, ML output)
              ├── [4] IntelligenceStep (needs: entity extractor regex)
              ├── [5] EvidenceStep (needs: entities, explanation, rules, ML)
              ├── [6] AssessmentStep (needs: evidence scores, risk factors)
              ├── [7] RefinementStep (needs: assessment, rules)
              ├── [8] ReasoningStep (needs: evidence, assessment, refinement)
              ├── [9] ReportStep (needs: all prior step outputs)
              ├── [10] KnowledgeStep (needs: entities + knowledge base files)
              ├── [11] ConnectorStep (needs: entities + configured connectors)
              └── [12] FusionStep (needs: all prior step outputs)
```

**Observations:**
- Tight coupling between all steps — each step expects the full `AnalysisContext` with all prior outputs
- No step isolation — a bug in step 3 can corrupt context for step 4-12
- No parallel execution — despite most steps being independent, runner is strictly sequential
- No step-level caching — same entities could be re-extracted needlessly

## 3. Shared Dependencies

| Dependency | Used By | Version |
|---|---|---|
| `pydantic.BaseModel` | All schemas, configs, domain models | 2.9+ |
| `fastapi.Depends` | Auth, rate limiting, database injection | 0.115+ |
| `scikit-learn` | ML prediction + training | 1.5+ |
| `numpy` | ML inference | Implicitly via sklearn |
| `Pillow` | OCR image loading | 11+ |
| `pytesseract` | OCR engine | 0.3+ |
| `httpx` | Connector HTTP calls | 0.28+ |
| `pyjwt` | Auth token creation/verification | 2.9+ |
| `lxml` | HTML parsing (sanitization) | 5.3+ |
| `aiofiles` | Async file operations | 24+ |

## 4. Frontend API Dependencies

```
Frontend SPA
  ├── GET /version — app startup (version check)
  ├── POST /analyze/text — text analysis form
  ├── POST /analyze/image — image analysis form
  ├── POST /analyze/investigation — investigation workspace
  ├── GET /health — dashboard health page
  ├── GET /ready — deployment health page
  ├── GET /metrics — dashboard metrics
  ├── POST /auth/token — auth (analyst/investigation features)
  ├── POST /auth/refresh — token refresh
  └── POST /auth/verify — token verification
```

**All frontend pages depend on backend availability.** No offline mode. No mock data for disconnected use.

## 5. Shared State Dependencies

| State | Type | Shared Across | Lifetime |
|---|---|---|---|
| ML Model | In-memory object | All worker processes | Process lifetime |
| Rate Limiter | In-memory dict | Single process | Process lifetime |
| Connector Cache | In-memory dict | Single process | Process lifetime |
| JWT Secret Key | Env variable | All processes | Config lifetime |
| Knowledge Base | Loaded JSON | Single process | Process lifetime (loaded once) |

**Multi-process issue:** When running with Gunicorn + multiple workers:
- Each worker loads its own ML model copy (memory overhead)
- Rate limiter state is per-worker (bypassable by switching workers)
- Connector cache is per-worker (defeats caching purpose)
- Knowledge base is loaded independently (works but slow startup)

## 6. File System Dependencies

| Path | Type | Accessed By | Purpose |
|---|---|---|---|
| `backend/model.joblib` | Read | MLStep (startup) | Load ML model |
| `backend/vectorizer.joblib` | Read | MLStep (startup) | Load TF-IDF vectorizer |
| `backend/dataset/scam_dataset.csv` | Read | MLStep (startup) | Load dataset reference |
| `backend/features.json` | Read | ExplanationStep | Top features |
| `backend/knowledge/patterns/*.json` | Read | KnowledgeStep (per-request) | Pattern matching |
| `backend/knowledge/watchlists/*.json` | Read | KnowledgeStep (per-request) | Watchlist matching |
| `backend/knowledge/advisories/*.json` | Read | KnowledgeStep (per-request) | Advisory lookup |
| `backend/knowledge/examples/*.json` | Read | KnowledgeStep (per-request) | Similar scam lookup |
| `backend/knowledge/history/*.json` | Read | InvestigationEngine | Past investigations |
| `frontend/dist/` | Read | Nginx (static serving) | Frontend assets |

**Issues:**
- All file reads are synchronous (`open()` not `aiofiles.open()`) — blocks the event loop
- Knowledge base files are re-read on every request (no caching)
- No file watching for hot-reload in development
- `model.joblib` path is hardcoded — not configurable

## 7. Docker Compose Dependencies

```
services:
  fastapi (backend)
    depends_on:
      - redis      ❌ No code uses Redis
    ports:
      - "8000:8000"
  nginx (frontend + reverse proxy)
    depends_on:
      - fastapi
    ports:
      - "80:80"
      - "443:443"
  redis
    image: redis:alpine   ❌ Unused dependency
```

**Issue:** Redis is in docker-compose but no backend code connects to it. It's likely intended for future rate limiting / caching but currently is dead weight.

## 8. CI/CD Dependencies

```
GitHub Actions:
  - CI: Python 3.12, Node 22
  - CD: Docker Hub (push), target VPS/cloud
  - Dependency Review: GitHub API
```

**No external CI service dependencies** (no Jenkins, CircleCI, etc.) Straightforward GitHub Actions setup.
