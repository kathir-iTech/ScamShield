# Technical Debt

Status after the security / product / ops / accuracy upgrade. Items that were
closed by that work are listed under **Resolved**; everything else is live
debt, ordered by severity.

---

## Resolved

| # | Item | Resolution |
|---|------|-----------|
| 2 | **`clean_text()` destroys entities** | `utils/text.py` now normalises through a safe-character whitelist; covered by `tests/unit/test_text_entities.py` |
| 3 | **No persistent storage** | SQLite storage layer in `core/storage/` (WAL, repositories, 9 tables) with users, sessions, audit and rate-limit state |
| 6 | **Custom JWT implementation, no revocation** | Refresh tokens are persisted and individually revocable; logout-all revokes the whole set. Retaining the in-repo signer is a recorded decision — see `ENGINEERING_DECISIONS.md` §4 |
| 8a | **No retraining signal** | Scheduled evaluation (`core/eval_scheduler.py`), CI gold-set gate (`evaluation/scripts/ci_gate.py`) and an active-learning label queue now exist. The retraining *API* is still open — see #36 |
| 30 | **No frontend E2E tests** | `frontend/e2e/feedback.e2e.ts`, `frontend/e2e/recovery.e2e.ts` |
| — | **No auth, no audit trail** | Accounts, sessions, API keys, audit log, abuse/rate limiting and security headers are in place (`tests/security/`, 176 tests) |
| — | **Docs exposed in production** | `DocsRouteGuardMiddleware` gates `/docs`, `/redoc`, `/openapi.json` when `ENVIRONMENT` is `production` or `staging` |
| — | **CSP missing `frame-ancestors` / `object-src`** | CSP and HSTS (incl. `preload`) completed in `core/security.py` |
| — | **Global rate limiter clobbered per-route headers** | `X-RateLimit-*` written with `setdefault` so route budgets win |
| — | **SQLite write lock deadlock** | Thread-local connections, lock-free reads, `RLock` held across `BEGIN … COMMIT` |
| — | **No secrets management for local dev** | `.env.production` blanked and gitignored; examples document required keys |

## Critical

| # | Item | Location | Impact | Recommendation |
|---|------|----------|--------|---------------|
| 1 | **FPR 14.06% / Recall 77.2% on the 308-sample gold set** | `rules.py`, `refinement.py`, `service.py` | Roughly 1 in 7 safe messages still flagged; 1 in 4 scams missed | **Do not re-tune against the existing gold set** — collect more labelled data first (`datasets/gold/`), then sweep. See `MODEL_STATUS.md` |

## High

| # | Item | Location | Impact | Recommendation |
|---|------|----------|--------|---------------|
| 4 | **Duplicate exception hierarchy** | `core/exceptions.py` + `domains/shared/exceptions.py` | ~70 lines duplicated, import confusion | Delete `domains/shared/exceptions.py`, re-export from `core/exceptions.py` |
| 5 | **Dead code: `RateLimitMiddleware`** | `core/security.py` | Unused class, superseded by `abuse.py` | Remove or delegate to `SlidingWindowRateLimitMiddleware` |
| 7 | **`AnalysisResponse` has 55 fields** | `schemas/responses.py` | Large response, many empty fields for safe messages | Split into tiered response model (safe/minimal, scam/full) |
| 9 | **K8s preview quality** | `k8s/` | Missing PVC, Secrets, PDB, NetworkPolicy, ServiceAccount | Complete production K8s manifests |
| 10 | **No secrets manager** | `.env.example`, `docker-compose.yml` | Secrets supplied by environment only; no rotation path | Integrate with a secrets manager before multi-env deployment |
| 36 | **No retraining API** | `train.py` | Retraining is manual despite scheduled evaluation | Expose a guarded, audited endpoint or run retraining as a job |
| 37 | **Rate-limit state is per-instance SQLite** | `core/storage/repositories.py` | Behind multiple replicas each replica has its own budget — limits are not global | Back the limiter with Redis (`core/cache.py` already exists) before scaling out |
| 38 | **No password reset / recovery** | `routers/accounts.py` | A user who forgets a password is permanently locked out | Add time-limited reset tokens over an email channel |
| 39 | **No account lockout** | `routers/auth.py` | Only sliding-window throttling; no exponential backoff or lockout on repeated failures | Add failure counters with progressive delay, audited |

## Medium

| # | Item | Location | Impact | Recommendation |
|---|------|----------|--------|---------------|
| 11 | **`PipelineContext` uses `Dict[str, Any]`** | `pipeline/context.py` | No type safety between pipeline steps | Define typed step contracts |
| 12 | **Hardcoded refinement multiplier (0.15)** | `refinement.py` | Arbitrary FP/FN impact calculation | Make configurable or data-driven |
| 13 | **Hardcoded ML evidence weight (20)** | `evidence.py` | Not configurable | Move to config/settings |
| 14 | **Tests that assert `True`** | `test_audit.py` | 6 tests verify nothing | Add real assertions |
| 15 | **`validation_v1.json` field name mismatch** | `evaluation/datasets/validation_v1.json` | Dataset uses wrong field names | Standardize field names to match schema |
| 16 | **`evaluate_classification()` duplicates `evaluation_runner.py`** | `core/evaluation_v2.py` | Two implementations of same evaluation logic | Consolidate into one |
| 17 | **No unit tests for ML model** | `predict.py` | `predict()` function untested | Add unit tests with synthetic test cases |
| 18 | **No unit tests for investigation domain** | `domains/investigation/` | Multi-message analysis logic untested | Add dedicated unit tests |
| 19 | **No unit tests for knowledge domain** | `domains/knowledge/` | Watchlist matching, fuzzy search untested | Add dedicated unit tests |
| 20 | **No unit tests for reasoning graph** | `domains/reasoning/graph.py` (538 lines) | 538 lines of untested logic | Add unit tests for family classification, evidence graph |
| 21 | **Connector parallelism limited to 4** | `connectors/manager.py` | Only 4 connectors queried simultaneously | Make configurable |
| 22 | **`"arte facts"` typo in JSON key** | `reporting/sections.py` | Produces malformed report output | Fix typo to `"artefacts"` |
| 23 | **`diagnostics.py` has wrong pipeline stage count** | `core/diagnostics.py` | Lists 7 stages, actual pipeline has 12 | Update to match actual pipeline |
| 24 | **6 audit tests with `assert True`** | `tests/security/test_audit.py` | Waste of CI time | Replace with real assertions or remove |
| 25 | **Quality dashboard score is arbitrary** | `scripts/quality_dashboard.py` | `_score_quality()` has no calibration basis | Derive score from actual benchmark targets |
| 40 | **Audit log has no retention/rotation** | `core/audit.py` | Grows without bound; no purge policy for compliance | Add age-based retention with an audited purge |
| 41 | **Refresh tokens never expire from storage** | `core/auth/token_store.py` | Revoked/expired rows accumulate indefinitely | Periodic sweep of expired rows |
| 42 | **SQLite single-writer limits horizontal scale** | `core/storage/db.py` | One writer per database file | Move to PostgreSQL before running more than one app replica against the same data |

## Low

| # | Item | Location | Impact | Recommendation |
|---|------|----------|--------|---------------|
| 26 | **Default `ENVIRONMENT = "development"`** | `core/config/security.py` | Production might run in dev mode | Use safer default or fail at startup |
| 27 | **Static salt for API key hashing** | `core/api_keys.py` | Weakens API key security | Use per-key random salt |
| 28 | **Predictable admin token subject** | `routers/auth.py` | `f"admin_{int(time.time())}"` is guessable | Use `secrets.token_hex()` |
| 29 | **Knowledge benchmark has 12 samples** | `evaluation/datasets/knowledge_benchmark.json` | Insufficient for accuracy measurement | Expand to 100+ samples |
| 31 | **No Dependabot/Renovate config** | `.github/` | Security vulnerabilities may go unnoticed | Add automated dependency update workflow |
| 32 | **`frontend/README.md` is default Vite template** | `frontend/README.md` | Misleading for new contributors | Customize with project-specific content |
| 33 | **Tamil Unicode range incomplete** | `core/multilingual.py` | Missing Grantha characters used in Tamil | Expand range to cover full Tamil Unicode block |
| 34 | **Google Safe Browsing API key in URL param** | `connectors/google_safe_browsing.py` | Key may be logged in URLs | Use `Authorization` header instead |
| 35 | **No `aud` claim in JWT** | `core/auth/jwt.py` | Tokens can be used against any service | Add audience validation |
| 43 | **WhatsApp / Telegram / Android channels are docs-only** | `scaffolds/` | Three of four planned channels have no implementation | Implement against `docs/CHANNEL_CONTRACTS.md` once provider credentials exist |
| 44 | **Extension is unsigned and unpublished** | `extension/` | Cannot be installed from a store; manual loading required | Package and sign for Web Store distribution |
| 45 | **CI workflow files blocked by token scope** | `.github/workflows/` | Push rejected without the GitHub `workflow` scope | Re-grant the token, or push these files from an authenticated session |

## Summary

| Severity | Count | Estimated Effort |
|----------|-------|-----------------|
| Critical | 1 | Data collection, not code |
| High | 9 | 3-4 weeks |
| Medium | 18 | 3-4 weeks |
| Low | 11 | 1-2 weeks |
| Resolved | 11 | — |
| **Open total** | **39** | **7-10 weeks** |
