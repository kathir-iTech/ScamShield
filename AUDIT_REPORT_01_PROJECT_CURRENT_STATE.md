# REPORT 1: PROJECT CURRENT STATE

## 1. Executive Summary

ScamShield is an open-source AI-powered scam SMS detection engine at version 1.0.0. It combines ML classification (LogisticRegression + TF-IDF), heuristic rules (18 patterns), OCR analysis, and multi-source threat intelligence into a single FastAPI backend with a React frontend. The project is **functionally complete but not production-ready** — it has strong depth in the backend domain logic but significant gaps in testing, error handling, observability, and deployment hardening.

## 2. Project Overview

**Purpose:** Detect phishing, fraud, and scam SMS messages using ML + rules. Target is India-specific scams (UPI, KYC, bank fraud, lottery, job, etc.).

**Target users:** Security researchers, telecom operators, financial institutions, general public (via demo).

**Current capabilities:**
- ML classification (LogisticRegression, TF-IDF, ~83% accuracy)
- 18 heuristic rule patterns (OTP, UPI, KYC, urgency, bank impersonation, etc.)
- OCR text extraction (Tesseract)
- Entity extraction (20+ types: URLs, phones, emails, UPI IDs, bank accounts, etc.)
- Multi-factor confidence scoring (ML + rules + entities + explanation)
- Evidence ranking with contradiction detection
- Pluggable connector framework (Google Safe Browsing implemented)
- Knowledge base matching (patterns, watchlists, advisories, historical investigations)
- Threat intelligence fusion (multi-source aggregation with conflict resolution)
- Investigation engine (multi-artefact, campaign detection, timeline, relationship graph)
- Report generation (4 templates: Technical, Executive, Law Enforcement, Customer)
- REST API with auto-generated Swagger/ReDoc, JWT auth, rate limiting
- Full frontend: 9 pages, evidence graph, timeline, campaign analysis, report builder
- Docker Compose deployment, Kubernetes manifests
- CI/CD via GitHub Actions (4 workflows)

**Completed modules:**
- ML Pipeline (predict.py, train.py)
- Rule Engine (rules.py with 18 patterns)
- OCR Service (ocr.py)
- Pipeline Orchestrator (pipeline/steps/*.py — 12 steps)
- Assessment Engine (evidence, explanation, scoring)
- Reasoning Engine (graph, refinement, decision trace)
- Knowledge Engine (patterns, watchlists, advisories, enrichment)
- Connector Framework (base, manager, registry, Google Safe Browsing, caching)
- Threat Intelligence Fusion (multi-source, conflict resolution)
- Investigation Engine (campaign, timeline, graph, entities, risk)
- Reporting Engine (4 templates, sections, export)
- Authentication (JWT, roles, refresh tokens)
- Security Middleware (rate limiting, body size, security headers, request ID, timeout)
- Frontend (React 19, TypeScript 6, Vite 8, Tailwind v4, Framer Motion)
- Evidence Graph (SVG force layout, zoom/pan/drag, keyboard nav)
- Timeline (grouped by phase, filter by type, search)
- Report Builder (template selection, copy/download/print/share)

**Current maturity assessment:** Beta. Core functionality is implemented but production hardening (observability, error handling, testing coverage, configuration management, documentation accuracy) is incomplete.

## 3. Complete Architecture

### Backend

```
FastAPI Application (main.py)
├── Routers
│   ├── health.py     — /health, /ready, /live, /metrics
│   ├── analyze.py    — /analyze/text, /analyze/image, /analyze/investigation
│   └── auth.py       — /auth/token, /auth/refresh, /auth/verify
├── Pipeline (pipeline/)
│   ├── PipelineRunner — sequential step execution
│   ├── Step base class — AnalysisStep with lifecycle hooks
│   ├── 12 steps: ml_step, rules_step, explanation_step, intelligence_step,
│   │   evidence_step, assessment_step, refinement_step, reasoning_step,
│   │   report_step, knowledge_step, connector_step, fusion_step
│   └── Registry — step ordering and dependency management
├── Services
│   └── Orchestrator — analyze_text() entry point
├── Connectors
│   ├── Base connector class, Manager, Registry
│   ├── Google Safe Browsing connector
│   ├── Mock connector (testing)
│   ├── Cache layer (TTL-based, in-memory)
│   └── Exceptions hierarchy
├── Domains
│   ├── Assessment — evidence building, scoring, explanation, categorization
│   ├── Knowledge — pattern matching, advisory lookup, enrichment
│   ├── Reasoning — decision graph, refinement, evidence chains
│   ├── Investigation — campaign detection, timeline, graph, entities, risk
│   ├── Intelligence — entity extraction, indicators
│   ├── Reporting — sections, templates, export
│   └── Shared — base models, exceptions, utilities
├── Intelligence Data
│   ├── Advisories (RBI, CERT-In, NPCI, banks)
│   ├── Watchlists (domains, emails, phones, UPI)
│   ├── Patterns (known scam patterns)
│   ├── Examples (known scam examples)
│   └── History (past investigations)
├── Core
│   ├── Security (rate limiting, CORS, body size, auth middleware)
│   ├── Auth (JWT, roles, dependencies)
│   ├── Config (13 config modules: pipeline, assessment, auth, connectors, etc.)
│   ├── Constants (categories, indicators, evidence, extraction, domain, labels)
│   ├── Logging (structured JSON, correlation IDs)
│   ├── Metrics (request counting, latency, failure tracking)
│   ├── Middleware (request ID, timeout, rate limiting)
│   ├── Resilience (circuit breaker, retry, timeout)
│   ├── Audit (event logging, auth events)
│   ├── Abuse (rate limiting, API key validation)
│   ├── Calibration (model calibration)
│   ├── Diagnostics (health checks, system info)
│   └── Multilingual (basic language detection)
├── Schemas (Pydantic)
│   ├── Requests (TextAnalysis, InvestigationArtefact)
│   └── Responses (AnalysisResponse, InvestigationResponse, etc.)
├── ML Model (model.joblib + vectorizer.joblib)
├── Dataset (scam_dataset.csv)
└── Config (settings.py — env-based with validation)
```

### Frontend

```
React 19 + TypeScript 6 + Vite 8 + Tailwind v4
├── Pages (9)
│   ├── landing — Marketing page with features, metrics, FAQ
│   ├── text-analysis — Message input form with Zod validation
│   ├── image-analysis — Image upload for OCR analysis
│   ├── analysis-result — Full analysis report view (14 sections)
│   ├── investigation — Multi-panel workspace (3-panel layout)
│   ├── dashboard — System health, metrics, capability listing
│   ├── system-status — Backend diagnostics
│   ├── deployment-health — Deployment monitoring
│   └── not-found — 404 page
├── App
│   ├── Router (lazy-loaded routes, Suspense boundaries)
│   └── Providers (TanStack Query client)
├── Features
│   ├── analysis — Context, hooks, analysis cards (14 components)
│   ├── graph — SVG evidence graph (7 components + layout engine + export)
│   ├── timeline — Investigation timeline (5 components + transform utils)
│   ├── report — Report builder (2 components + 2 utils + templates)
│   ├── investigation — Workspace layout (9 components + hooks + types)
│   ├── demo — Demo cases and walkthrough
│   ├── entity-explorer — Entity browsing and search
│   ├── explainability — "Why was this flagged?" component
│   └── threat-intel — Threat intelligence viewer
├── UI Components (16)
│   ├── button, badge, card, input, textarea, label, skeleton
│   ├── empty-panel, error-panel, page-skeleton, page-transition
│   ├── copy-button, info-row, metric, section, status-badge
│   └── error-boundary, retry-button, toast-container
├── Hooks
│   ├── use-scamshield (6 TanStack Query hooks)
│   └── use-toast
├── Services
│   ├── api (Axios instance with interceptors + diagnostics)
│   └── scamshield (6 API functions)
├── Design
│   ├── tokens (spacing, radius, shadow, typography, animation, layout)
│   └── status (risk/prediction/decision/priority/severity/assessment mappers)
├── Utils
│   ├── cn (Tailwind class merge)
│   ├── validation (Zod schemas)
│   ├── diagnostics (network error recording)
│   └── version
└── Types
    ├── api (AnalysisResponse, HealthResponse, etc.)
    └── index (re-exports)
```

### AI Pipeline

```
Input Text → sanitise_text → PipelineRunner
  1. ML Step (predict.py) — TF-IDF → LogisticRegression → prediction + confidence
  2. Rules Step (rules.py) — 18 regex patterns → rule_score + rule_label + reasons
  3. Explanation Step — category detection, indicator extraction, severity
  4. Intelligence Step — entity extraction (20+ types via regex)
  5. Evidence Step — evidence building, correlation, conflict detection, scoring
  6. Assessment Step — multi-factor scoring → band + confidence + review flags
  7. Refinement Step — rule-based refinement of assessment
  8. Reasoning Step — evidence graph, decision trace, family classification
  9. Report Step — structured report sections
  10. Knowledge Step — knowledge base matching
  11. Connector Step — external connector lookups (Google Safe Browsing)
  12. Fusion Step — multi-source fusion (ML + rules + connectors + knowledge)
```

## 4. Folder Structure

See repository file listing in AUDIT_PREAMBLE. Every major folder is documented with responsibilities in the project README.

## 5. Data Flow

```
Input (text/image)
  → Sanitise (PII masking, validation)
  → Pipeline Runner (sequential 12-step execution)
    → ML Step: TF-IDF → LogisticRegression → scam/safe + confidence
    → Rules Step: 18 regex patterns → score + label + reasons
    → Explanation Step: category, indicators, severity, summary
    → Intelligence Step: entity extraction (URL, phone, email, UPI, etc.)
    → Evidence Step: build evidence items, correlate, detect conflicts, decision score
    → Assessment Step: weighted scoring → assessment_band + confidence + review flags
    → Refinement Step: rule-based adjustments
    → Reasoning Step: evidence graph, decision trace, scam family
    → Report Step: structured sections for each template
    → Knowledge Step: match against patterns, watchlists, advisories
    → Connector Step: external API calls (Google Safe Browsing)
    → Fusion Step: aggregate all sources, resolve conflicts
  → Response (AnalysisResponse with prediction, evidence, entities, risk, assessment)
  → Frontend renders analysis result and investigation workspace
```

## 6. Complete Feature Inventory

### COMPLETE
- ML classification (LogisticRegression, TF-IDF)
- 18 heuristic rule patterns
- Entity extraction (20+ types)
- Multi-factor evidence scoring
- Confidence breakdown (ML/rules/entities/explanation)
- Risk breakdown (credential theft/financial loss/identity theft/malware/social engineering)
- Assessment bands (4 levels with manual review flags)
- OCR text extraction (Tesseract)
- Input sanitisation + PII masking
- REST API with Swagger/ReDoc
- CORS + security headers + rate limiting
- Structured JSON logging with correlation IDs
- Request metrics and diagnostics
- Frontend analysis result page (14 info cards)
- Evidence graph (SVG force layout, 7 node types, 6 edge types)
- Investigation timeline (12 event types, clustering, filtering)
- Campaign analysis (group by scam family, shared entities)
- Report builder (4 templates, copy/download/print/share)
- Demo cases (6 pre-built investigations)
- Docker Compose deployment
- Nginx reverse proxy with security headers + caching
- Kubernetes manifests (deployment, HPA, ingress, configmap)
- GitHub Actions CI/CD (4 workflows)
- JWT authentication (access + refresh tokens, role-based)

### PARTIAL
- Frontend test coverage (20 test files, but only for UI components — no feature tests)
- Knowledge base data (some advisories populated, many patterns are empty)
- Connector framework (only Google Safe Browsing implemented; cache works)
- Threat intelligence fusion (basic aggregation, limited conflict resolution)
- Investigation engine (works but investigation report endpoint is not exposed via frontend)
- Error boundary coverage (basic in frontend, unhandled in many places)
- Multilingual support (basic infrastructure only)
- Model training pipeline (train.py exists but no automated retraining)

### PROTOTYPE
- Calibration module (basic infrastructure, not integrated)
- Deployment health page (exists but likely unused)
- Continuous evaluation script (exists but not integrated into CI)
- Quality dashboard/gate scripts (exist but not integrated)

### PLANNED (from docs)
- Enhanced multilingual support
- Automated model retraining
- Advanced threat intelligence connectors
- Real-time monitoring dashboards
- Mobile SDK
- Browser extension

### DEPRECATED/NOT USED
- middleware/__init__.py (empty directory)
- Several empty evaluation dataset directories (banking, delivery, government, etc.)

## 7. API Inventory

| Endpoint | Method | Purpose | Input | Output | Dependencies |
|---|---|---|---|---|---|
| `/analyze/text` | POST | Analyze text message | `TextAnalysisRequest.text` | `AnalysisResponse` | ML model, rules, pipeline |
| `/analyze/image` | POST | Analyze image via OCR | `UploadFile` (image) | `ImageAnalysisResponse` | Tesseract OCR, pipeline |
| `/analyze/investigation` | POST | Multi-artefact investigation | `InvestigationRequest.artefacts` | `InvestigationResponse` | All domains, connectors |
| `/health` | GET | System health check | None | Health dict | Diagnostics, metrics |
| `/ready` | GET | Readiness probe | None | Ready dict | Diagnostics |
| `/live` | GET | Liveness probe | None | Liveness dict | None |
| `/metrics` | GET | Request metrics snapshot | None | Metrics dict | Metrics collector |
| `/version` | GET | API version info | None | Version dict | Constants |
| `/auth/token` | POST | Get access token | None | `TokenResponse` | JWT config |
| `/auth/token/admin` | POST | Get admin token | None | `TokenResponse` | JWT config, audit |
| `/auth/refresh` | POST | Refresh token | `{refresh_token}` | `TokenResponse` | JWT config |
| `/auth/verify` | POST | Verify token | `{token}` | `{valid, sub, role}` | JWT config |
