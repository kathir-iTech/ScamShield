# Production Hardening

> Phase 3 Step 2 — Enterprise security, reliability, and resilience.

---

## Threat Model

| Threat | Vector | Mitigation |
|--------|--------|------------|
| Resource exhaustion | Oversized text (>10 KB) | Rejected with `TextTooLargeError` at router |
| Decompression bomb | Crafted image with extreme pixel count | `ImageDecompressionBombError` via dimension/pixel validation |
| Unicode attacks | Zero-width chars, control chars, mixed encodings | NFKC normalisation + character filtering in `utils/validate.py` |
| Regex runaway | Crafted input matching complex patterns | Input size limited before reaching regex engine |
| PII leakage | Exception tracebacks exposing message content | `_mask_pii()` in exception handlers; no `exc_info` in stage failure logs |
| Concurrent model access | Race on `_model` / `_vectorizer` globals | Double-checked locking with `threading.Lock` |
| Image corruption | Truncated file, invalid header, EXIF manipulation | `PIL.Image.verify()`, mode normalisation, dimension checks |
| Temporary file leak | Crash before `os.unlink` | `try/finally` block guarantees cleanup |
| File type spoof | `.exe` with `image/png` content-type | Content-type check + supported type whitelist |
| Pipeline stage crash | One service failure kills entire request | Non-critical stages degrade gracefully via `_try_step()` |

---

## Resilience Strategy

### Fail-Safe Pipeline

```
ML Classification    → critical — failure aborts request
Rule Engine          → critical — failure aborts request
Explanation          → critical — failure aborts request
Threat Intelligence  → non-critical — skips on failure, entities empty
Evidence             → non-critical — skips on failure, default scores
Assessment           → non-critical — skips on failure, assessment defaults
Report               → non-critical — skips on failure, investigation empty
```

Critical stages (ML, Rules, Explanation) must succeed. Non-critical stages produce degraded results when they fail, allowing the pipeline to return a partial analysis.

### Graceful Degradation

When a non-critical stage fails, the corresponding response fields use their dataclass defaults:
- Entity failure → empty entity list, zero summary
- Evidence failure → zero decision score, SAFE level, no evidence
- Assessment failure → zero assessment score, LOW confidence
- Report failure → empty investigation report

### Failure Recovery

| Failure | Recovery |
|---------|----------|
| Model load failure | `ModelLoadError` raised on first request, logged, no retry |
| OCR failure | `ImageExtractionError` returned to client |
| Image corruption | `ImageCorruptedError` with specific message |
| Temp file not deletable | Silently ignored (OS-level cleanup later) |

---

## Resource Management

### Temporary Files

```
routers/analyze.py:
1. NamedTemporaryFile(delete=False) — deterministic naming with safe suffix
2. try/finally guarantees os.unlink()
3. Exception in except handler also calls os.unlink()
4. On Windows, OSError during unlink is silently caught
```

### Memory

- Text capped at 10,000 characters (`MAX_TEXT_LENGTH`)
- Image size capped at `MAX_FILE_SIZE_MB` (default 10 MB)
- Image pixel count capped at 50 megapixels (`_MAX_IMAGE_PIXELS`)
- Image dimension capped at 10,000 px (`_MAX_IMAGE_DIMENSION`)
- `tracemalloc` available for production monitoring

### File Descriptors

- `PIL.Image.open()` → `img.load()` reads data, then closed by GC
- `pytesseract.image_to_string()` writes temp files internally; on Windows these are cleaned by pytesseract
- One temp file per image analysis; guaranteed cleanup

---

## Concurrency Model

### Shared State Audit

| Object | Type | Mutability | Thread-safe |
|--------|------|------------|-------------|
| `predict._model` | joblib object | Immutable after load | Yes — `threading.Lock` double-checked lock |
| `predict._vectorizer` | joblib object | Immutable after load | Yes — same lock |
| `predict._loaded` | bool | Written once | Yes — protected by lock |
| All `_*_REGEXES` | list/tuple of compiled patterns | Immutable after module load | Yes — read-only |
| `core.constants.*` | frozenset/tuple/str | Immutable | Yes — read-only |
| `config.settings.*` | int/float/str | Set at import | Yes — no mutation |
| Service module-level dicts | dict/tuple | Immutable after module load | Yes — read-only |
| `AnalysisResult` instances | dataclass | Per-request | Not shared between requests |

### Recommendations

- Run behind a WSGI server (gunicorn/uvicorn) with `workers=2-4` for CPU-bound parallelism
- The pipeline itself is single-threaded per request; model loading is the only cross-request shared state
- No request-scoped state is shared between concurrent requests
- `_lazy_load()` is idempotent and safe under concurrent calls

---

## Input Defence

### Text Validation (routers/analyze.py → utils/validate.py)

| Check | Method | Error |
|-------|--------|-------|
| Empty text | `strip()` → length check | `EmptyTextError` |
| Length | `len(text) > MAX_TEXT_LENGTH` | `TextTooLargeError` |
| Control characters | Regex `[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]` | Stripped silently |
| Zero-width chars | Regex `[\u200b\u200c\u200d\u2060-\u2064\ufeff]` | Stripped silently |
| Unassigned unicode | Regex `[\ufff0-\uffff\U000e0000-\U0010ffff]` | Stripped silently |
| Mixed newlines | `\n{3,}` → `\n\n` | Normalised |
| Unicode normalisation | `unicodedata.normalize("NFKC")` | Normalised |
| Empty after sanitisation | Length check | `EmptyTextError` |

### Image Validation (ocr.py)

| Check | Method | Error |
|-------|--------|-------|
| Header | `Image.open()` | `ImageCorruptedError` |
| Integrity | `Image.verify()` | `ImageCorruptedError` |
| Pixel count | `width * height > 50M` | `ImageDecompressionBombError` |
| Dimensions | `width|height > 10K` | `ImageDimensionError` |
| Content type | `file.content_type` whitelist | `InvalidImageError` |
| File size | `len(contents) > 10 MB` | `InvalidImageError` |
| Data loading | `img.load()` | `ImageCorruptedError` |
| Colour mode | Convert `L`/`RGB`/`RGBA` only | Normalised to RGB |

---

## Log Sanitisation

### PII Masking

All exception handlers in `main.py` route error messages through `_mask_pii()` before logging:

| Pattern | Replacement |
|---------|-------------|
| `\b\d{10,}\b` | `<REDACTED>` |
| Email addresses | `<EMAIL>` |
| Indian phone numbers | `<PHONE>` |
| "upi" (case-insensitive) | `<UPI>` |
| "otp" (case-insensitive) | `<OTP>` |

### Logging Guidelines

| Do log | Don't log |
|--------|-----------|
| Request ID | Message content |
| Pipeline stage name | OCR extracted text |
| Character count | Phone numbers |
| Processing time | UPI IDs |
| Status code | Email addresses |
| Exception type | Bank account numbers |
| Failure reason | OTP values |
| | Full URLs |

---

## Timeout Strategy

Python's `re` module does not support built-in timeouts. The mitigation strategy is layered:

1. **Input size limits** — Text larger than 10 KB is rejected before reaching regex engines
2. **Pre-compiled patterns** — All regex patterns are compiled at module load, not per-request
3. **Deduplication** — Entity extraction deduplicates values with sets to limit downstream processing
4. **Bounded iteration** — Evidence items capped at 8 supporting + unlimited conflicting
5. **No recursion** — Zero recursive algorithms in the pipeline
6. **No unbounded loops** — All loops iterate over bounded inputs (pre-compiled pattern lists, entity lists, indicator lists)

For production deployments requiring hard timeouts, use an external mechanism:
- **WSGI**: gunicorn `--timeout` for worker-level timeout
- **ASGI**: uvicorn `--timeout-keep-alive` + reverse proxy timeouts (nginx `proxy_read_timeout`)

---

## Security Controls

| Control | Status |
|---------|--------|
| Input length limit | ✓ Enforced at router |
| File size limit | ✓ 10 MB default |
| Image type whitelist | ✓ JPEG/PNG/WebP/BMP |
| Unicode normalisation | ✓ NFKC |
| Control character strip | ✓ All non-printable ASCII |
| Zero-width character strip | ✓ |
| Decompression bomb protection | ✓ 50 MP limit |
| Image verification | ✓ `PIL.Image.verify()` |
| Exception PII masking | ✓ `_mask_pii()` |
| Temp file cleanup | ✓ `try/finally` |
| Path traversal prevention | ✓ `NamedTemporaryFile` (no user-controlled path) |
| No eval/exec | ✓ |
| No shell injection | ✓ |
| CORS | ⚠ Wide open (`*`) — configure for production |

---

## Operational Recommendations

### Deployment

1. Run behind nginx or Cloudflare for TLS termination, rate limiting, and request size checks
2. Use `gunicorn -w 2-4 -t 30` for production (2-4 workers, 30s timeout)
3. Set `SCAMSHIELD_MAX_TEXT_LENGTH` to desired limit (default 10,000)
4. Set `SCAMSHIELD_MAX_FILE_SIZE_MB` to desired limit (default 10 MB)
5. Configure CORS `allow_origins` in `main.py` for your domain

### Monitoring

1. Track `request_id` across all log entries for request correlation
2. Monitor `pipeline step '%s' failed` — indicates service degradation
3. Monitor `ML model loaded` — fires once on first request (or restart)
4. Set up synthetic health checks against `GET /health`
5. Track per-endpoint latency via middleware timing logs

### Known Limitations

1. No rate limiting — implement at reverse proxy level
2. No authentication — API is internal by design
3. No persistent storage — all analysis is ephemeral
4. Regex timeout — mitigated by input size limits; cannot guarantee against adversarial regex slowdown
5. No distributed tracing — request IDs provide correlation within a single process

---

## Benchmark Results

Run `python tests/benchmark.py` in the backend directory.

Expected performance (single core, warm):
| Metric | Scam text | Safe text |
|--------|-----------|-----------|
| P50 latency | ~15-25ms | ~15-25ms |
| P95 latency | ~30-50ms | ~30-50ms |
| Throughput | ~40-60 req/s | ~40-60 req/s |
| Memory/req | <100 KiB | <100 KiB |
