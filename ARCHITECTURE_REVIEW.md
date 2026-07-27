# Architecture Review

## Backend Architecture — Score: 8/10

### Purpose
Process text/image inputs through 12 sequential pipeline stages to produce a structured scam assessment.

### Strengths
- Clean FastAPI middleware stack with 6 well-defined layers
- 12-step pipeline with declarative dependency resolution via `StepRegistry`
- Domain-driven design with clear separation (assessment, reasoning, reporting, intelligence)
- Centralized configuration with 5 deployment profiles
- Comprehensive exception hierarchy (20+ exception classes)
- Structured JSON logging with correlation IDs
- In-memory metrics with latency percentiles

### Weaknesses
- 12 sequential steps for a single analysis create high latency (avg 57-113ms)
- Some steps mutate shared pipeline context in-place (side effects)
- Pipeline step execution order uses hardcoded priorities rather than dynamic dependency graph
- `PipelineResult` has 64 fields — many empty for safe/low-risk messages
- Exception propagation in pipeline is opaque: `except PipelineError: raise` loses context

### Coupling
- **Tight**: Pipeline steps reference shared context dict with string keys — no typed contracts between steps
- **Loose**: Domains are well-separated with public API facades

### Maintainability: 8/10
- Excellent modularity and typing. The 12-step pipeline is easy to modify or reorder. Some duplication between `core/exceptions.py` and `domains/shared/exceptions.py`.

### Scalability: 7/10
- Stateless FastAPI — horizontally scalable behind load balancer
- No persistent state — all analysis is ephemeral
- No caching between pipeline stages (each request re-extracts entities, re-queries connectors)

### Performance
- P95 latency: 14.8ms (fast hardware) — 91.9ms (avg hardware) across 162 samples
- Pipeline is synchronous sequential — no parallel step execution
- Model loading is lazy (first request pays cold-start penalty)

### Security: 8/10
- Security headers, rate limiting, CORS, request body limits, PII masking
- Custom JWT implementation (non-standard, no RSA/ECDSA support)
- Auth disabled by default

### Complexity: 7/10
- 107 source files, 12 pipeline steps, 17 entity extractors, 16 refinement rules
- Some functions are too large (e.g., `assess()` in `service.py` is 158 lines, `_classify_family` in `graph.py` is ~150 lines)

---

## Frontend Architecture — Score: 8/10

### Purpose
Provide a polished web interface for scam analysis, investigation, and system monitoring.

### Strengths
- React 19 + TypeScript 6 strict mode
- Lazy-loaded pages with Suspense boundaries
- Custom UI component library (17 components)
- Feature modules (Timeline, Graph, Report, Analysis) are well-separated
- Clean service layer for API communication
- Error boundaries at page level
- Comprehensive test suite (Vitest, 16 test files)

### Weaknesses
- No E2E/Playwright tests
- No i18n infrastructure
- Bundle size gate at 512 KB may be aggressive for feature growth
- `frontend/README.md` is still the Vite default template

### Complexity: 6/10
- Multiple redundant UI patterns (accordion, tabs, buttons, etc. are built custom instead of using shadcn/ui or similar)
- 17 custom UI components where a library would reduce maintenance

---

## AI Pipeline — Score: 6/10

### Purpose
Classify messages as scam or safe using ML + heuristic rules.

### Strengths
- TF-IDF (5000 features, 1-2 ngrams) + Logistic Regression with `class_weight="balanced"`
- 80/20 stratified train/test split
- Deterministic and fast inference (sub-millisecond)

### Weaknesses
- **Static model** — trained once, never retrained. No active learning pipeline.
- **No embedding model** — TF-IDF is a bag-of-words approach, missing semantic understanding
- **Text cleaning destroys entities** — `clean_text()` in `utils/text.py` strips all non-alphanumeric characters including dots from URLs, @ from emails, + from phones
- **52% FPR** is unacceptable for production — system is overly aggressive
- No model versioning or A/B testing support
- No confidence calibration (model outputs raw probabilities, not calibrated scores)

---

## Reasoning Engine — Score: 7/10

### Purpose
Classify scam family, build evidence graph, generate decision trace.

### Strengths
- Sophisticated family taxonomy (6 families: Credential Theft, Payment Fraud, Social Engineering, etc.)
- Evidence graph with typed nodes and weighted edges
- Decision trace for explainability
- FP/FN refinement rules (16 rules)

### Weaknesses
- `_classify_family()` is 150+ lines of hardcoded keyword matching
- Evidence graph generates synthetic edges that may reference non-existent nodes
- No deduplication of evidence edges
- Family classification accuracy is not measured independently

---

## Knowledge Engine — Score: 5/10

### Purpose
Match message entities against known threat indicators (watchlists, advisories).

### Strengths
- Fuzzy matching with configurable Levenshtein threshold
- Multi-type matching (domains, URLs, phones, emails, UPIs, keywords)
- Cached lookups

### Weaknesses
- **No persistent storage** — watchlists are in-memory only, rebuilt on restart
- Knowledge benchmark has only **12 samples** — cannot measure accuracy
- No scheduled updates for watchlists
- No integration with external threat intel feeds (AlienVault, AbuseIPDB, etc.)
- Advisory matching is rudimentary (presence/absence only, no confidence scoring)

---

## Connector Framework — Score: 8/10

### Purpose
Query external threat intelligence services for enrichment.

### Strengths
- Clean ABC with `BaseConnector`
- Auto-discovery via `ConnectorRegistry`
- Caching with TTL
- Retry logic with configurable backoff
- Parallel lookups with timeout
- Graceful degradation (connector failure doesn't block pipeline)

### Weaknesses
- Only 2 connectors (Google Safe Browsing + Mock)
- Connector parallelism limited to 4 simultaneously
- Google Safe Browsing API key embedded in URL query parameter (potential logging leak)
- No connector health SLA tracking

---

## Threat Intelligence Fusion — Score: 7/10

### Purpose
Merge evidence from multiple connectors and sources into a unified assessment.

### Strengths
- Deduplication of evidence
- Conflict detection between sources
- Agreement computation
- Evidence ranking (primary, supporting, weak, contradictory)

### Weaknesses
- Only fuses connector results — does not incorporate external threat intel feeds
- Evidence ranking is based on simple count heuristics
- No integration with STIX/TAXII for structured threat intel

---

## Investigation Engine — Score: 6/10

### Purpose
Analyze multiple related messages (artefacts) for campaign detection, timeline reconstruction, and entity merging.

### Strengths
- Campaign detection across messages
- Timeline reconstruction with event clustering
- Cross-message entity merging
- Multi-artefact risk scoring

### Weaknesses
- **No dedicated unit tests** — only tested via evaluation framework
- Entity merging uses simple name/type matching, no fuzzy matching across artefacts
- Campaign detection thresholds are arbitrary
- `domains/investigation/` module exists but was not fully audited (files not found in backend/)

---

## Deployment Architecture — Score: 7/10

### Strengths
- Docker + docker-compose with security hardening
- 5 GitHub Actions CI/CD workflows
- Release automation (tag → build → push → GitHub Release)
- Production Nginx config with TLS, rate limiting, caching
- Kubernetes manifests for orchestration

### Weaknesses
- **K8s is preview quality** — missing PVC, PDB, NetworkPolicy, Secrets, ServiceAccount
- No CD pipeline (builds images but doesn't deploy)
- No environment-specific deployment workflows
- No monitoring stack (Prometheus/Grafana)
- No log aggregation (ELK/Loki)
- No secrets management (API keys in .env files)
