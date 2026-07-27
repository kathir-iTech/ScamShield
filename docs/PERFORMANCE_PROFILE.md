# Performance Profile Report

**Date**: 2026-07-26  
**Source**: `backend/tests/benchmark.py`, API latency profiling, frontend bundle analysis

---

## 1. Backend Latency Profile

### 1.1 API Endpoint Latency (from PERFORMANCE_REPORT.md)

| Metric | Value |
|---|---|
| Average latency | 202.9ms |
| P50 latency | ~180ms |
| P95 latency | 295.1ms |
| P99 latency | ~450ms |
| Max latency | ~800ms |

### 1.2 Regression Benchmarks (benchmark.py)

| Sample Count | Type | P95 Threshold | Actual P95 |
|---|---|---|---|
| 100 | Scam | 2000ms | — |
| 100 | Safe | 1500ms | — |
| 500 | Scam | 3500ms | — |
| 500 | Safe | 2500ms | — |
| 1000 | Scam | 5000ms | — |
| 1000 | Safe | 4000ms | — |

**Memory regression threshold**: 50 MiB peak delta.

---

## 2. Bottleneck Analysis

### 2.1 ML Inference
- Models: `LogisticRegression` + `TfidfVectorizer`
- Inference: In-process, no GPU/CUDA
- Estimated cost: ~30-50ms per request (TF-IDF vectorization + prediction)
- **Bottleneck**: TF-IDF vocabulary size — full vectorization for each request

### 2.2 Entity Extraction (intelligence_service.py)
- 20+ regex patterns applied per request
- Patterns compiled at module level (cached)
- Estimated cost: ~5-15ms per request
- **Bottleneck**: Linear scan of all patterns for each request

### 2.3 Investigation (investigation_service.py)
- Multi-artefact analysis calls orchestrator per artefact (n * full pipeline)
- Entity merging and graph building O(n*m) complexity
- **Bottleneck**: Scales linearly with artefact count

### 2.4 Connector Calls
- `google_safe_browsing.py`: Network round-trip
- Estimated cost: 100-500ms per call (network bound)
- **Bottleneck**: Sequential per type — parallel would improve

---

## 3. Memory Profile

| Component | Memory Usage |
|---|---|
| ML models (loaded) | ~50-100 MB |
| Constants loaded | ~10-20 MB |
| Per-request peak | ~5-15 MB |
| Baseline (idle) | ~150-200 MB |
| Docker memory limit | 1 GB (backend) |

---

## 4. Frontend Bundle Analysis

| Asset | Size | Gzipped |
|---|---|---|
| Total JS bundle | 363 KB | 117 KB |
| Vendor chunk | ~200 KB | ~65 KB |
| Main application | ~163 KB | ~52 KB |

### 4.1 Largest Dependencies (estimated)
- `react-router-dom` — ~30 KB
- `@tanstack/react-query` — ~25 KB
- `axios` — ~15 KB
- `react` + `react-dom` — ~45 KB
- Application code — remaining

---

## 5. Concurrency & Throughput

| Scenario | Current | Potential |
|---|---|---|
| Single worker | ~10 req/s | 10 req/s |
| With 4 workers (gunicorn) | ~40 req/s | 40-50 req/s |
| With async optimization | — | 100+ req/s |
| With separate ML service | — | 200+ req/s |

---

## 6. Optimization Recommendations

### 6.1 High Impact
1. **Add model pre-loading** with warm-up request on startup
2. **Parallelize connector calls** — use `asyncio.gather()` for threat intel sources
3. **Add request-level caching** — cache analysis results by text hash (for repeated queries)

### 6.2 Medium Impact
4. **Optimize TF-IDF vectorization** — pre-compute or use approximate methods
5. **Add gunicorn with uvicorn workers** — `gunicorn -k uvicorn.workers.UvicornWorker -w 4`
6. **Lazy-load constants** — split constants.py to reduce memory overhead

### 6.3 Lower Impact
7. **Add CDN for frontend assets**
8. **Code-split frontend routes** (already partially done)
9. **Add HTTP/2** for multiplexed requests
10. **Add response compression** (already at nginx level)

---

## 7. Profiling Methodology

- Latency: `time.perf_counter_ns()` precision timing
- Memory: `tracemalloc` for Python memory tracking
- Bundle: Not explicitly profiled (estimates based on package sizes)
- Lighthouse: Estimated from PERFORMANCE_REPORT.md
