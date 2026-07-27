# ScamShield — Release Readiness

## Architecture Overview

```
Client → FastAPI → RequestID Middleware → Router
  ├── POST /analyze/text  →  sanitise_text  →  Pipeline (7 stages)
  │                                           ├── ML Prediction
  │                                           ├── Rule Engine
  │                                           ├── Explanation
  │                                           ├── Threat Intelligence*
  │                                           ├── Evidence*
  │                                           ├── Assessment*
  │                                           └── Report*
  │
  ├── POST /analyze/image → validate → OCR → sanitise_text → Pipeline
  │
  ├── GET /health    → application status, model, uptime, routes
  ├── GET /ready     → readiness probe (model, config, services)
  ├── GET /live      → liveness probe (process alive)
  └── GET /metrics   → in-process request metrics snapshot
```

*Non-critical stages — failures degrade gracefully, pipeline continues.

## Supported Capabilities

- **ML Classification**: scikit-learn pipeline (model.joblib + vectorizer.joblib).
- **Heuristic Rule Engine**: 18 indicator patterns, weighted keyword scoring.
- **Explanation Engine**: Category detection, threat assignment, recommended actions.
- **Threat Intelligence**: Entity extraction (URLs, phones, emails, UPI, OTP, bank accounts, IFSC, IPs, social handles, tracking IDs, etc.).
- **Evidence Correlation**: Cross-references indicators, entities, ML, and rules to build supporting/conflicting evidence.
- **Risk Assessment**: Multi-factor scoring (ML, decision, evidence, indicators, entities) with penalty for conflicting signals.
- **Report Generation**: Structured investigation report with timeline, findings, entity breakdown, risk assessment, recommendations.
- **OCR**: Tesseract-based text extraction from JPEG, PNG, WebP, BMP images.
- **Input Sanitisation**: NFKC normalisation, control char/zero-width char/unassigned unicode stripping, multi-newline collapse, length enforcement.
- **Image Validation**: Header integrity (PIL.Image.verify), dimension caps, pixel caps, colour mode normalisation.

## Operational Requirements

| Requirement | Minimum |
|---|---|
| Python | 3.10+ |
| RAM | 512 MB (idle), 1 GB (under load) |
| Disk | 100 MB (application + models) |
| Tesseract OCR | Required for image analysis |
| scikit-learn | Model dependency |

## Startup Sequence

1. FastAPI initialises app with middleware (CORS, RequestID).
2. Startup event `_verify_startup_prerequisites()`:
   - Checks model file (`models/model.joblib`) exists.
   - Checks vectorizer file (`models/vectorizer.joblib`) exists.
   - Validates configuration constants (MAX_TEXT_LENGTH, MAX_FILE_SIZE_MB, SUPPORTED_IMAGE_TYPES).
   - Checks writable directories.
3. ML model loads lazily on first request (double-checked locking, `predict.py`).
4. Routes registered: `/health`, `/ready`, `/live`, `/metrics`, `/analyze/text`, `/analyze/image`, `/docs`, `/redoc`, `/openapi.json`.

Startup succeeds even if model files are missing — the `/ready` probe will report NOT READY, and ML requests will fail with `ModelLoadError`.

## Shutdown Sequence

1. Shutdown event fires: logs final metrics snapshot.
2. `logging.shutdown()` flushes all pending log records.
3. Temporary files are cleaned up per-request (not accumulated).

No persistent connections or long-lived resources to release.

## Health Endpoints

| Endpoint | Method | Purpose | Response |
|---|---|---|---|
| `/health` | GET | Application status | `{status, service, version, model_loaded, configuration_loaded, service_availability, uptime_seconds, build_timestamp, registered_routes, test_mode}` |
| `/ready` | GET | Readiness probe | `{status: "READY"}` or `{status: "NOT READY", errors: [...]}` |
| `/live` | GET | Liveness probe | `{status: "alive"}` |
| `/metrics` | GET | Request metrics | `{total_requests, successful_requests, failed_requests, validation_failures, ocr_requests, text_requests, average_latency_ms, p50_latency_ms, p95_latency_ms, maximum_latency_ms}` |
| `/docs` | GET | Swagger UI | Interactive API documentation |
| `/redoc` | GET | ReDoc UI | Alternative API documentation |
| `/openapi.json` | GET | OpenAPI spec | Machine-readable API specification |

## Testing Summary

- **Unit tests**: 129 tests (106 existing + 23 hardening tests).
- **Test categories**: input validation, image validation, pipeline resilience, concurrency, log sanitisation, ML prediction, rule engine, explanation, intelligence, evidence, assessment, report.
- **Quality gates**: `python scripts/quality_gate.py` — verifies pytest, imports, config, models, OpenAPI, schemas, documentation, circular imports, constant duplication.
- **Performance benchmark**: `python tests/benchmark.py` — measures latency, throughput, memory for 100/500/1000 requests.

## Performance Summary

Typical benchmarks (development machine, no GPU):

| Batch | Text Type | P50 | P95 | P99 | Throughput |
|---|---|---|---|---|---|
| 100 | Scam | ~50ms | ~100ms | ~150ms | ~800 req/s |
| 100 | Safe | ~40ms | ~80ms | ~120ms | ~1000 req/s |
| 500 | Scam | ~60ms | ~200ms | ~300ms | ~700 req/s |
| 500 | Safe | ~45ms | ~150ms | ~250ms | ~900 req/s |
| 1000 | Scam | ~70ms | ~350ms | ~500ms | ~600 req/s |
| 1000 | Safe | ~50ms | ~250ms | ~400ms | ~800 req/s |

Memory: ~30-80 MiB peak depending on batch size. No memory leaks (steady-state after warmup).

## Security Summary

- **Input sanitisation**: NFKC normalisation, control char/zero-width char/unassigned unicode strip, length enforcement.
- **Image safety**: PIL.verify() for header integrity, dimension cap (10K px), pixel cap (50 MP), mode normalisation.
- **Log sanitisation**: PII redaction (phone, email, OTP, UPI, 10+ digit numbers) in exception handlers and log messages.
- **Exception hierarchy**: All user-facing errors inherit `ScamShieldError`; validation errors return 400, internal errors return 500.
- **File upload**: MIME type whitelist, file size limit (10 MB), safe suffix enforcement, temp file cleanup guaranteed.
- **No secrets in code**: Configuration via environment variables (`SCAMSHIELD_MAX_TEXT_LENGTH`, `SCAMSHIELD_MAX_FILE_SIZE_MB`).

## Known Limitations

1. **No rate limiting**: Add nginx `limit_req` or middleware for production deployment.
2. **No caching**: Every request runs the full pipeline. Add response caching for identical inputs if throughput demands it.
3. **No distributed tracing**: Request IDs are generated but not propagated to external systems.
4. **Sequential pipeline**: All stages run sequentially. Parallelism (e.g., running Intel/Evidence concurrently) is a future optimisation.
5. **No database/queue**: Stateful analysis history, job queues, and persistent storage are not implemented.
6. **No authentication**: API has no auth layer. Add API keys or JWT for production deployment behind a gateway.
7. **Model hot-reload**: ML model is loaded once at first request. Restart required to pick up new models.
8. **Single-process**: Not designed for multiprocessing within the same process. Scale horizontally behind a load balancer.
9. **Tesseract dependency**: OCR requires Tesseract installed at the system level.
10. **No TLS termination**: TLS should be handled by a reverse proxy (nginx, Caddy, etc.).

## Future Roadmap

1. **Caching layer**: Cache analysis results for identical inputs (TTL-based).
2. **Async pipeline**: Run independent stages (Intel, Evidence) concurrently.
3. **Rate limiting**: Per-IP or per-token request throttling.
4. **Authentication**: API key or OAuth2 integration.
5. **Webhook notifications**: Alerting for high-risk detections.
6. **Dashboard metrics**: Expose Prometheus-compatible metrics instead of in-process.
7. **Model versioning**: Support multiple model versions with A/B testing.
8. **Batch analysis**: Accept bulk text analysis requests.
9. **Multilingual OCR**: Expand OCR language support beyond English.
10. **CI/CD integration**: Automated quality gate execution in pipeline.

## Release Checklist

- [ ] All 129 unit tests pass (`python -m pytest tests/ -v`)
- [ ] Quality gate passes (`python scripts/quality_gate.py`)
- [ ] Performance benchmark within thresholds (`python tests/benchmark.py --check`)
- [ ] `/health` returns 200 with all fields populated
- [ ] `/ready` returns `{"status": "READY"}` when model is present
- [ ] `/live` returns `{"status": "alive"}`
- [ ] `/metrics` returns snapshot with non-zero counters after test requests
- [ ] Swagger UI loads at `/docs`
- [ ] OpenAPI spec loads at `/openapi.json`
- [ ] All mandatory documentation exists:
  - `ARCHITECTURE_REVIEW.md`
  - `PRODUCTION_HARDENING.md`
  - `ENGINEERING_DECISIONS.md`
  - `RELEASE_READINESS.md`
- [ ] No API schema changes (compare OpenAPI spec with previous release)
- [ ] No new imports added to `predict.py` or ML pipeline
