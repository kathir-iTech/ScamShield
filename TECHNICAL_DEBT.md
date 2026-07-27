# Technical Debt

## Critical

| # | Item | Location | Impact | Recommendation |
|---|------|----------|--------|---------------|
| 1 | **52% False Positive Rate** | `rules.py`, `refinement.py`, `service.py` | Produces unusable results — nearly half of safe messages flagged as scam | Recalibrate rule weights, adjust thresholds, improve FP refinement rules |
| 2 | **`clean_text()` destroys entities** | `utils/text.py:4-9` | Strips dots from URLs, @ from emails, + from phones before entity extraction | Move entity extraction before text cleaning, or use a more selective cleaner |
| 3 | **No persistent storage** | Entire backend | All analysis is ephemeral — no history, no audit trail, no user data | Add SQLite (MVP) or PostgreSQL (production) |

## High

| # | Item | Location | Impact | Recommendation |
|---|------|----------|--------|---------------|
| 4 | **Duplicate exception hierarchy** | `core/exceptions.py` + `domains/shared/exceptions.py` | ~70 lines duplicated, import confusion | Delete `domains/shared/exceptions.py`, re-export from `core/exceptions.py` |
| 5 | **Dead code: `RateLimitMiddleware`** | `core/security.py:40-80` | Unused class, superseded by `abuse.py` | Remove or update to delegate to `SlidingWindowRateLimitMiddleware` |
| 6 | **Custom JWT implementation** | `core/auth/jwt.py` | Non-standard, no RSA/ECDSA, no revocation, no leeway | Replace with `python-jose` or `PyJWT` |
| 7 | **`AnalysisResponse` has 55 fields** | `schemas/responses.py` | Large response, many empty fields for safe messages | Split into tiered response model (safe/minimal, scam/full) |
| 8 | **Static ML model** | `predict.py`, `train.py` | Model never retrained, no learning from new scams | Add retraining API + scheduled retraining |
| 9 | **K8s preview quality** | `k8s/` | Missing PVC, Secrets, PDB, NetworkPolicy, ServiceAccount | Complete production K8s manifests |
| 10 | **No secrets management** | `.env.example`, `docker-compose.yml` | API keys in plaintext files | Integrate with secrets manager |

## Medium

| # | Item | Location | Impact | Recommendation |
|---|------|----------|--------|---------------|
| 11 | **`PipelineContext` uses `Dict[str, Any]`** | `pipeline/context.py` | No type safety between pipeline steps | Define typed step contracts |
| 12 | **Hardcoded refinement multiplier (0.15)** | `refinement.py:536,557` | Arbitrary FP/FN impact calculation | Make configurable or data-driven |
| 13 | **Hardcoded ML evidence weight (20)** | `evidence.py:160` | Not configurable | Move to config/settings |
| 14 | **Tests that assert `True`** | `test_audit.py:25-54` | 6 tests verify nothing | Add real assertions |
| 15 | **`validation_v1.json` field name mismatch** | `evaluation/datasets/validation_v1.json` | Dataset uses wrong field names, incompatible with validation framework | Standardize field names to match schema |
| 16 | **`evaluate_classification()` duplicates `evaluation_runner.py`** | `core/evaluation_v2.py` + `evaluation/evaluation_runner.py` | Two implementations of same evaluation logic | Consolidate into one |
| 17 | **No unit tests for ML model** | `predict.py` | `predict()` function untested | Add unit tests with synthetic test cases |
| 18 | **No unit tests for investigation domain** | `domains/investigation/` | Multi-message analysis logic untested | Add dedicated unit tests |
| 19 | **No unit tests for knowledge domain** | `domains/knowledge/` | Watchlist matching, fuzzy search untested | Add dedicated unit tests |
| 20 | **No unit tests for reasoning graph** | `domains/reasoning/graph.py` (538 lines) | 538 lines of untested logic | Add unit tests for family classification, evidence graph |
| 21 | **Connector parallelism limited to 4** | `connectors/manager.py:108` | Only 4 connectors queried simultaneously | Make configurable |
| 22 | **`"arte facts"` typo in JSON key** | `reporting/sections.py:319` | Produces malformed report output | Fix typo to `"artefacts"` |
| 23 | **`diagnostics.py` has wrong pipeline stage count** | `core/diagnostics.py:90` | Lists 7 stages, actual pipeline has 12 | Update to match actual pipeline |
| 24 | **6 audit tests with `assert True`** | `tests/security/test_audit.py` | Waste of CI time | Replace with real assertions or remove |
| 25 | **Quality dashboard score is arbitrary** | `scripts/quality_dashboard.py:108-116` | `_score_quality()` has no calibration basis | Derive score from actual benchmark targets |

## Low

| # | Item | Location | Impact | Recommendation |
|---|------|----------|--------|---------------|
| 26 | **Default `ENVIRONMENT = "development"`** | `core/config/security.py:11` | Production might run in dev mode | Use safer default or fail at startup |
| 27 | **Static salt for API key hashing** | `core/api_keys.py:10` | Weakens API key security | Use per-key random salt |
| 28 | **Predictable admin token subject** | `routers/auth.py:23` | `f"admin_{int(time.time())}"` is guessable | Use `secrets.token_hex()` |
| 29 | **Knowledge benchmark has 12 samples** | `evaluation/datasets/knowledge_benchmark.json` | Insufficient for accuracy measurement | Expand to 100+ samples |
| 30 | **No frontend E2E tests** | `frontend/` | Integration bugs may reach production | Add Playwright tests for critical flows |
| 31 | **No Dependabot/Renovate config** | `.github/` | Security vulnerabilities may go unnoticed | Add automated dependency update workflow |
| 32 | **`frontend/README.md` is default Vite template** | `frontend/README.md` | Misleading for new contributors | Customize with project-specific content |
| 33 | **Tamil Unicode range incomplete** | `core/multilingual.py:4` | Missing Grantha characters used in Tamil | Expand range to cover full Tamil Unicode block |
| 34 | **Google Safe Browsing API key in URL param** | `connectors/google_safe_browsing.py:226` | Key may be logged in URLs | Use `Authorization` header instead |
| 35 | **No `aud` claim in JWT** | `core/auth/jwt.py` | Tokens can be used against any service | Add audience validation |

## Summary

| Severity | Count | Estimated Effort |
|----------|-------|-----------------|
| Critical | 3 | 3-5 days |
| High | 7 | 2-3 weeks |
| Medium | 15 | 3-4 weeks |
| Low | 10 | 1-2 weeks |
| **Total** | **35** | **7-10 weeks** |
