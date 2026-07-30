import time
import sys
import os
import statistics

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def percentile(data, p):
    if not data:
        return 0.0
    sorted_data = sorted(data)
    k = (p / 100.0) * (len(sorted_data) - 1)
    f = int(k)
    c = f + 1
    if f >= len(sorted_data):
        return sorted_data[-1]
    return sorted_data[f] + (k - f) * (sorted_data[c] - sorted_data[f])

def main():
    from fastapi.testclient import TestClient
    from main import app

    n_calls = 50
    text = "Your account has been compromised. Click http://evil.com to verify now."
    payload = {"text": text}
    latencies = []

    with TestClient(app) as client:
        for i in range(n_calls):
            t0 = time.perf_counter()
            response = client.post("/analyze/text", json=payload)
            t1 = time.perf_counter()
            elapsed = (t1 - t0) * 1000
            latencies.append(elapsed)

            if response.status_code != 200:
                print(f"Request {i} failed: {response.status_code} {response.text[:200]}")

    avg_ms = statistics.mean(latencies)
    min_ms = min(latencies)
    max_ms = max(latencies)
    p50 = percentile(latencies, 50)
    p95 = percentile(latencies, 95)
    p99 = percentile(latencies, 99)

    print("\n=== API Latency Profiling (/analyze/text) — AFTER WARMUP ===")
    print(f"{'Metric':<15} {'Value (ms)':<15}")
    print("-" * 30)
    print(f"{'Min':<15} {min_ms:<15.2f}")
    print(f"{'Max':<15} {max_ms:<15.2f}")
    print(f"{'Avg':<15} {avg_ms:<15.2f}")
    print(f"{'P50':<15} {p50:<15.2f}")
    print(f"{'P95':<15} {p95:<15.2f}")
    print(f"{'P99':<15} {p99:<15.2f}")
    print(f"{'N':<15} {len(latencies):<15}")

if __name__ == "__main__":
    main()
