# ScamShield X — Architecture Vision

## Philosophy

ScamShield has excellent engineering for its current stage. The architecture is clean, the code is typed, the tests are comprehensive. But the project is at an inflection point: it needs to decide whether to stay a research prototype or evolve into a production product.

ScamShield X is the architecture vision for the production product. It is not a rewrite — it's a strategic evolution that keeps what works, replaces what doesn't, and adds what's missing.

---

## Keep (90% of backend, 80% of frontend)

| Component | Why Keep | Changes Needed |
|-----------|----------|----------------|
| Layered architecture | Clean separation of concerns | None |
| Domain-driven package structure | Works well, easy to navigate | None |
| FastAPI + Pydantic | Battle-tested, well-integrated | None |
| Rule engine | 50+ rule categories, production-hardy | Version rules, make impacts configurable |
| Connector framework | Circuit breaker, retry, parallel execution | Make parallelism configurable |
| Evaluation framework | 4 modes, HTML reports, regression | None |
| Investigation engine | Unique multi-message analysis | Add unit tests |
| CI/CD workflows | 5 well-crafted pipelines | Add deploy step |
| Docker containers | Hardened, non-root, health checks | Add secrets mount |
| Frontend service layer | Clean API abstraction | None |
| Error response format | Consistent across all endpoints | None |
| Structured logging | JSON + correlation IDs | None |
| Security middleware | Headers, CORS, rate limiting | None |

## Redesign (5% of backend)

| Component | Current | ScamShield X | Why |
|-----------|---------|--------------|-----|
| Pipeline orchestrator | 12 sequential steps, Dict[str, Any] context | DAG-based with typed step interfaces | Parallel execution, type safety, pluggable steps |
| ML model | Static TF-IDF + LR, 52% FPR | Ensemble: LR + shallow NN + LLM judge | Dramatically improved accuracy |
| Auth system | Custom JWT, disabled by default | python-jose + API keys, always-on | Security, auditability |
| Response model | 55-field AnalysisResponse | Tiered: SafeResponse / ScamResponse / InvestigationResponse | Cleaner API, smaller payloads |

## Simplify (5% of codebase)

| Component | Current | ScamShield X | Why |
|-----------|---------|--------------|-----|
| Exception hierarchy | 20 classes across 2 files | 10 classes in 1 file | Eliminate duplication |
| FP/FN rules | 16 hardcoded rules in refinement.py | 16 configurable rules in settings | Tunable without code changes |
| Configuration profiles | 5 profiles, env vars at import | 3 profiles + runtime config reload | Fewer profiles, dynamic config |

## Remove (2% of codebase)

| Component | Current | ScamShield X | Why |
|-----------|---------|--------------|-----|
| RateLimitMiddleware | Dead code in core/security.py | — | Superseded, unused |
| domains/shared/exceptions.py | Duplicate file | — | Use core/exceptions.py |
| evaluation_v2.py | Duplicate evaluation logic | — | Use evaluation_runner.py |
| Tests that assert True | 6 audit tests | — | Remove or fix |
| `"arte facts"` typo | Wrong key in report JSON | — | Fix |

## Add (new infrastructure)

| Component | Purpose | Priority |
|-----------|---------|----------|
| **SQLite → PostgreSQL** | Persistent storage for analyses, users, watchlists, audit log | P0 |
| **Prometheus metrics** | request count, latency, error rate by endpoint, FPR monitor | P0 |
| **Grafana dashboards** | Real-time visibility into system health | P0 |
| **Model retraining API** | Trigger retraining on new scam data | P1 |
| **Response caching (Redis)** | Avoid re-analyzing identical messages | P1 |
| **Batch analysis API** | Upload CSV, get bulk results | P2 |
| **PWA manifest + service worker** | Installable mobile experience | P2 |
| **WebSocket for real-time analysis** | Live streaming of pipeline progress | P2 |
| **OpenTelemetry tracing** | End-to-end request tracing | P2 |

---

## Target Architecture (ScamShield X)

```
┌─────────────────────────────────────────────────────────┐
│                      Frontend (React + TS)               │
│  Analysis UI │ Investigation UI │ Reports │ Dashboard   │
└──────────────────────────┬──────────────────────────────┘
                           │ HTTPS
┌──────────────────────────▼──────────────────────────────┐
│                      API Gateway (Nginx)                  │
│                   TLS termination │ Rate limiting         │
└──────────────────────────┬──────────────────────────────┘
                           │
┌──────────────────────────▼──────────────────────────────┐
│                 FastAPI Application                       │
│                                                          │
│  ┌─────────┐ ┌──────────┐ ┌────────┐ ┌──────────────┐  │
│  │ Auth    │ │ Pipeline │ │ Eval   │ │ Admin        │  │
│  │ Router  │ │ Router   │ │ Router │ │ Router       │  │
│  └────┬────┘ └────┬─────┘ └───┬────┘ └──────┬───────┘  │
│       │           │           │              │          │
│  ┌────▼───────────▼───────────▼──────────────▼───────┐  │
│  │              Service Layer                          │  │
│  │  AnalysisSvc │ InvestigationSvc │ ReportSvc │      │  │
│  └──────────────────────┬────────────────────────────┘  │
│                         │                                │
│  ┌──────────────────────▼────────────────────────────┐  │
│  │         Orchestration (DAG-based pipeline)         │  │
│  │  ┌─────┐ ┌─────┐ ┌──────┐ ┌─────┐ ┌──────────┐  │  │
│  │  │Lex  │→│Entity│→│Rules │→│ML   │→│Refinement│  │  │
│  │  └─────┘ └─────┘ └──────┘ └─────┘ └──────────┘  │  │
│  │  ┌────────┐ ┌──────────┐ ┌────────┐ ┌─────────┐  │  │
│  │  │Connect │→│Reasoning │→│Evidence│→│Reporting │  │  │
│  │  └────────┘ └──────────┘ └────────┘ └─────────┘  │  │
│  └──────────────────────┬────────────────────────────┘  │
│                         │                                │
│  ┌──────────────────────▼────────────────────────────┐  │
│  │              Domain Layer                           │  │
│  │  Assessment │ Reasoning │ Knowledge │ Intelligence │  │
│  └──────────────────────┬────────────────────────────┘  │
│                         │                                │
│  ┌──────────────────────▼────────────────────────────┐  │
│  │           Infrastructure Layer                      │  │
│  │  Config │ Auth │ Metrics │ Logging │ Security     │  │
│  └──────────────────────┬────────────────────────────┘  │
└─────────────────────────┼──────────────────────────────┘
                          │
┌─────────────────────────▼──────────────────────────────┐
│                   Data Layer                             │
│  ┌──────────┐ ┌───────────┐ ┌────────┐ ┌───────────┐  │
│  │PostgreSQL│ │   Redis   │ │  ML    │ │ Object    │  │
│  │          │ │  (Cache)  │ │ Model  │ │ Storage   │  │
│  └──────────┘ └───────────┘ └────────┘ └───────────┘  │
└─────────────────────────────────────────────────────────┘
                          │
┌─────────────────────────▼──────────────────────────────┐
│              External Connectors                         │
│  VirusTotal │ PhishTank │ GSB │ URLScan │ IpQuality   │
└─────────────────────────────────────────────────────────┘
```

## Migration Strategy

Do NOT rewrite. Migrate incrementally:

1. **Week 1-2**: Fix FPR, fix clean_text, add persistence (SQLite)
2. **Week 3-4**: Add monitoring (Prometheus + Grafana), add cache (Redis/disk)
3. **Week 5-6**: Refactor pipeline to DAG, refactor auth to python-jose
4. **Week 7-8**: Add model retraining, add batch API, complete K8s manifests
5. **Week 9-12**: Add PWA, add E2E tests, performance optimization

Each step is independently deployable and reversible.

## Principles

| Principle | What It Means |
|-----------|---------------|
| **Data-driven, not hardcoded** | Every threshold, weight, and rule impact comes from config or data |
| **Persist everything** | No in-memory-only state except caches |
| **Type-safe end to end** | Typed step contracts, typed API responses, typed persistence |
| **Observable by default** | Every request is traced, measured, logged, and alertable |
| **Defense in depth** | Auth always-on, secrets managed, TLS everywhere |
| **Incremental, not Big Bang** | Every change is independently deployable and reversible |

## What ScamShield X Unlocks

| Capability | Enabler | Impact |
|-----------|---------|--------|
| Sub-10% FPR | Ensemble model + configurable rules + retraining | Product actually usable |
| User retention | Persistence → accounts → history | Users come back |
| Enterprise sales | Persistent audit trail, batch API, SLA | Revenue |
| Mobile reach | PWA + share intent | Users on devices where scams happen |
| Community contributions | Typed step contracts, plugin architecture | Faster innovation |
| 24/7 reliability | Monitoring, alerting, auto-scaling | Trust |
