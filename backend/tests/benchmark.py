"""Performance benchmark with regression assertions.

Usage:
    python tests/benchmark.py              # run only (no assertions)
    python tests/benchmark.py --check      # run + assert thresholds

Latency thresholds (P95):
  100 req  scam: 2000ms  safe: 1500ms
  500 req  scam: 3500ms  safe: 2500ms
  1000 req scam: 5000ms  safe: 4000ms

Memory regression threshold: 50 MiB peak delta.
"""

import os
import sys
import time
import tracemalloc
from services.orchestrator import analyze_text

SCAM_SAMPLE = (
    "URGENT: Your SBI account will be deactivated. "
    "Update KYC immediately: https://sbi-kyc.xyz"
)
SAFE_SAMPLE = "Good morning. Hope you have a nice day."

# Regression thresholds: (n, p95_ms_scam, p95_ms_safe)
_THRESHOLDS = [
    (100, 2000, 1500),
    (500, 3500, 2500),
    (1000, 5000, 4000),
]
_MEMORY_THRESHOLD_KB = 50 * 1024  # 50 MiB


def _run_batch(text: str, n: int, label: str) -> dict:
    latencies = []
    tracemalloc.start()
    start = time.perf_counter()
    for _ in range(n):
        t0 = time.perf_counter_ns()
        analyze_text(text)
        latencies.append((time.perf_counter_ns() - t0) / 1_000_000)
    elapsed = time.perf_counter() - start
    current, peak = tracemalloc.get_traced_memory()
    tracemalloc.stop()

    latencies.sort()
    avg = sum(latencies) / len(latencies)
    p50 = latencies[len(latencies) // 2]
    p95 = latencies[int(len(latencies) * 0.95)]
    p99 = latencies[int(len(latencies) * 0.99)]

    print(f"\n{'='*60}")
    print(f"  {label} — {n} requests")
    print(f"{'='*60}")
    print(f"  Total time    : {elapsed:.2f}s")
    print(f"  Throughput    : {n / elapsed:.1f} req/s")
    print(f"  Avg latency   : {avg:.1f}ms")
    print(f"  P50           : {p50:.1f}ms")
    print(f"  P95           : {p95:.1f}ms")
    print(f"  P99           : {p99:.1f}ms")
    print(f"  Min           : {min(latencies):.1f}ms")
    print(f"  Max           : {max(latencies):.1f}ms")
    print(f"  Memory delta  : {current / 1024:.0f} KiB")
    print(f"  Memory peak   : {peak / 1024:.0f} KiB")

    return {
        "n": n, "elapsed": elapsed, "avg_ms": avg,
        "p50": p50, "p95": p95, "p99": p99,
        "min_ms": min(latencies), "max_ms": max(latencies),
        "memory_kb": current / 1024, "memory_peak_kb": peak / 1024,
    }


def _run_checks(results: list) -> bool:
    failures = 0
    for r in results:
        for n, scam_thresh, safe_thresh in _THRESHOLDS:
            if r["n"] != n:
                continue
            if "scam" in r.get("label", "").lower():
                if r["p95"] > scam_thresh:
                    print(f"\n  REGRESSION: {r['label']} P95 {r['p95']:.0f}ms > {scam_thresh}ms")
                    failures += 1
            if "safe" in r.get("label", "").lower():
                if r["p95"] > safe_thresh:
                    print(f"\n  REGRESSION: {r['label']} P95 {r['p95']:.0f}ms > {safe_thresh}ms")
                    failures += 1
        if r.get("memory_peak_kb", 0) > _MEMORY_THRESHOLD_KB:
            print(f"\n  REGRESSION: {r['label']} memory peak {r['memory_peak_kb']:.0f} KiB > {_MEMORY_THRESHOLD_KB} KiB")
            failures += 1
    return failures == 0


def main():
    check = "--check" in sys.argv
    print("Warming up (2 iterations)...")
    analyze_text(SCAM_SAMPLE)
    analyze_text(SAFE_SAMPLE)
    print("Warmup complete.")

    results = []
    for n in (100, 500, 1000):
        r1 = _run_batch(SCAM_SAMPLE, n, "Scam text")
        r1["label"] = f"Scam text ({n})"
        results.append(r1)
        r2 = _run_batch(SAFE_SAMPLE, n, "Safe text")
        r2["label"] = f"Safe text ({n})"
        results.append(r2)

    print("\nDone.")

    if check:
        print("\n--- Regression check ---")
        if _run_checks(results):
            print("All benchmarks within thresholds.\n")
        else:
            print("REGRESSION DETECTED — exiting with code 1.\n")
            sys.exit(1)


if __name__ == "__main__":
    main()
