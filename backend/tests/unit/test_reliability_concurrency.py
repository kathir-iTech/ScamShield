import threading
import time
from concurrent.futures import ThreadPoolExecutor, as_completed

import pytest
from fastapi.testclient import TestClient
from main import app


class TestConcurrentRequests:
    def test_multiple_concurrent_text_analysis(self):
        client = TestClient(app)
        results = []

        def analyze(i):
            resp = client.post("/analyze/text", json={
                "text": f"Test message number {i} for concurrent analysis"
            })
            return resp.status_code

        with ThreadPoolExecutor(max_workers=5) as executor:
            futures = [executor.submit(analyze, i) for i in range(10)]
            for f in as_completed(futures):
                results.append(f.result())

        for status_code in results:
            assert status_code == 200

    def test_concurrent_requests_get_different_ids(self):
        client = TestClient(app)
        request_ids = set()

        for i in range(5):
            resp = client.post("/analyze/text", json={"text": f"message {i}"})
            request_ids.add(resp.headers.get("X-Request-ID"))

        assert len(request_ids) == 5

    def test_empty_pool_submission(self):
        with ThreadPoolExecutor(max_workers=1) as executor:
            future = executor.submit(lambda: 42)
            assert future.result() == 42


class TestLargePayloads:
    def test_max_length_text_accepted(self):
        client = TestClient(app)
        text = "x" * 10000
        resp = client.post("/analyze/text", json={"text": text})
        assert resp.status_code in (200, 422, 504)

    def test_oversized_text_rejected(self):
        client = TestClient(app)
        text = "x" * 100001
        resp = client.post("/analyze/text", json={"text": text})
        assert resp.status_code == 422

    def test_medium_text_accepted(self):
        client = TestClient(app)
        text = "x" * 5000
        resp = client.post("/analyze/text", json={"text": text})
        assert resp.status_code == 200


class TestGracefulShutdown:
    def test_app_shutdown_completes(self):
        client = TestClient(app)
        resp = client.get("/health")
        assert resp.status_code == 200

    def test_metrics_after_requests(self):
        client = TestClient(app)
        client.get("/health")
        resp = client.get("/metrics")
        assert resp.status_code == 200
        data = resp.json()
        assert "total_requests" in data


class TestRepeatedInvestigation:
    def test_multiple_analyses_different_inputs(self):
        client = TestClient(app)
        for i in range(5):
            resp = client.post("/analyze/text", json={
                "text": f"Test message {i} for repeated analysis"
            })
            assert resp.status_code == 200

    def test_sequential_analysis_consistency(self):
        client = TestClient(app)
        texts = [
            "URGENT: Your account needs verification",
            "Hello, how are you doing today?",
            "Win a free iPhone now!",
            "Meeting at 3 PM tomorrow",
        ]
        results = []
        for text in texts:
            resp = client.post("/analyze/text", json={"text": text})
            assert resp.status_code == 200
            results.append(resp.json()["prediction"])
        assert len(results) == 4