import os
import time

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from core.abuse import SlidingWindowRateLimiter, SlidingWindowRateLimitMiddleware

os.environ["SCAMSHIELD_ENVIRONMENT"] = "testing"
os.environ["SCAMSHIELD_AUTH_ENABLED"] = "false"


class TestSlidingWindowRateLimiter:
    def test_allows_requests_within_limit(self):
        limiter = SlidingWindowRateLimiter(max_requests=5, window_seconds=60)
        now = time.monotonic()
        for _ in range(5):
            assert limiter.record_request("127.0.0.1", now) is True

    def test_blocks_requests_over_limit(self):
        limiter = SlidingWindowRateLimiter(max_requests=3, window_seconds=60)
        now = time.monotonic()
        for _ in range(3):
            limiter.record_request("127.0.0.1", now)
        assert limiter.record_request("127.0.0.1", now) is False

    def test_remaining_decreases(self):
        limiter = SlidingWindowRateLimiter(max_requests=5, window_seconds=60)
        now = time.monotonic()
        assert limiter.remaining("127.0.0.1") == 5
        limiter.record_request("127.0.0.1", now)
        assert limiter.remaining("127.0.0.1") == 4

    def test_window_slides(self):
        limiter = SlidingWindowRateLimiter(max_requests=3, window_seconds=0.1)
        now = time.monotonic()
        for _ in range(3):
            limiter.record_request("127.0.0.1", now)
        assert limiter.record_request("127.0.0.1", now) is False
        time.sleep(0.12)
        assert limiter.record_request("127.0.0.1", time.monotonic()) is True

    def test_block_after_multiple_violations(self):
        limiter = SlidingWindowRateLimiter(max_requests=2, window_seconds=60)
        now = time.monotonic()
        for _ in range(2):
            limiter.record_request("127.0.0.1", now)
        limiter.record_request("127.0.0.1", now)
        limiter.record_request("127.0.0.1", now)
        limiter.record_request("127.0.0.1", now)
        assert limiter.is_blocked("127.0.0.1") is True

    def test_different_ips_independent(self):
        limiter = SlidingWindowRateLimiter(max_requests=2, window_seconds=60)
        now = time.monotonic()
        limiter.record_request("1.1.1.1", now)
        limiter.record_request("1.1.1.1", now)
        assert limiter.record_request("1.1.1.1", now) is False
        assert limiter.record_request("2.2.2.2", now) is True


class TestSlidingWindowRateLimitMiddleware:
    @pytest.fixture(autouse=True)
    def _save_limiter(self):
        import core.abuse
        original = core.abuse._limiter
        yield
        core.abuse._limiter = original

    def test_rate_limit_headers_present(self):
        app = FastAPI()

        @app.get("/test")
        async def test_endpoint():
            return {"ok": True}

        app.add_middleware(SlidingWindowRateLimitMiddleware, max_requests=10, window_seconds=60)

        with TestClient(app) as c:
            resp = c.get("/test")
            assert resp.status_code == 200
            assert resp.headers.get("X-RateLimit-Limit") == "10"
            assert resp.headers.get("X-RateLimit-Remaining") is not None
            assert resp.headers.get("X-RateLimit-Reset") is not None

    def test_rate_limit_blocks_excess(self):
        app = FastAPI()

        @app.get("/test")
        async def test_endpoint():
            return {"ok": True}

        app.add_middleware(SlidingWindowRateLimitMiddleware, max_requests=3, window_seconds=60)

        with TestClient(app) as c:
            for _ in range(3):
                resp = c.get("/test")
                assert resp.status_code == 200
            resp = c.get("/test")
            assert resp.status_code == 429
            assert "Retry-After" in resp.headers

    def test_rate_limit_no_block_for_different_ips(self):
        app = FastAPI()

        @app.get("/test")
        async def test_endpoint():
            return {"ok": True}

        app.add_middleware(SlidingWindowRateLimitMiddleware, max_requests=2, window_seconds=60)

        with TestClient(app) as c:
            resp = c.get("/test", headers={"X-Forwarded-For": "10.0.0.1"})
            assert resp.status_code == 200
            resp = c.get("/test", headers={"X-Forwarded-For": "10.0.0.2"})
            assert resp.status_code == 200

    def test_reset(self):
        limiter = SlidingWindowRateLimiter(max_requests=3, window_seconds=60)
        now = time.monotonic()
        for _ in range(3):
            limiter.record_request("127.0.0.1", now)
        assert limiter.record_request("127.0.0.1", now) is False
        limiter.reset()
        assert limiter.record_request("127.0.0.1", time.monotonic()) is True
