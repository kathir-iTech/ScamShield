import time
from concurrent.futures import ThreadPoolExecutor, as_completed

import pytest
from fastapi.testclient import TestClient


class TestThroughput:
    def test_single_request_latency(self, client):
        start = time.perf_counter()
        resp = client.post("/analyze/text", json={"text": "Test message for latency check"})
        elapsed = time.perf_counter() - start
        assert resp.status_code == 200
        assert elapsed < 10.0

    def test_burst_50_requests_no_errors(self, client):
        errors = []
        for i in range(50):
            resp = client.post("/analyze/text", json={"text": f"Burst test message number {i}"})
            if resp.status_code != 200:
                errors.append(f"req {i}: {resp.status_code}")
        assert not errors, f"Errors in burst: {errors[:10]}"

    def test_burst_50_throughput(self, client):
        start = time.perf_counter()
        count = 50
        for i in range(count):
            resp = client.post("/analyze/text", json={"text": f"Throughput test message {i}"})
            assert resp.status_code == 200
        total = time.perf_counter() - start
        rps = count / total
        assert rps >= 5


class TestConcurrentLoad:
    def test_10_concurrent_requests(self, client):
        errors = []
        def req(i):
            resp = client.post("/analyze/text", json={"text": f"Concurrent load test {i}"})
            if resp.status_code != 200:
                errors.append(f"req {i}: {resp.status_code}")
            return resp.status_code
        with ThreadPoolExecutor(max_workers=10) as ex:
            list(ex.map(req, range(10)))
        assert not errors, f"Errors in concurrent: {errors[:5]}"

    def test_concurrent_health_and_analyze(self, client):
        def health():
            return client.get("/health").status_code
        def analyze(i):
            return client.post("/analyze/text", json={"text": f"Mixed load {i}"}).status_code
        with ThreadPoolExecutor(max_workers=8) as ex:
            health_futures = [ex.submit(health) for _ in range(5)]
            analyze_futures = [ex.submit(analyze, i) for i in range(10)]
            codes = [f.result() for f in health_futures + analyze_futures]
        assert all(c == 200 for c in codes), f"Non-200 codes: {[c for c in codes if c != 200]}"


class TestSustainedLoad:
    def test_sequential_no_degradation(self, client):
        times = []
        for i in range(20):
            start = time.perf_counter()
            resp = client.post("/analyze/text", json={"text": f"Sustained load test {i}"})
            elapsed = time.perf_counter() - start
            assert resp.status_code == 200
            times.append(elapsed)
        first_half = sum(times[:10]) / 10
        second_half = sum(times[10:]) / 10
        assert second_half < first_half * 3

    def test_multiple_endpoints(self, client):
        endpoints = [
            ("GET", "/health"),
            ("GET", "/version"),
            ("POST", "/analyze/text", {"text": "Test message for endpoint mix"}),
        ]
        for ep in endpoints:
            if ep[0] == "GET":
                resp = client.get(ep[1])
            else:
                resp = client.post(ep[1], json=ep[2])
            assert resp.status_code == 200, f"Failed on {ep[1]}: {resp.status_code}"
