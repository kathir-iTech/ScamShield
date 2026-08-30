# Roadmap

## Immediate (Weeks 1-2)

| # | Item | Rationale | Impact | Effort | Priority |
|---|------|-----------|--------|--------|----------|
| 1 | **Fix 52% FPR** | System is unusable — half of safe messages flagged as scam | Critical | 3-5 days | P0 |
| 2 | **Fix `clean_text()` entity destruction** | URLs, emails, phones stripped before extraction | High | 1 day | P0 |
| 3 | **Delete duplicate exceptions** | 70 lines duplicate code | Low | 30 min | P1 |
| 4 | **Fix `"arte facts"` typo** | Produces broken report JSON | Medium | 15 min | P1 |
| 5 | **Fix diagnostics pipeline count** | Lists 7 stages, actual pipeline has 12 | Low | 15 min | P1 |

## Short-Term (Weeks 3-6)

| # | Item | Rationale | Impact | Effort | Priority |
|---|------|-----------|--------|--------|----------|
| 6 | **Add SQLite persistence** | Foundation for user accounts, history, audit trail | High | 3-5 days | P0 |
| 7 | **Add real assertions to 6 audit tests** | Remove tests that assert `True` | Low | 1 hour | P1 |
| 8 | **Add ML model unit tests** | Core AI logic has 0 tests | High | 1-2 days | P1 |
| 9 | **Add investigation domain unit tests** | 538-line untested reasoning graph | High | 2-3 days | P1 |
| 10 | **Add knowledge domain unit tests** | Watchlist matching untested | Medium | 1 day | P1 |
| 11 | **Add Prometheus metrics endpoint** | Foundation for monitoring | High | 1-2 days | P0 |
| 12 | **Add monitoring stack (Prometheus + Grafana)** | See what's happening in production | High | 2-3 days | P0 |

## Medium-Term (Weeks 7-12)

| # | Item | Rationale | Impact | Effort | Priority |
|---|------|-----------|--------|--------|----------|
| 13 | **Replace custom JWT with python-jose** | Standard library, audited, safe | Medium | 1-2 days | P1 |
| 14 | **Parallelize pipeline** | 12 sequential steps could run in parallel | High | 3-5 days | P1 |
| 15 | **Add response caching** | Many repeat queries (same domain, same message) | Medium | 2-3 days | P1 |
| 16 | **Add E2E tests (Playwright)** | Catch integration bugs before release | High | 3-5 days | P1 |
| 17 | **Complete K8s production manifests** | PVC, Secrets, PDB, NetworkPolicy | High | 2-3 days | P2 |
| 18 | **Add Dependabot for auto-dependency updates** | Security hygiene | Medium | 1 hour | P2 |
| 19 | **Add batch analysis API** | Upload CSV of messages for bulk check | Medium | 2-3 days | P2 |
| 20 | **Add retraining API** | ML model learns from new scam data | High | 3-5 days | P1 |

## Long-Term (Months 3-6)

| # | Item | Rationale | Impact | Effort | Priority |
|---|------|-----------|--------|--------|----------|
| 21 | **Add mobile app (SMS integration)** | Reach users at point of scam | High | 2-3 months | P2 |
| 22 | **Add browser extension** | Check links while browsing | High | 1-2 months | P2 |
| 23 | **Add multi-region deployment** | Global availability and DR | High | 1-2 months | P3 |
| 24 | **Replace ML model with LLM-based detection** | Dramatically improve accuracy for complex scams | Transformative | 1-2 months | P1 |
| 25 | **Open-source community program** | Contributors, security researchers, translators | Medium | Ongoing | P3 |

## Prioritization Framework

```
Priority   | Criteria
-----------|--------------------------------------------------
P0 (block) | Production cannot launch without this
P1 (must)  | Production should not launch without this
P2 (should)| Important but not blocking launch
P3 (could) | Nice to have, post-MVP
```

## Dependencies

```
Fix FPR ──────────► Retrain ML ──► Improve recall ──► LLM model
                          │
                          ▼
              Add retraining API
              
SQLite ──► User accounts ──► History ──► Audit trail
    │                                        │
    ▼                                        ▼
Batch API                          Law enforcement reports

Monitoring ──► Alerts ──► SLA dashboards
```

## Total Effort Estimate

| Phase | Weeks | Estimated Engineering Hours |
|-------|-------|---------------------------|
| Immediate | 1-2 | 40-60 hours |
| Short-term | 3-6 | 80-120 hours |
| Medium-term | 7-12 | 160-240 hours |
| Long-term | 13-24 | 400-600 hours |
| **Total** | **6 months** | **680-1020 hours** |

## Risk Assessment

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|------------|
| FPR fix introduces new FNs | High | High | Holdout evaluation set, regression checks |
| SQLite becomes bottleneck | Medium | Medium | Use migrations, design for PostgreSQL swap |
| LLM model is too expensive | Medium | High | Tiered approach: ML for simple, LLM for complex |
| Contributors don't join | Medium | Medium | Focus on automation, not community |
