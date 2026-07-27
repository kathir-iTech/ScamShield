# ScamShield Master Audit — Report 02: Architecture Review

**Date:** 2026-07-26

Every subsystem reviewed on 10 dimensions. Scores out of 10.

---

## 1. Orchestrator (`orchestrator.py` — 283 lines)

| Dimension | Score | Notes |
|-----------|-------|-------|
| Purpose | 9 | Clear: coordinate 12 pipeline stages |
| Strengths | | Linear pipeline with timing, graceful degradation via `_try_step` |
| Weaknesses | | `asdict()` serializes entire dataclass at each stage — repeated work. No async parallelism. Stage 5+ stages marked as "try" (non-fatal) but stage 1-3 are fatal — inconsistent |
| Coupling | 4 | Direct imports to every service module. Knows internal field names of every service |
| Maintainability | 6 | Adding a stage = new import + new `_step_*` function + new call in `_run_pipeline` |
| Scalability | 3 | Synchronous, single-threaded. 12 stages × text length = O(n) per request |
| Performance | 5 | ~200ms average, but `asdict()` is called on 90+ field dataclass multiple times |
| Security | 7 | No security issues in orchestrator itself |
| Extensibility | 5 | New stages require modifying orchestrator; no plugin architecture |
| Complexity | 6 | 283 lines, well-structured but tightly coupled |

**Overall: 5.5/10**

---

## 2. ML Service (`ml_service.py` + `predict.py` — 7 + 43 lines)

| Dimension | Score | Notes |
|-----------|-------|-------|
| Purpose | 8 | Clear: wrap model prediction |
| Strengths | | Simple, fast inference (~45ms average) |
| Weaknesses | | `ml_service.py` is a 7-line pass-through — adds zero value. `predict.py` loads model on import (module-level side effect). No error handling for missing model |
| Coupling | 5 | Direct sklearn dependency |
| Maintainability | 7 | Trivial, but the 7-line wrapper should be eliminated |
| Scalability | 3 | In-process model. No GPU support. No model serving |
| Performance | 7 | 45ms average is fast |
| Security | 4 | Pickle deserialization of joblib files |
| Complexity | 9 | Minimal complexity |

**Overall: 5.5/10**

---

## 3. Rule Engine (`rules.py` + `rules_service.py` — 172 + 27 lines)

| Dimension | Score | Notes |
|-----------|-------|-------|
| Purpose | 9 | Clear: heuristic scam detection |
| Strengths | | 4 check functions cover OTP, urgency/money, links, service keywords. Weighted scoring, capping at 100 |
| Weaknesses | | `rules_service.py` is a 27-line pass-through. Duplicate regex patterns with `intelligence_service.py` (OTP patterns, bank lists, government references). `check_service_keywords` redefines lists already in `core/constants.py` (banks, payment apps, govt refs) |
| Coupling | 5 | Imports constants directly |
| Maintainability | 6 | Duplicate data is a maintenance risk |
| Scalability | 7 | Simple linear checks, fast |
| Performance | 8 | ~5-10ms |
| Complexity | 8 | Straightforward |

**Overall: 6.5/10**

---

## 4. Entity Intelligence (`intelligence_service.py` — 382 lines)

| Dimension | Score | Notes |
|-----------|-------|-------|
| Purpose | 9 | Clear: extract 20 types of entities from text |
| Strengths | | Comprehensive extractors. Module-level compiled regex for performance. Dedup with seen-set pattern. Risk classification per entity type |
| Weaknesses | | All functions return `List[Dict]` instead of typed objects. String-typed entity types (no enum). OCR metadata parameter exists but is unused (`ocr_metadata: dict = None`). `analyze()` function is a 20-call sequential block |
| Coupling | 6 | Heavily dependent on `core/constants.py` for all regex patterns and risk maps |
| Maintainability | 6 | 382 lines, repeated seen-set pattern ~20 times |
| Scalability | 7 | Each request scans 20 regexes |
| Performance | 7 | ~10-20ms for text < 10K chars |
| Complexity | 7 | Straightforward extraction logic |

**Overall: 6.8/10**

---

## 5. Evidence Service (`evidence_service.py` — 445 lines)

| Dimension | Score | Notes |
|-----------|-------|-------|
| Purpose | 8 | Build evidence from ML, rules, entities; detect correlations/conflicts |
| Strengths | | Maps entity types to scam indicators. Correlates pairs of evidence types. Conflict detection. Confidence breakdown calculation |
| Weaknesses | | 445 lines is long. `build_evidence()` is a single monolithic function (not broken into helpers). Imports 45+ constants from core/constants.py |
| Coupling | 5 | Tightly coupled to constants for every evidence type string |
| Maintainability | 5 | Monolithic function, heavy constant imports |
| Performance | 6 | O(n*m) correlation checks |
| Complexity | 6 | Moderate complexity |

**Overall: 5.5/10**

---

## 6. Assessment Service (`assessment_service.py` — 204 lines)

| Dimension | Score | Notes |
|-----------|-------|-------|
| Purpose | 9 | Weighted scoring from ML, rules, evidence, indicators, entities |
| Strengths | | Clean weighted formula. Conflict penalty. Manual review triggers. Well-documented thresholds |
| Weaknesses | | None significant |
| Coupling | 7 | Imports settings constants, but that's appropriate |
| Maintainability | 8 | Good |
| Performance | 8 | Fast |
| Complexity | 8 | Straightforward math |

**Overall: 7.5/10**

---

## 7. Refinement Engine (`refinement_service.py` — 701 lines)

| Dimension | Score | Notes |
|-----------|-------|-------|
| Purpose | 8 | Mitigate FP/FN through post-processing rules |
| Strengths | | 13 refinement rules with dataclass-based rule definitions. Condition functions are lambdas. Decision stability analysis |
| Weaknesses | | **701 lines** — second largest service. `_evaluate_rules` is complex. Rules use string matching on assessment bands — brittle. Some rules have duplicative logic (e.g., FP_Rule_05, FP_Rule_06 both check "Investigation" band) |
| Coupling | 5 | Knows internal field names of assessment, evidence, reasoning |
| Maintainability | 4 | Too long, complex lambda rules hard to debug |
| Performance | 6 | 13 rules evaluated per request |
| Complexity | 4 | High complexity due to interaction of 13 rules |

**Overall: 5.0/10**

---

## 8. Reasoning Engine (`reasoning_service.py` — 646 lines)

| Dimension | Score | Notes |
|-----------|-------|-------|
| Purpose | 8 | Build evidence graph, classify scam family |
| Strengths | | EvidenceNode + EvidenceEdge dataclasses. Graph construction. Weighted family classification. Dominant evidence chain extraction |
| Weaknesses | | 646 lines. Complex interaction between graph building, family scoring, chain extraction. `_classify_family()` uses hardcoded indicator-to-family mappings |
| Coupling | 5 | Tight to constants for family definitions |
| Maintainability | 5 | High complexity, long function chains |
| Performance | 5 | Graph construction O(n²) for n evidence items |
| Complexity | 4 | Most complex service |

**Overall: 5.0/10**

---

## 9. Knowledge Engine (`knowledge_service.py` — 826 lines)

| Dimension | Score | Notes |
|-----------|-------|-------|
| Purpose | 8 | Match analysis results against known intelligence (watchlists, advisories, history) |
| Strengths | | Three matching backends (exact, prefix/suffix, Levenshtein). Dataclass-based KnowledgeMatch. Comprehensive `enrich_analysis()` function |
| Weaknesses | | **826 lines — largest backend file**. `enrich_analysis()` is a 300+ line function. Entity type mapping is hardcoded. `enrich_investigation_result()` duplicates some logic |
| Coupling | 5 | Tight to intelligence schemas |
| Maintainability | 4 | Single monolithic function |
| Performance | 5 | Levenshtein on every entity for every request is O(n*m) |
| Complexity | 4 | High |

**Overall: 4.5/10**

---

## 10. Investigation Engine (`investigation_service.py` — 696 lines)

| Dimension | Score | Notes |
|-----------|-------|-------|
| Purpose | 9 | Multi-artefact investigation with campaign detection |
| Strengths | | Well-structured with dataclasses (InvestigationArtefact, MergedEntity, TimelineEvent, CampaignIndicators, InvestigationResult). Clear step functions. Campaign scoring with weighted formula |
| Weaknesses | | 696 lines. Each artefact runs full pipeline (12 stages × n artefacts = expensive). Relationship graph limited to 30 nodes/40 edges. No pagination |
| Coupling | 6 | Calls `analyze_text()` from orchestrator — dependency on full pipeline |
| Maintainability | 6 | Long but well-structured |
| Scalability | 3 | O(n × pipeline) — doesn't scale with artefact count |
| Performance | 3 | n artefacts × ~200ms each = expensive |
| Complexity | 6 | Moderate |

**Overall: 5.5/10**

---

## 11. Connector Framework (`connectors/*` — 946 total lines)

| Dimension | Score | Notes |
|-----------|-------|-------|
| Purpose | 9 | Plugin-based threat intel connector architecture |
| Strengths | | Clean abstract base class. Manager with lifecycle. Registry for source registration. Cache layer. Configuration-driven |
| Weaknesses | | Only 1 real connector (Google Safe Browsing). Mock connector for testing. No circuit breaker. No rate limiting per connector |
| Coupling | 8 | Low — abstract base isolates implementations |
| Maintainability | 8 | Well-structured |
| Scalability | 6 | Currently sequential; `CONNECTOR_PARALLELISM` config exists but not verified in implementation |
| Performance | 5 | Network call per connector adds latency |
| Security | 5 | API key in env var |
| Extensibility | 8 | Adding new connector = implement base class + register |

**Overall: 7.0/10**

---

## 12. Threat Intelligence Fusion (`threat_intelligence_service.py` — 334 lines)

| Dimension | Score | Notes |
|-----------|-------|-------|
| Purpose | 9 | Fuse results from multiple threat intel sources |
| Strengths | | Dedup, clustering, agreement/conflict scoring, evidence ranking, conflict resolution by source weight. Dataclass-based FuseResult |
| Weaknesses | | Only 2 sources configured (Google SB + mock). Agreement score may be misleading with few sources |
| Coupling | 7 | Depends on config settings for source weights |
| Maintainability | 7 | Well-structured |
| Performance | 7 | Fast — pure computation |
| Complexity | 7 | Moderate |

**Overall: 7.0/10**

---

## 13. Frontend Architecture

| Dimension | Score | Notes |
|-----------|-------|-------|
| Purpose | 9 | SPA for scam analysis with multiple views |
| Strengths | | Feature-based organization. Lazy-loaded routes. React Query for server state. TypeScript strict. 17 UI primitives |
| Weaknesses | | No client state management (no Zustand/Redux). Toast system uses module-level counter. No E2E tests. Error boundary not per-route. Dashboard feature dir is empty |
| Coupling | 6 | Tight to API response shapes (90+ field AnalysisResponse) |
| Maintainability | 7 | Well-organized |
| Scalability | 5 | Bundle grows linearly with feature count |
| Performance | 6 | 363KB gzip 117KB bundle. Lazy loading helps |
| Security | 5 | No auth, no CSP in nginx |
| Extensibility | 7 | Adding page = add route + lazy import |

**Overall: 6.5/10**

---

## 14. Infrastructure Architecture

| Dimension | Score | Notes |
|-----------|-------|-------|
| Purpose | 8 | Docker, K8s, Nginx for deployment |
| Strengths | | Docker Compose with security hardening. K8s with HPA. Nginx with rate limiting. 5 CI workflows |
| Weaknesses | | No database. No secrets management. No monitoring stack. CORS wide open. Security scans use `continue-on-error: true` |
| Maintainability | 6 | Config files are simple |
| Scalability | 5 | HPA exists but backend is synchronous — no async workers |
| Performance | 5 | Single node, no caching layer |
| Security | 4 | CORS wildcard, env secrets, no network policies |

**Overall: 5.0/10**
