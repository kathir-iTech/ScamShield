import time
import sys
import os
import statistics

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def generate_text(length: int) -> str:
    base = "Your account has been compromised. Click http://evil.com to verify now. "
    repeats = (length // len(base)) + 1
    return (base * repeats)[:length]

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
    from predict import predict

    text_lengths = [10, 50, 200, 1000]
    n_calls = 100

    texts = {l: generate_text(l) for l in text_lengths}

    print("=== Inference Latency Profiling ===")
    print(f"{'Text Len':<10} {'N':<6} {'Min(ms)':<10} {'Max(ms)':<10} {'Avg(ms)':<10} {'P50(ms)':<10} {'P95(ms)':<10} {'P99(ms)':<10}")
    print("-" * 76)

    all_results = {}

    for length in text_lengths:
        text = texts[length]
        latencies = []

        for i in range(n_calls):
            t0 = time.perf_counter()
            predict(text)
            t1 = time.perf_counter()
            latencies.append((t1 - t0) * 1000)

        avg_ms = statistics.mean(latencies)
        min_ms = min(latencies)
        max_ms = max(latencies)
        p50 = percentile(latencies, 50)
        p95 = percentile(latencies, 95)
        p99 = percentile(latencies, 99)

        all_results[length] = {
            "min": min_ms, "max": max_ms, "avg": avg_ms,
            "p50": p50, "p95": p95, "p99": p99
        }

        print(f"{length:<10} {n_calls:<6} {min_ms:<10.2f} {max_ms:<10.2f} {avg_ms:<10.2f} {p50:<10.2f} {p95:<10.2f} {p99:<10.2f}")

    first_text = texts[10]
    t0 = time.perf_counter()
    predict(first_text)
    t1 = time.perf_counter()
    cold_start_ms = (t1 - t0) * 1000

    print()
    print(f"First call (cold start, includes model load): {cold_start_ms:.2f} ms")
    print(f"Subsequent calls (warm):                      {all_results[10]['avg']:.2f} ms avg")

if __name__ == "__main__":
    main()
