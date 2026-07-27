# Project Current State

## 1. Executive Summary

ScamShield is a production-grade, full-stack scam detection platform built to analyze SMS, email, images, and social media messages for scam indicators. It combines ML classification (TF-IDF + Logistic Regression) with a heuristic rules engine, entity extraction, threat intelligence fusion, and a multi-stage evidence/reasoning pipeline. The frontend is a React 19 SPA with TypeScript, and the backend is a FastAPI application with 12 pipeline stages.

**Version**: 1.0.0  
**License**: MIT  
**Total source files**: ~250+ (backend 107, frontend ~150)  
**Tests**: 472 passing  
**Documentation**: 60+ markdown files  

### Key Metrics (from latest evaluation run)

| Metric | Value | Target | Status |
|--------|-------|--------|--------|
| Accuracy | 83.3% | >= 90% | ❌ Below target |
| Precision | 90.4% | >= 95% | ❌ Below target |
| Recall | 89.8% | >= 95% | ❌ Below target |
| F1 | 90.1% | >= 95% | ❌ Below target |
| FPR | 52.0% | < 10% | ❌ Critical |
| FNR | 10.2% | < 5% | ❌ Below target |
| Category Accuracy | 63.4% | > 80% | ❌ Poor |
| Risk Accuracy | 44.4% | > 80% | ❌ Poor |
| Assessment Accuracy | 36.4% | > 80% | ❌ Poor |
| P95 Latency | 14.8–91.9ms | < 1000ms | ✅ Good |

## 2. Project Overview

### Purpose
Detect and classify scam messages across SMS, email, WhatsApp, Telegram, and social media platforms using ML and heuristic analysis.

### Target Users
- General public (via frontend web app)
- Security researchers (via API and evaluation framework)
- Enterprise SOC teams (via investigation engine)

### Current Capabilities
- Text analysis via ML + rules hybrid engine
- Image OCR + analysis
- Multi-message investigation (timeline, campaign detection, entity merging)
- Knowledge retrieval (watchlists, advisories, pattern matching)
- Connector framework (Google Safe Browsing, mock threat intel)
- Evidence graph with reasoning trace
- AI-generated human-readable reports
- Full evaluation framework with HTML reports
- CI/CD with 5 GitHub Actions workflows
- Docker + docker-compose deployment
- Kubernetes manifests (preview quality)

### Completed Modules
- ML pipeline (TF-IDF + Logistic Regression)
- Rules engine (4 heuristic check functions)
- Entity extraction (17 extractors)
- Evidence scoring + conflict detection
- Assessment scoring (6 weighted components)
- Reasoning engine (family taxonomy + evidence graph)
- FP/FN refinement (16 rules)
- Report generation (4 templates)
- Knowledge engine (fuzzy matching + watchlists)
- Connector framework (auto-discovery + caching)
- Threat intelligence fusion
- Investigation engine (multi-message campaign detection)
- Authentication layer (JWT + RBAC)
- Security middleware (headers, rate limiting, CORS)
- Evaluation framework (3 modes + HTML reports)
- Continuous evaluation pipeline

### Current Maturity
- **Backend**: Production-ready (9/10)
- **Frontend**: Production-ready (8/10)
- **ML**: Research-grade (6/10) — static model, no retraining pipeline
- **Infrastructure**: CI/CD ready (8/10), K8s preview (4/10)
- **Testing**: Above average (8/10) — 472 tests but missing E2E
- **Documentation**: Exceptional (9.5/10)
- **Detection Quality**: Below production targets — 52% FPR is the critical blocker

## 3. Complete Architecture

### Backend
```
FastAPI Application
├── Middleware Stack (6 layers)
│   ├── RequestIDMiddleware
│   ├── SecurityHeadersMiddleware (CSP, HSTS, XFO, etc.)
│   ├── SlidingWindowRateLimitMiddleware
│   ├── RequestBodySizeMiddleware
│   ├── GZipMiddleware
│   └── RequestTimeoutMiddleware (30s)
├── Routers (3)
│   ├── /health, /ready, /live
│   ├── /analyze/text, /analyze/image, /analyze/investigation
│   └── /auth/token, /auth/refresh, /auth/verify
├── Pipeline (12 sequential steps)
│   ├── ML Step → Rules Step → Explanation Step
│   ├── Intelligence Step → Evidence Step
│   ├── Assessment Step → Refinement Step
│   ├── Reasoning Step → Report Step
│   ├── Knowledge Step → Connector Step → Fusion Step
│   └── Result
├── Core Infrastructure
│   ├── Config (5 deployment profiles)
│   ├── Logger (structured JSON)
│   ├── Metrics (latency percentiles)
│   ├── Auth (JWT + RBAC)
│   ├── Audit Trail
│   ├── API Keys
│   ├── Resilience (circuit breaker, retry)
│   └── Abuse detection (sliding window)
├── Connectors (3)
│   ├── Google Safe Browsing
│   ├── Mock Threat Connector
│   └── ConnectorRegistry (auto-discovery)
└── Evaluation Framework
    ├── evaluation_runner.py (3 modes)
    ├── Quality gate, dashboard, CI pipeline
    └── 3 datasets (162 + 511 + 12 samples)
```

### Frontend
```
React 19 + TypeScript 6 + Vite 8
├── 9 Pages (lazy-loaded)
├── 17 UI components
├── 5 Feature modules (Timeline, Graph, Report, Analysis, Shared)
├── 2 API services
└── 16 test files (Vitest)
```

### AI Pipeline
```
Input Text
  → [ML Step] TF-IDF → Logistic Regression → scam/safe + confidence
  → [Rules Step] OTP check + Urgency/Money + Links + Keywords → risk score
  → [Explanation Step] Category detection + indicator extraction + severity
  → [Intelligence Step] Entity extraction (17 types) + risk assignment
  → [Evidence Step] Correlate evidence + detect conflicts + decision score
  → [Assessment Step] 6-component scoring → assessment band + confidence
  → [Refinement Step] 7 FP rules + 9 FN rules → adjusted score + prediction
  → [Reasoning Step] Family taxonomy + evidence graph + decision trace
  → [Report Step] Human-readable investigation report
  → [Knowledge Step] Watchlist matching + advisory lookup
  → [Connector Step] External threat intel (GSB, etc.)
  → [Fusion Step] Merge connector results + final scoring
  → Result
```

## 4. Folder Structure

```
scamshield/
├── .github/workflows/        # CI/CD: 5 workflows (ci, backend, frontend, docker, release)
├── backend/                  # Python FastAPI application
│   ├── config/               # Settings, env-var overrides, validation
│   ├── connectors/           # External threat intel: GSB, mock, registry, cache
│   ├── core/                 # Infrastructure: auth, audit, metrics, middleware, resilience
│   │   ├── auth/             # JWT + RBAC
│   │   ├── config/           # 14 config modules (assessment, pipeline, security, etc.)
│   │   └── constants/        # 6 constant modules (categories, labels, extraction, etc.)
│   ├── data/                 # Training dataset (scam_dataset.csv)
│   ├── domains/              # Domain logic
│   │   ├── assessment/       # Scoring, evidence, conflicts, explanation
│   │   ├── intelligence/     # Entity extraction (17 extractors)
│   │   ├── reasoning/        # FP/FN rules, evidence graph, family taxonomy, decision trace
│   │   ├── reporting/        # Report generation (4 templates)
│   │   └── shared/           # Shared models, utils, exceptions
│   ├── middleware/            # App middleware (empty, moved to core/)
│   ├── models/               # ML model artifacts (model.joblib, vectorizer.joblib)
│   ├── pipeline/             # 12-step pipeline execution + registry
│   │   └── steps/            # Individual pipeline step implementations
│   ├── routers/              # FastAPI route handlers (health, analyze, auth)
│   ├── schemas/              # Pydantic request/response models
│   ├── scripts/              # Quality gate, dashboard, CI pipeline
│   ├── services/             # Orchestrator, threat intelligence fusion
│   ├── tests/                # 472 tests across unit/security/integration/architecture
│   └── utils/                # Text cleaning, validation helpers
├── docs/                     # 35 documentation files
├── evaluation/               # Evaluation framework
│   ├── datasets/             # 3 datasets (benchmark, validation, knowledge)
│   ├── reports/              # Versioned evaluation runs (metrics, predictions, reports)
│   └── scripts/              # Schema, build, report, error analysis
├── frontend/                 # React 19 + TypeScript SPA
│   ├── src/                  # 9 pages, 17 components, 5 features, 16 tests
│   └── Dockerfile + nginx.conf
├── k8s/                      # Kubernetes manifests (preview)
│   ├── backend-deployment.yaml
│   ├── frontend-deployment.yaml
│   ├── hpa.yaml
│   ├── ingress.yaml
│   └── configmap.yaml
├── nginx/                    # External reverse proxy config
├── scripts/                  # Shell scripts (start, stop, health, diagnostics)
└── Root *.md                 # 35+ documentation files
```

## 5. Data Flow

```
User Input (text/image)
    │
    ▼
[FastAPI Router] → Validate + normalize
    │
    ▼
[PipelineRunner] → Execute 12 steps sequentially
    │
    ├── ML Step: TF-IDF vectorize + Logistic Regression predict
    ├── Rules Step: 4 heuristic checks → risk score (0-100)
    ├── Explanation Step: Category + indicators + severity
    ├── Intelligence Step: 17 entity extractors + risk assignment
    ├── Evidence Step: Correlate + detect conflicts + decision score
    ├── Assessment Step: 6-component weighted score (0-100)
    ├── Refinement Step: 16 FP/FN rules → adjusted score
    ├── Reasoning Step: Family taxonomy + evidence graph + decision trace
    ├── Report Step: Human-readable report with 4 templates
    ├── Knowledge Step: Watchlist matching + advisory lookup
    ├── Connector Step: External threat intel queries
    └── Fusion Step: Merge + aggregate confidence
    │
    ▼
[PipelineResult] → Serialize to AnalysisResponse (55 fields)
    │
    ▼
[Frontend] → Render result (risk level, evidence graph, report, entities)
```

## 6. Complete Feature Inventory

### Complete
- Text scam analysis (ML + rules)
- Entity extraction (17 types: URL, email, phone, UPI, bank, Aadhaar, etc.)
- Evidence scoring and conflict detection
- Assessment scoring with 6 weighted components
- Reasoning with family taxonomy and evidence graph
- AI-generated investigation reports
- Knowledge engine (watchlist matching, fuzzy search)
- Connector framework (auto-discovery, caching, retry)
- Google Safe Browsing integration
- Threat intelligence fusion
- Multi-message investigation (campaign detection, timeline, entity merging)
- JWT authentication + RBAC (guest/authenticated/admin)
- Rate limiting (sliding window, IP blocking)
- Security headers (CSP, HSTS, XFO, XSS, etc.)
- Structured logging with correlation IDs
- Metrics (latency percentiles, request counts)
- Health checks (liveness, readiness, version)
- CI/CD (5 GitHub Actions workflows)
- Docker deployment
- Evaluation framework (3 modes, HTML reports)
- Quality gate + dashboard + CI pipeline

### Partial
- Image OCR analysis (Tesseract works but not deeply integrated)
- Multilingual support (Tanglish/Tamil normalization exists but not production-tested)
- API versioning (internal version constants but no URL versioning)
- Model calibration (calibration module exists but not tuned on production data)

### Prototype
- Kubernetes deployment (manifests exist but missing PVC, secrets, PDB, network policies)
- Continuous evaluation pipeline (exists but not integrated into CI)
- Admin API key management (code exists but no routes)

### Planned (from docs)
- Model retraining pipeline
- Persistent storage for analysis history
- User accounts and saved analyses
- OAuth/OIDC integration
- Prometheus metrics exporter
- Grafana dashboards

### Deprecated
- `core/security.py::RateLimitMiddleware` (superseded by `core/abuse.py::SlidingWindowRateLimitMiddleware`)
- `domains/shared/exceptions.py` (duplicate of `core/exceptions.py`)

## 7. API Inventory

### Health Endpoints
| Endpoint | Method | Purpose | Input | Output | Dependencies |
|----------|--------|---------|-------|--------|-------------|
| `/health` | GET | Full system health | — | Model exists, connectors, dependencies | Model files, connectors |
| `/ready` | GET | Readiness probe | — | `{"status": "ready"}` | — |
| `/live` | GET | Liveness probe | — | `{"status": "alive"}` | — |
| `/version` | GET | Version info | — | Version, build time, commit | — |
| `/metrics` | GET | Prometheus metrics | — | Prometheus text format | Metrics module |

### Analysis Endpoints
| Endpoint | Method | Purpose | Input | Output | Dependencies |
|----------|--------|---------|-------|--------|-------------|
| `/analyze/text` | POST | Scam text analysis | `{"text": str}` | `AnalysisResponse` (55 fields) | Full pipeline |
| `/analyze/image` | POST | Image OCR + analysis | Multipart image | `ImageAnalysisResponse` | OCR + full pipeline |
| `/analyze/investigation` | POST | Multi-message investigation | `{"artefacts": [...]}` | `InvestigationResponse` | Investigation engine |

### Auth Endpoints
| Endpoint | Method | Purpose | Input | Output | Dependencies |
|----------|--------|---------|-------|--------|-------------|
| `/auth/token` | POST | User login | `{"username", "password"}` | `TokenResponse` | Auth module |
| `/auth/token/admin` | POST | Admin login | `{"username", "password"}` | `TokenResponse` | Auth module |
| `/auth/refresh` | POST | Token refresh | `{"refresh_token"}` | `TokenResponse` | Auth module |
| `/auth/verify` | GET | Token verification | Auth header | `{"valid": bool}` | Auth module |

### AnalysisResponse Structure (55 fields)
```
{
  "prediction": "scam"|"safe",
  "confidence": float,
  "risk_level": "CRITICAL"|"HIGH"|"MEDIUM"|"LOW"|"VERY LOW",
  "decision_level": "CRITICAL"|"HIGH RISK"|"SUSPICIOUS"|"LOW RISK"|"SAFE",
  "assessment_band": str,
  "scam_category": str,
  "reasoning_family": str,
  "reasoning_subfamily": str,
  "decision_score": int,
  "assessment_score": int,
  "assessment_confidence": str,
  "assessment_summary": str,
  "business_reason": str,
  "technical_reason": str,
  "recommended_action": str,
  "review_required": bool,
  "manual_review_reason": str,
  "entities": [...],
  "evidence": {...},
  "confidence_breakdown": {...},
  "risk_breakdown": {...},
  "reasoning_summary": str,
  "dominant_evidence_chain": [...],
  "evidence_graph": {...},
  "decision_trace": {...},
  "investigation_report": {...},
  "rule_score": float,
  "rule_label": str,
  "rule_reasons": [...],
  "execution_telemetry": {...},
  "errors": []
}
```
