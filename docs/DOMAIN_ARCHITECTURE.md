# Domain Architecture

## Overview

The domain decomposition splits the monolithic `backend/services/` into seven cohesive domain packages under `backend/domains/`. Each domain owns its models, business logic, and public API. Oversized services are refactored to ≤250 lines by delegating to their respective domain packages.

## Domain Map

```
backend/domains/
├── shared/            # Base models, constants, utilities
│   ├── public.py      # Re-exports everything
│   ├── constants.py   # All shared constants (split from core/constants.py)
│   ├── models.py      # KnowledgeMatch, AdvisoryMatch, HistoricalMatch,
│   │                  #   EvidenceNode, EvidenceEdge, ReasoningResult,
│   │                  #   RefinementResult, RefinementRule
│   ├── utils.py       # normalise(), levenshtein(), digits_only(), domain_from_url()
│   └── exceptions.py  # DomainError, NotFoundError
│
├── knowledge/         # Knowledge base matching & enrichment
│   ├── public.py      # enrich_analysis(), enrich_investigation_result(), search_by_indicator()
│   ├── matcher.py     # Matching algorithms (_is_match)
│   ├── search.py      # Search by URL/domain/phone/email/UPI/bank/QR/keywords/family
│   ├── advisory.py    # Advisory matching, historical correlation
│   ├── enrichment.py  # Entity enrichment orchestration
│   └── service.py     # KnowledgeService class + get_service() singleton
│
├── reasoning/         # Reasoning engine & refinement rules
│   ├── public.py      # reason(), refine(), check_decision_stability(), get_all_rules()
│   ├── graph.py       # Evidence graph, decision trace, family classification
│   └── refinement.py  # FP/FN detection rules, score adjustment
│
├── intelligence/      # Entity extraction from text
│   ├── public.py      # analyze(), extract_* functions (18 extractors)
│   ├── extractors.py  # URL/phone/email/UPI/bank/OTP/IP/social/etc. extractors
│   └── service.py     # analyze() orchestration
│
├── assessment/        # Risk assessment, evidence, explanation
│   ├── public.py      # assess(), build_evidence(), generate_explanation(), etc.
│   ├── evidence.py    # Evidence collection, correlation, conflict detection, scoring
│   ├── explanation.py # Category detection, severity, explanation generation
│   └── service.py     # assess() function
│
├── investigation/     # Multi-artefact investigation
│   ├── public.py      # investigate()
│   ├── models.py      # InvestigationArtefact, MergedEntity, TimelineEvent, etc.
│   ├── entities.py    # Entity validation, normalisation, merging
│   ├── timeline.py    # Timeline event building
│   ├── campaign.py    # Campaign detection
│   ├── graph.py       # Relationship graph
│   ├── risk.py        # Global risk computation
│   └── service.py     # investigate() orchestration
│
└── reporting/         # Report generation
    ├── public.py      # generate_report(), generate_investigation_report()
    ├── sections.py    # Report section builders (executive summary, findings, etc.)
    └── service.py     # generate_report() function
```

## Dependency Direction

```
shared  ←  domains  ←  services  ←  pipeline  ←  routers
  │           │            │             │
  └───────────┴────────────┴─────────────┘
  (all layers import from shared)

Allowed:
  shared → (no dependencies)
  domains → shared
  services → domains, shared
  pipeline → services, domains, shared
  routers → services, pipeline, domains, shared

Forbidden:
  Any domain → routers
  Any domain → pipeline
  Domain ↔ Domain circular imports
```

## Refactored Services

| Original | Lines | Refactored | Domain Package |
|----------|-------|------------|----------------|
| `knowledge_service.py` | 826 | 38 lines (facade) | `domains/knowledge/` |
| `investigation_service.py` | 604 | 37 lines (facade) | `domains/investigation/` |
| `refinement_service.py` | 599 | 35 lines (facade) | `domains/reasoning/` |
| `reasoning_service.py` | 583 | 16 lines (facade) | `domains/reasoning/` |
| `report_service.py` | 389 | 14 lines (facade) | `domains/reporting/` |
| `evidence_service.py` | 382 | 22 lines (facade) | `domains/assessment/` |
| `intelligence_service.py` | 337 | 29 lines (facade) | `domains/intelligence/` |
| `threat_intelligence_service.py` | 334 | 3 files ≤150 each | `services/threat_intelligence_service/` (package) |

## Removed Pass-Through Wrappers

| File | Reason | Callers Updated |
|------|--------|-----------------|
| `services/ml_service.py` | No abstraction value — `predict.predict()` | `pipeline/steps/ml_step.py` |
| `services/rules_service.py` | No abstraction value — `rules.*` | `pipeline/steps/rules_step.py` |
| `services/ocr_service.py` | No abstraction value — `ocr.*` | `routers/analyze.py` |

## Shared Models Consolidation

Previously duplicated across multiple services, now in `domains/shared/models.py`:
- `KnowledgeMatch`, `AdvisoryMatch`, `HistoricalMatch` (was in `knowledge_service.py`)
- `EvidenceNode`, `EvidenceEdge`, `ReasoningResult` (was in `reasoning_service.py`)
- `RefinementResult`, `RefinementRule` (was in `refinement_service.py`)

Previously duplicated utility functions, now in `domains/shared/utils.py`:
- `normalise()` — NFKC normalise + lower + strip
- `levenshtein()` — edit distance
- `digits_only()` — extract digits from string
- `domain_from_url()` — extract domain from URL

## Extension Guide

### Adding a new domain

```
backend/domains/mydomain/
├── __init__.py
├── public.py       # Public API exports
├── models.py       # Domain-specific data models
└── service.py      # Business logic
```

1. Create the directory under `backend/domains/`
2. Implement models, service, and any helper modules
3. Export public symbols via `public.py`
4. Create a thin facade in `backend/services/my_service.py` if backward compat needed
5. Update `core/constants.py` if adding new constants (or add to `domains/shared/constants.py`)

### Adding a new pipeline step

Create a new step class in `backend/pipeline/steps/` and register it in `services/orchestrator.py`.

### Adding a new entity extractor

Add the function to `domains/intelligence/extractors.py` and export it from `domains/intelligence/public.py`.

## Architecture Tests

Located in `tests/architecture/test_architecture.py`:

| Test | What it verifies |
|------|------------------|
| `test_no_service_exceeds_250_lines` | No service file >250 lines (except `__init__.py`) |
| `test_no_circular_imports` | All domain/service/pipeline modules import cleanly |
| `test_each_domain_has_public_py` | Every domain package exports via `public.py` |
| `test_no_pass_through_wrappers_remain` | Wrapper files removed |
| `test_domain_dependency_direction` | No domain imports from routers or pipeline |
| `test_core_constants_not_imported_by_domains` | Domains use `domains.shared.constants`, not `core.constants` |
