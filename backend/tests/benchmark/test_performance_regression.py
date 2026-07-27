import time
import pytest

from services.orchestrator import analyze_text
from services.threat_intelligence_service.fusion import fuse_connector_results
from core.auth import create_access_token, UserRole


class TestPerformanceBenchmarks:
    @pytest.mark.xfail(reason="ML model loading exceeds 500ms on cold start", strict=False)
    def test_text_analysis_latency_under_500ms(self):
        start = time.perf_counter()
        result = analyze_text("test message for latency benchmark")
        elapsed_ms = (time.perf_counter() - start) * 1000
        assert elapsed_ms < 500
        assert result is not None

    def test_text_analysis_repeated_calls_stable(self):
        times = []
        for i in range(5):
            start = time.perf_counter()
            analyze_text(f"Performance test message {i}")
            elapsed_ms = (time.perf_counter() - start) * 1000
            times.append(elapsed_ms)
        avg_ms = sum(times) / len(times)
        assert avg_ms < 500

    def test_text_analysis_prediction_consistent(self):
        results = []
        for _ in range(3):
            result = analyze_text("URGENT: claim your prize now!")
            results.append(result.get("prediction"))
        assert all(r == results[0] for r in results)

    def test_entity_extraction_speed(self):
        start = time.perf_counter()
        result = analyze_text("Contact admin@example.com or call +1-555-123-4567 urgently")
        elapsed_ms = (time.perf_counter() - start) * 1000
        assert elapsed_ms < 500
        assert len(result.get("entities", [])) > 0


class TestThroughput:
    def test_pipeline_throughput_multiple(self):
        start = time.perf_counter()
        count = 10
        for i in range(count):
            analyze_text(f"Throughput test message {i}")
        total_ms = (time.perf_counter() - start) * 1000
        avg_ms = total_ms / count
        assert avg_ms < 1000

    def test_concurrent_throughput(self):
        from concurrent.futures import ThreadPoolExecutor
        start = time.perf_counter()

        def analyze(i):
            return analyze_text(f"Concurrent test {i}")

        with ThreadPoolExecutor(max_workers=4) as executor:
            futures = [executor.submit(analyze, i) for i in range(8)]
            results = [f.result() for f in futures]

        total_ms = (time.perf_counter() - start) * 1000
        assert total_ms < 5000
        assert len(results) == 8


class TestMemoryUsage:
    def test_analysis_does_not_grow_unbounded(self):
        import sys
        sizes = []
        for i in range(10):
            result = analyze_text(f"Memory test {i}")
            try:
                sizes.append(sys.getsizeof(str(result)))
            except Exception:
                pass
        if len(sizes) > 1:
            avg_size = sum(sizes) / len(sizes)
            max_size = max(sizes)
            assert max_size < avg_size * 3


class TestLatencyRegression:
    def test_text_analysis_p95_latency_under_1s(self):
        times = []
        for _ in range(20):
            start = time.perf_counter()
            analyze_text("Latency regression test message")
            elapsed_ms = (time.perf_counter() - start) * 1000
            times.append(elapsed_ms)
        times.sort()
        p95_idx = int(len(times) * 0.95)
        p95_ms = times[p95_idx]
        assert p95_ms < 1000

    def test_text_analysis_p50_latency_under_500ms(self):
        times = []
        for _ in range(20):
            start = time.perf_counter()
            analyze_text("Median latency regression test")
            elapsed_ms = (time.perf_counter() - start) * 1000
            times.append(elapsed_ms)
        times.sort()
        p50_ms = times[len(times) // 2]
        assert p50_ms < 500


class TestFusionPerformance:
    def test_fuse_empty_results_is_fast(self):
        start = time.perf_counter()
        result = fuse_connector_results([])
        elapsed_ms = (time.perf_counter() - start) * 1000
        assert elapsed_ms < 100
        assert result.overall_verdict == "clean"


class TestAuthPerformance:
    def test_create_token_is_fast(self):
        start = time.perf_counter()
        token = create_access_token(subject="test", role=UserRole.ADMIN)
        elapsed_ms = (time.perf_counter() - start) * 1000
        assert elapsed_ms < 100
        assert token is not None
