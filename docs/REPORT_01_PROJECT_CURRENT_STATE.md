# ScamShield Master Audit — Report 01: Project Current State

**Date:** 2026-07-26 | **Repo:** scamshield-main | **Version:** v1.0.0

---

## 1. Executive Summary

ScamShield is a Python/FastAPI + React/TypeScript scam detection system that analyzes SMS and image text through a 12-stage pipeline combining ML classification, heuristic rules, entity extraction, evidence correlation, reasoning, and threat intel fusion. The repository contains ~10,107 lines of Python backend code, ~8,334 lines of TypeScript/TSX frontend code, and extensive documentation.

The project has reached v1.0.0 with 244/244 tests passing, TypeScript strict mode passing with 0 errors, and a 511-sample validation dataset. Production build succeeds. However, several critical metrics reveal the system is not production-ready: 72.8% accuracy, 61.7% false positive rate, 0.0% assessment band accuracy.

---

## 2. Project Overview

### Purpose
Detect scam SMS messages, phishing attempts, and fraudulent communications targeting Indian users. Combines ML classification (LogisticRegression + TF-IDF) with 18 heuristic rules, entity extraction, evidence correlation, reasoning chains, and threat intelligence fusion.

### Target Users
- **Primary:** Indian consumers receiving SMS messages in English and Indian languages
- **Secondary:** Law enforcement / cyber crime investigators (investigation dashboard)
- **Tertiary:** Researchers studying scam detection methodologies

### Current Capabilities
- Text analysis via ML + rules + entity extraction + evidence + reasoning + assessment + refinement + knowledge lookup + connector queries + threat fusion
- Image analysis via OCR (Tesseract) + text analysis pipeline
- Multi-artefact investigation with campaign detection, timeline, relationship graph
- Health/liveness/readiness endpoints
- OpenAPI docs at /docs and /redoc
- Prometheus metrics endpoint at /metrics
- Docker Compose + Kubernetes deployment
- GitHub Actions CI/CD (5 workflows)

### Completed Modules
- Orchestrator with 12-stage pipeline
- Rule engine (18 check functions, 4 grouped into analyze_message)
- ML service (LogisticRegression via sklearn)
- Entity intelligence (20+ extractor functions)
- Evidence service (correlation + conflict detection)
- Assessment service (weighted scoring)
- Refinement engine (13 refinement rules)
- Reasoning engine (evidence graph + family classification)
- Knowledge service (intelligence matching against watchlists/advisories/history)
- Connector framework (abstract base + Google Safe Browsing + mock)
- Threat intelligence fusion engine
- Investigation service (multi-artefact, campaign, timeline, graph)
- Report service (detailed + investigation reports)
- Frontend: landing, dashboard, text/image analysis, results, investigation, system status, deployment health, 404
- Frontend features: analysis cards (13), relationship graph (7 components), timeline (5 components), report builder, demo walkthrough
- CI/CD: 5 GitHub Actions workflows
- Docker: 2 Dockerfiles + compose with security hardening
- K8s: 5 manifests
- Evaluation framework with 3 datasets (162 + 511 samples)

### Current Maturity
- **Engineering maturity:** Beta/Release Candidate
- **Product maturity:** Alpha — functional but not user-ready
- **Production readiness:** Pre-production — gap analysis shows critical missing items (auth, rate limiting, secrets management, monitoring)
- **ML maturity:** Beta — 72.8% accuracy, 61.7% FPR, no retraining pipeline

---

## 3. Complete Architecture

### Backend Architecture

```
FastAPI (main.py)
├── Routers
│   ├── analyze.py    POST /analyze/text, /analyze/image, /analyze/investigation
│   └── health.py     GET /health, /ready, /live
├── Core
│   ├── constants.py     774 lines — all scam taxonomy, patterns, risk maps
│   ├── exceptions.py    102 lines — custom exception hierarchy
│   ├── metrics.py       132 lines — request/stage counters
│   ├── diagnostics.py   137 lines — system health checks
│   ├── context.py       44 lines  — request ID context
│   ├── middleware.py    63 lines  — request ID middleware
│   ├── log_config.py    52 lines  — logging configuration
│   └── logger.py        96 lines  — structured logger
├── Config
│   └── settings.py      203 lines — all tunable parameters
├── Services (12-stage pipeline)
│   ├── orchestrator.py      283 lines — pipeline coordinator
│   ├── ml_service.py         7 lines — wrapper around predict.py
│   ├── rules_service.py     27 lines — wrapper around rules.py
│   ├── intelligence_service.py  382 lines — entity extraction
│   ├── explanation_service.py   212 lines — indicator/scam category
│   ├── evidence_service.py      445 lines — evidence correlation
│   ├── assessment_service.py    204 lines — weighted scoring
│   ├── refinement_service.py    701 lines — FP/FN refinement rules
│   ├── reasoning_service.py     646 lines — evidence graph + family classification
│   ├── knowledge_service.py     826 lines — intelligence matching (largest service)
│   ├── report_service.py        389 lines — report generation
│   ├── investigation_service.py 696 lines — multi-artefact investigation
│   ├── threat_intelligence_service.py 334 lines — fusion engine
│   └── ocr_service.py           11 lines — wrapper around ocr.py
├── Connectors
│   ├── base.py                52 lines — abstract connector
│   ├── google_safe_browsing.py 332 lines — Google SB v4 API
│   ├── mock.py                144 lines — test double
│   ├── manager.py             248 lines — connector lifecycle
│   ├── registry.py             77 lines — source registration
│   ├── cache.py                65 lines — response cache
│   ├── models.py               39 lines — data models
│   ├── utils.py                58 lines — utilities
│   └── exceptions.py           18 lines — error types
├── Schemas (Pydantic)
│   ├── requests.py      16 lines — TextAnalysisRequest, InvestigationRequest
│   └── responses.py    197 lines — AnalysisResponse, ImageAnalysisResponse, InvestigationResponse
├── Intelligence Data
│   ├── loader.py        115 lines — loads advisories, watchlists, history, patterns
│   ├── schemas.py       145 lines — AdvisoryRecord, ThreatRecord, HistoricalInvestigation
│   ├── advisories/      JSON — banks, cert_in, internal, npci, rbi
│   ├── watchlists/      JSON — domain, email, phone, upi
│   ├── patterns/        JSON — known_patterns.json (226 lines)
│   ├── history/         JSON — investigations.json (49 lines)
│   └── examples/        JSON — known_scam_examples.json (66 lines)
├── Models (trained)
│   ├── model.joblib            41 KB — LogisticRegression
│   └── vectorizer.joblib      192 KB — TfidfVectorizer
├── Data
│   └── scam_dataset.csv    ~5,000 rows, 548 KB
├── Utils
│   ├── text.py      9 lines
│   └── validate.py  43 lines
└── Scripts
    └── quality_gate.py  254 lines — 9 QA checks
```

### Frontend Architecture

```
React 18 + TypeScript + Vite
├── App.tsx → Providers → AppRouter
├── Providers
│   └── QueryClientProvider (TanStack React Query)
├── Router (react-router-dom v6 with lazy loading)
│   ├── / → Landing
│   ├── /dashboard → Dashboard
│   ├── /analyze/text → TextAnalysis
│   ├── /analyze/image → ImageAnalysis
│   ├── /analysis/result → AnalysisResult
│   ├── /investigation → Investigation
│   ├── /system → SystemStatus
│   └── * → NotFound
├── Layouts
│   ├── RootLayout (sidebar + header + footer + Outlet)
│   ├── Sidebar (nav links)
│   ├── Header (title + status)
│   └── Footer (minimal)
├── Pages (9)
│   ├── landing.tsx         215 lines — hero, metrics, features, FAQ, CTA
│   ├── dashboard.tsx       225 lines — stats cards, time series
│   ├── text-analysis.tsx   126 lines — text input form
│   ├── image-analysis.tsx  225 lines — image upload + preview
│   ├── analysis-result.tsx 170 lines — result display
│   ├── investigation.tsx   268 lines — multi-artefact investigation UI
│   ├── system-status.tsx   325 lines — health metrics dashboard
│   ├── deployment-health.tsx 149 lines — deployment status
│   └── not-found.tsx        20 lines — 404
├── Features
│   ├── analysis/      13 card components + context + hook
│   ├── graph/         7 components (evidence graph visualization)
│   ├── report/        2 components (report builder + section view)
│   ├── timeline/      5 components (investigation timeline)
│   ├── demo/          2 components + 301-line sample-cases.ts
│   └── shared/        1 skeleton component
├── Components/UI
│   ├── error-boundary.tsx, retry-button.tsx, toast-container.tsx
│   └── ui/ 17 primitive components (badge, button, card, skeleton, etc.)
├── Design tokens (status.ts, tokens.ts)
├── Hooks (use-scamshield.ts, use-toast.ts)
├── Services (api.ts axios instance, scamshield.ts typed functions)
├── Types (api.ts 140 lines, index.ts 18 lines)
├── Utils (cn.ts, diagnostics.ts, validation.ts, version.ts)
└── Tests (20 files, ~646 lines)
```

### AI Pipeline (12 stages)

```
Input Text
  │
  ▼
1. ML Classification   → prediction + confidence (LogisticRegression + TF-IDF)
  │
  ▼
2. Rule Engine         → risk_score + risk_label + reasons (18 heuristic rules)
  │
  ▼
3. Explanation         → summary + risk_level + scam_category + indicators + threats
  │
  ▼
4. Threat Intelligence → entities + entity_summary + entity_risk (20 extractors)
  │
  ▼
5. Evidence            → decision_score + supporting/conflicting evidence + confidence/risk breakdown
  │
  ▼
6. Assessment          → assessment_score + band + confidence + business/technical reasons
  │
  ▼
7. Refinement          → refined_prediction + refined_score + decision_stability (13 rules)
  │
  ▼
8. Reasoning           → family + subfamily + evidence graph + decision trace + dominant chains
  │
  ▼
9. Report              → full investigation report with all sections
  │
  ▼
10. Knowledge          → matches against watchlists/advisories/historical investigations
  │
  ▼
11. Connectors         → enrichment from external threat intel sources (Google SB)
  │
  ▼
12. Threat Fusion      → fused verdict from all connector sources
  │
  ▼
Output Dict (90+ fields in AnalysisResult dataclass → serialized to dict via asdict)
```

### Reasoning Engine
Located in `reasoning_service.py` (646 lines). Builds an evidence graph (EvidenceNode + EvidenceEdge dataclasses), classifies scam family/subfamily based on evidence weighted scoring, produces decision trace, dominant evidence chains, and reasoned summary. Outputs `ReasoningResult` dataclass with 11 fields.

### Knowledge Engine
Located in `knowledge_service.py` (826 lines — largest backend file). Loads all intelligence data (advisories, watchlists, history, patterns) via `loader.py`, then matches analysis entities against known indicators using exact match, prefix, suffix, and Levenshtein fuzzy matching. Returns matches with confidence scores, family classifications, and advisory references.

### Connector Framework
Abstract base class (`BaseConnector`) with concrete implementations (`GoogleSafeBrowsingConnector`, `MockConnector`). Managed by `ConnectorManager` which handles lifecycle, registration via `Registry`, and response caching via `Cache`. Configuration-driven timeouts, retries, and parallelism.

### Investigation Engine
Located in `investigation_service.py` (696 lines). Accepts multiple artefacts, validates them, runs full pipeline on each, merges entities across artefacts, builds timeline events, detects coordinated campaigns (shared phones/domains/UPI/emails, repeated wording, same scam family), constructs relationship graph, computes global risk, and produces investigation report. Outputs `InvestigationResult` dataclass.

### Threat Intelligence
Located in `threat_intelligence_service.py` (334 lines). Fusion engine that takes results from multiple connectors (currently Google Safe Browsing + mock), deduplicates, clusters by indicator, computes agreement/conflict scores, ranks evidence, resolves conflicts by source weight, and produces fused verdict (clean/suspicious/malicious).

### Deployment & Infrastructure
- **Docker Compose:** Backend + Frontend with health checks, resource limits, security hardening (read_only, cap_drop, no-new-privileges, tmpfs)
- **Dockerfiles:** Backend (21 lines), Frontend (24 lines, Nginx-based)
- **Kubernetes:** 5 manifests (backend-deployment, frontend-deployment, configmap, hpa, ingress)
- **Nginx:** 116-line config with reverse proxy, static serving, rate limiting
- **Scripts:** 10 shell scripts (diagnostics, health, logs, restart, start, status, stop, validate-env, verify, version), 1 PowerShell script
- **GitHub Actions:** 5 workflows (backend.yml, frontend.yml, ci.yml, docker.yml, release.yml)

---

## 4. Folder Structure & Responsibilities

| Directory | Responsibility | Key Contents |
|-----------|---------------|--------------|
| `backend/`  | Python FastAPI backend | 52 .py files, 10,107 lines |
| `backend/services/` | 14 service modules | All pipeline stages |
| `backend/connectors/` | Threat intel connector framework | 9 files |
| `backend/core/` | Core infrastructure | constants, exceptions, metrics, diagnostics, logging, middleware |
| `backend/config/` | Configuration | settings.py (203 lines, all tunable params) |
| `backend/schemas/` | Pydantic request/response models | requests.py (16 lines), responses.py (197 lines) |
| `backend/routers/` | FastAPI route handlers | analyze.py (212 lines), health.py (80 lines) |
| `backend/models/` | Trained ML model files | model.joblib (41 KB), vectorizer.joblib (192 KB) |
| `backend/intelligence/` | Threat intelligence data | JSON watchlists, advisories, patterns, history |
| `backend/data/` | Training data | scam_dataset.csv (~5,000 rows) |
| `backend/tests/` | Test suite | 12 test files, ~1,816 lines |
| `backend/utils/` | Utility functions | text.py, validate.py |
| `backend/scripts/` | Backend scripts | quality_gate.py |
| `frontend/` | React/TypeScript frontend | 86 TS/TSX files, 8,334 lines |
| `frontend/src/pages/` | Route-level page components | 9 pages |
| `frontend/src/features/` | Feature modules | analysis, graph, report, timeline, demo, shared |
| `frontend/src/components/` | Shared UI components | error-boundary, retry-button, toast, 17 ui primitives |
| `frontend/src/layouts/` | Layout components | root-layout, sidebar, header, footer |
| `frontend/src/hooks/` | Custom React hooks | use-scamshield, use-toast |
| `frontend/src/services/` | API client layer | api.ts (axios), scamshield.ts (typed functions) |
| `frontend/src/types/` | TypeScript type definitions | api.ts, index.ts |
| `frontend/src/utils/` | Utility functions | cn, diagnostics, validation, version |
| `frontend/src/design/` | Design tokens | status.ts, tokens.ts |
| `frontend/src/test/` | Frontend tests | 20 files, ~646 lines |
| `evaluation/` | ML evaluation framework | evaluation_runner.py, 5 scripts, 3 datasets, report output |
| `evaluation/datasets/` | Benchmark datasets | benchmark.json (162 samples), validation_v1.json (511 samples), knowledge_benchmark.json |
| `evaluation/reports/` | Evaluation results | 10 timestamped eval runs with metrics/predictions/errors |
| `evaluation/scripts/` | Evaluation scripts | schema, build_dataset, report, error_analysis, validate |
| `k8s/` | Kubernetes manifests | 5 files |
| `nginx/` | Nginx configuration | default.conf (116 lines) |
| `scripts/` | Shell/PowerShell operational scripts | 11 files |
| `.github/workflows/` | CI/CD pipelines | 5 workflow files (513 total lines) |
| `docs/` | Project documentation | 18 files covering all aspects |

---

## 5. Data Flow

### Text Analysis Flow

```
1. USER INPUT
   POST /analyze/text { "text": "..." }
   │
2. ROUTER (analyze.py)
   │  sanitise_text() → validates + cleans
   │  metrics.record_request()
   │  calls analyze_text()
   │
3. ORCHESTRATOR (orchestrator.py)
   │  Creates AnalysisResult dataclass (90+ fields)
   │  Runs 12 timed stages sequentially
   │  Each stage populates AnalysisResult fields
   │  Returns asdict(result) → Dict[str, object]
   │
4. ROUTER RESPONSE
   │  AnalysisResponse(**result) → Pydantic validation
   │  Returns JSON to client
   │
5. FRONTEND
   │  api.post() → useMutation hook
   │  Navigates to /analysis/result with state
   │  Displays via 13 analysis card components
```

### Image Analysis Flow

```
1. USER UPLOAD
   POST /analyze/image (multipart)
   │  Content-Type validation
   │  File size validation
   │
2. OCR EXTRACTION
   │  Temporary file write
   │  extract_text() → Tesseract call
   │  Cleanup temp file
   │
3. Same as text analysis (steps 3-5)
   │  + extracted_text included in response
```

### Investigation Flow

```
1. POST /analyze/investigation { "artefacts": [...] }
   │
2. INVESTIGATION SERVICE
   │  _validate_artefacts() → filter empty/invalid
   │  _analyse_artefacts() → call analyze_text() per artefact
   │  _merge_entities() → cross-artefact dedup
   │  _detect_repeated_indicators()
   │  _build_timeline() → event sequence
   │  _detect_campaign() → shared entities, wording, family
   │  _build_relationship_graph() → nodes + edges
   │  _compute_global_risk() → weighted scoring
   │
3. KNOWLEDGE ENRICHMENT
   │  enrich_investigation_result() → matches against intel
   │
4. RESPONSE
   │  InvestigationResponse → artefacts, merged_entities, campaign, timeline, graph, assessment
```

---

## 6. Complete Feature Inventory

### Backend Features

| Feature | Status | File | Lines | Notes |
|---------|--------|------|-------|-------|
| ML Classification | **Complete** | predict.py, ml_service.py | 43+7 | LogisticRegression + TF-IDF |
| Rule Engine | **Complete** | rules.py, rules_service.py | 172+27 | 18 patterns in 4 composite checks |
| Entity Extraction | **Complete** | intelligence_service.py | 382 | 20 extractors (URL, phone, email, UPI, etc.) |
| Explanation Generation | **Complete** | explanation_service.py | 212 | Summary, indicators, threats |
| Evidence Correlation | **Complete** | evidence_service.py | 445 | Decision scoring, confidence breakdown |
| Risk Assessment | **Complete** | assessment_service.py | 204 | Weighted 5-factor scoring |
| Refinement Engine | **Complete** | refinement_service.py | 701 | 13 FP/FN mitigation rules |
| Reasoning Engine | **Complete** | reasoning_service.py | 646 | Evidence graph, family classification |
| Report Generation | **Complete** | report_service.py | 389 | Structured reports with sections |
| Knowledge Engine | **Complete** | knowledge_service.py | 826 | Intel matching via fuzzy search |
| Connector Framework | **Complete** | connectors/*.py | 946 total | Base, GSB, Mock, Manager, Registry, Cache |
| Threat Intel Fusion | **Complete** | threat_intelligence_service.py | 334 | Agreement/conflict/resolution |
| Investigation Engine | **Complete** | investigation_service.py | 696 | Multi-artefact, campaign, timeline, graph |
| OCR Service | **Partial** | ocr_service.py, ocr.py | 11+63 | Tesseract-dependent, no tests |
| Input Validation | **Complete** | utils/validate.py | 43 | sanitise_text() |
| Text Utilities | **Prototype** | utils/text.py | 9 | Token count only |
| API Routers | **Complete** | routers/analyze.py, health.py | 212+80 | 6 endpoints |
| Pydantic Schemas | **Complete** | schemas/*.py | 16+197 | Request/response validation |
| Settings/Config | **Complete** | config/settings.py | 203 | 100+ tunable parameters |
| Constants | **Complete** | core/constants.py | 774 | All taxonomy, patterns, risk maps |
| Exception Hierarchy | **Complete** | core/exceptions.py | 102 | 12 custom exception types |
| Metrics | **Complete** | core/metrics.py | 132 | Request counters, stage timers |
| Diagnostics | **Complete** | core/diagnostics.py | 137 | Health checks |
| Structured Logging | **Complete** | core/logger.py, log_config.py | 96+52 | JSON/text, file/stdout |
| Request ID Middleware | **Complete** | core/middleware.py | 63 | Per-request correlation ID |
| Authentication | **Not implemented** | — | — | No auth layer |
| Rate Limiting | **Not implemented** | — | — | No API rate limiting |
| Model Training | **Prototype** | train.py | 72 | Basic script, no HP tuning |
| Quality Gate | **Complete** | scripts/quality_gate.py | 254 | 9 automated checks |

### Frontend Features

| Feature | Status | File(s) | Lines | Notes |
|---------|--------|---------|-------|-------|
| Landing Page | **Complete** | landing.tsx | 215 | Hero, metrics, features, FAQ, CTA |
| Dashboard | **Complete** | dashboard.tsx | 225 | Stats, time series chart |
| Text Analysis | **Complete** | text-analysis.tsx | 126 | Input form |
| Image Analysis | **Complete** | image-analysis.tsx | 225 | Upload + preview |
| Analysis Result | **Complete** | analysis-result.tsx | 170 | Results display |
| Investigation | **Complete** | investigation.tsx | 268 | Multi-artefact investigation |
| System Status | **Complete** | system-status.tsx | 325 | Health metrics dashboard |
| Deployment Health | **Complete** | deployment-health.tsx | 149 | Status page |
| Analysis Cards (13) | **Complete** | features/analysis/components/ | ~1,100 total | Summary, assessment, category, confidence, entity, evidence, recommendation, risk, technical, threat, timeline |
| Evidence Graph | **Complete** | features/graph/ | ~1,200 total | 7 components for relationship graph |
| Investigation Timeline | **Complete** | features/timeline/ | ~900 total | 5 components for timeline |
| Report Builder | **Complete** | features/report/ | ~350 total | 2 components |
| Demo/Walkthrough | **Complete** | features/demo/ | ~550 total | Sample cases, demo panel |
| Error Boundary | **Complete** | error-boundary.tsx | 50 | Catches render errors |
| Toast Notifications | **Complete** | toast-container.tsx | 37 | Auto-dismiss toasts |
| UI Component Library | **Complete** | components/ui/ | 17 primitives | Badge, button, card, skeleton, etc. |
| Design Tokens | **Complete** | design/ | 120 total | Status colors, spacing, typography |
| API Client | **Complete** | services/ | 77 total | Axios + typed service functions |
| React Query Hooks | **Complete** | hooks/ | 67 total | 6 hooks for API + toast |
| TypeScript Types | **Complete** | types/ | 158 total | API types |
| State Management | **Partial** | — | — | React Query only; no client state mgmt |
| E2E Tests | **Not implemented** | — | — | No Playwright/Cypress |
| PWA Support | **Not implemented** | — | — | No service worker |
| Accessibility Audit | **Partial** | — | — | UX_AUDIT.md covers some WCAG |
| Mobile Responsiveness | **Not verified** | — | — | Not confirmed from source |

### Infrastructure Features

| Feature | Status | Notes |
|---------|--------|-------|
| Docker Compose | **Complete** | Hardened (read_only, cap_drop, no-new-privileges) |
| Dockerfiles | **Complete** | Backend + Frontend |
| Kubernetes Manifests | **Complete** | 5 manifests |
| Nginx Config | **Complete** | Full reverse proxy + static serving |
| GitHub Actions CI | **Complete** | 5 workflows |
| Secret Management | **Not implemented** | `.env` file only |
| Database | **Not implemented** | No persistence layer |
| Monitoring Stack | **Not implemented** | No Grafana/Prometheus config |
| Alerting | **Not implemented** | No alert manager |
| CD Pipeline | **Complete** | GHCR publish on version tag |

### Evaluation Features

| Feature | Status | Notes |
|---------|--------|-------|
| Evaluation Runner | **Complete** | API + local modes |
| Dataset Builder | **Complete** | Build dataset from templates |
| Schema Validation | **Complete** | Dataset schema validation |
| HTML Report Generation | **Complete** | Rich HTML reports |
| Error Analysis | **Complete** | Error classification |
| Output Validation | **Complete** | Prediction validation |
| 162-sample Benchmark | **Complete** | benchmark.json |
| 511-sample Validation | **Complete** | validation_v1.json |
| Knowledge Benchmark | **Complete** | knowledge_benchmark.json |
| Family Benchmark | **Complete** | family_benchmark reports |
| 10 Evaluation Runs | **Complete** | Multiple timestamped runs |

---

## 7. API Inventory

### Health Router

| Endpoint | Method | Purpose | Input | Output | Dependencies |
|----------|--------|---------|-------|--------|-------------|
| `/health` | GET | Overall health status | — | `{status, version, uptime, ...}` | diagnostics module |
| `/ready` | GET | Readiness probe | — | `{ready, checks: [...]}` | diagnostics module |
| `/live` | GET | Liveness probe | — | `{alive}` | Minimal |
| `/metrics` | GET | Prometheus metrics snapshot | — | `{total_requests, failures, avg_latency, stages: {...}}` | metrics module |

### Analysis Router

| Endpoint | Method | Purpose | Input | Output | Dependencies |
|----------|--------|---------|-------|--------|-------------|
| `/analyze/text` | POST | Analyze SMS text | `TextAnalysisRequest { text: string }` | `AnalysisResponse` (90+ fields) | Full pipeline (orchestrator, all services) |
| `/analyze/image` | POST | Analyze image via OCR | `UploadFile (image)` | `ImageAnalysisResponse` (analysis + extracted_text) | OCR + full pipeline |
| `/analyze/investigation` | POST | Multi-artefact investigation | `InvestigationRequest { artefacts: [...] }` | `InvestigationResponse` | Investigation service + knowledge enrichment |

### AnalysisResponse Structure (90+ fields)

```
{
  prediction, confidence, rule_score, rule_label,
  reasons, suggested_action, summary, risk_level,
  scam_category, detected_indicators, threats,
  recommended_actions, entities, entity_summary, entity_risk,
  decision_score, decision_level, decision_reasoning,
  supporting_evidence, conflicting_evidence,
  confidence_breakdown, risk_breakdown,
  recommended_priority, recommended_action,
  assessment_score, assessment_band, assessment_confidence,
  assessment_summary, business_reason, technical_reason,
  review_required, manual_review_reason,
  investigation_report,
  refined_prediction, refined_assessment_score, refined_assessment_confidence,
  refined_review_required, refinement_applied_rules, refinement_summary,
  decision_stable, stability_concerns,
  reasoning_family, reasoning_subfamily, reasoning_family_confidence,
  reasoning_summary, reasoning_evidence_graph, reasoning_decision_trace,
  reasoning_primary_evidence, reasoning_supporting_evidence,
  reasoning_weak_evidence, reasoning_contradictory_evidence,
  reasoning_dominant_evidence_chain,
  knowledge_matches, advisory_references, historical_matches,
  connector_matches, threat_intel_fusion
}
```

### InvestigationResponse Structure

```
{
  investigation_id, artefacts_analysed,
  artefact_results: [{index, type, text_preview, prediction, assessment_score, ...}],
  merged_entities: { phone: [...], url: [...], email: [...], ... },
  repeated_indicators: { "OTP Request": 3, ... },
  campaign: { campaign_detected, confidence, indicators, summary },
  timeline: [{index, artefact, event_type, description, details}],
  relationship_graph: { nodes: [...], edges: [...] },
  global_assessment: { overall_risk, overall_score, confidence, ... },
  investigation_report: { report_id, generated_at, report_type, ... },
  knowledge_matches, advisory_references, historical_matches
}
```
