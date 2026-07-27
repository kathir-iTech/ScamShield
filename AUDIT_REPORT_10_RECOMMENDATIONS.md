# REPORT 10: RECOMMENDATIONS & ROADMAP

## 1. Critical (Immediate — before any production use)

| # | Recommendation | Effort | Impact | Category |
|---|---|---|---|---|
| C1 | **Fix admin token endpoint** — Remove `/auth/token/admin` or gate behind real authentication | 1h | Critical | Security |
| C2 | **Add max_length validation** to text analysis endpoint (char limit) | 30m | High | Security |
| C3 | **Add image dimension validation** to image analysis endpoint | 1h | High | Security |
| C4 | **Implement token revocation** — Add blacklist check for JWT tokens | 4h | High | Security |
| C5 | **Fix domain_manager.py line 1** — Remove or implement SQL comment artifact | 10m | Low | Code quality |
| C6 | **Remove unused Redis dependency** from docker-compose (or wire it up) | 30m | Medium | Correctness |

## 2. High Priority (Next Sprint)

| # | Recommendation | Effort | Impact | Category |
|---|---|---|---|---|
| H1 | **Add comprehensive testing** — Write tests for: pipeline steps, domain services, connectors, frontend features | 40h | High | Reliability |
| H2 | **Add Prometheus metrics format** — Replace plain dict /metrics with Prometheus exposition | 4h | High | Observability |
| H3 | **Add structured error codes** — Replace generic 500 with typed error responses | 8h | High | API quality |
| H4 | **Add per-IP rate limiting** — Move rate limiter to Redis-backed implementation | 12h | Critical | Security |
| H5 | **Add ReDoS protection** — Wrap regex in entity extractor with timeout | 4h | Medium | Security |
| H6 | **Add model integrity check** — SHA-256 checksum verified at startup | 2h | Medium | Security |
| H7 | **Populate empty knowledge base files** — Add scam patterns for job/lottery/investment/impersonation/delivery/loan | 8h | Medium | Accuracy |
| H8 | **Add per-feature error boundaries** on frontend | 4h | Medium | UX |
| H9 | **Add loading/empty states** for all frontend pages and features | 8h | Medium | UX |
| H10 | **Fix .env.example** — Remove unimplemented API keys, add missing config vars | 1h | Low | Documentation |

## 3. Medium Priority (Next 2-3 Sprints)

| # | Recommendation | Effort | Impact | Category |
|---|---|---|---|---|
| M1 | **Replace generic exception handlers** with domain-specific error classes | 8h | Medium | Code quality |
| M2 | **Add distributed tracing** — Integrate OpenTelemetry for pipeline spans | 12h | High | Observability |
| M3 | **Implement per-step timeouts** in pipeline runner | 4h | Medium | Resilience |
| M4 | **Add pipeline step caching** — Skip connector/knowledge steps if same entities analyzed recently | 8h | Medium | Performance |
| M5 | **Add dependency scanning** — `pip-audit` + `npm audit` in CI | 2h | Medium | Security |
| M6 | **Add container image scanning** — Trivy in CI/CD | 2h | Medium | Security |
| M7 | **Add mobile-responsive layout** for graph and investigation panels | 8h | Medium | UX |
| M8 | **Add keyboard focus trapping** for modals and panels | 4h | Medium | Accessibility |
| M9 | **Add skip-to-content link** on all pages | 2h | Low | Accessibility |
| M10 | **Add offline detection** — Graceful degradation when backend unreachable | 4h | Medium | UX |
| M11 | **Add audit log persistence** — Ship logs to file or external sink | 4h | Medium | Compliance |
| M12 | **Convert pipeline to parallel execution model** for independent steps | 12h | Medium | Performance |
| M13 | **Add async file I/O** — Use aiofiles for knowledge base reads | 4h | Medium | Performance |
| M14 | **Implement real connectors** — VirusTotal, WhoisXML, PassiveTotal | 20h | High | Completeness |
| M15 | **Add alerting rules** — Integration with Slack/email for failure alerts | 6h | Medium | Observability |
| M16 | **Add pre-commit hooks** — ruff, mypy, prettier, eslint | 2h | Medium | Code quality |

## 4. Low Priority (Next Release)

| # | Recommendation | Effort | Impact | Category |
|---|---|---|---|---|
| L1 | **Add multi-language support** — Train model on Hindi, Tamil, Telugu, Bengali SMS | 40h+ | High | Completeness |
| L2 | **Implement model retraining pipeline** — Automated retrain + validation | 20h | High | ML Ops |
| L3 | **Add A/B testing framework** — Shadow deploy new models | 16h | Medium | ML Ops |
| L4 | **Add drift detection** — Monitor prediction distribution over time | 8h | Medium | ML Ops |
| L5 | **Create evaluation dataset** — Populate empty directories with curated test cases | 16h | High | Quality |
| L6 | **Add vulnerability disclosure policy** and SECURITY.md | 2h | Medium | Community |
| L7 | **Add contributing guide** (CONTRIBUTING.md) | 4h | Medium | Community |
| L8 | **Add SBOM generation** to CI pipeline | 2h | Low | Compliance |
| L9 | **Optimize Docker images** — Multi-stage builds, .dockerignore | 4h | Medium | Deployment |
| L10 | **Add PodDisruptionBudget** + NetworkPolicy for K8s manifests | 2h | Medium | Deployment |
| L11 | **Switch to uv/pip-tools** for deterministic dependency management | 2h | Low | Reliability |
| L12 | **Wrap entity extractor in strategy pattern** to break up god class | 8h | Medium | Code quality |
| L13 | **Add API version prefix** (e.g., `/v1/analyze/text`) | 4h | Low | API design |

## 5. Proposed Release Roadmap

### v1.1.0 — Production Hardening (4-6 weeks)
- C1, C2, C3, C4, C6 (security fixes)
- H1 (testing — pipeline + domains)
- H2, H3 (observability)
- H4, H5 (rate limiting + ReDoS)
- H8, H9 (frontend robustness)

### v1.2.0 — Completeness (4-6 weeks)
- H7 (populate knowledge base)
- M14 (implement real connectors)
- M4, M12, M13 (performance)
- M1, M16 (code quality)
- H10, M11 (documentation + audit)

### v1.3.0 — ML Operations (4-6 weeks)
- M5, M6 (security scanning)
- L2, L3, L4 (ML pipeline)
- L5 (evaluation dataset)
- M10 (offline support)

### v2.0.0 — Multi-Language + Scale (8-12 weeks)
- L1 (multi-language)
- L9, L10, L13 (deployment)
- Multi-worker Redis support
- Real-time dashboard
- Mobile SDK (planning)

## 6. Executive Summary

**Current strength:** Strong backend domain logic with well-structured pipeline, comprehensive entity extraction, multi-factor assessment, and investigation engine. Frontend is type-safe, well-architected, and visually polished.

**Key weaknesses:**
1. **Security** — Critical auth flaws (admin token, client-asserted roles) must be fixed before any production deployment
2. **Testing** — <10% coverage. Pipeline, domains, connectors all untested.
3. **Observability** — No tracing, no alerting, no Prometheus integration. Debugging production issues will be difficult.
4. **Data quality** — Half the knowledge base is empty. Model is untuned and uncalibrated. No evaluation dataset exists.

**Top 3 actions:**
1. Fix authentication vulnerabilities (admin token endpoint, role validation)
2. Add input validation limits (text length, image dimensions)
3. Write pipeline and domain service tests

The codebase requires an estimated **6-8 weeks of focused engineering** to reach production readiness (v1.1.0). The architecture is sound — the gaps are in hardening, completeness, and operational concerns.
