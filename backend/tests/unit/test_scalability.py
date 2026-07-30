import os
import time
import threading
from unittest.mock import MagicMock, patch

import pytest

from core.abuse import (
    SlidingWindowRateLimiter,
    RedisSlidingWindowRateLimiter,
    create_rate_limiter,
)


class TestSlidingWindowRateLimiterThreadSafety:
    def test_concurrent_record_request(self):
        limiter = SlidingWindowRateLimiter(max_requests=100, window_seconds=60)
        errors = []

        def worker(ip):
            now = time.monotonic()
            for _ in range(50):
                try:
                    limiter.record_request(ip, now)
                except Exception as e:
                    errors.append(e)

        threads = [threading.Thread(target=worker, args=("10.0.0.1",)) for _ in range(8)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        assert not errors, f"Thread safety errors: {errors}"
        remaining = limiter.remaining("10.0.0.1")
        assert remaining >= 0

    def test_concurrent_remaining_and_record(self):
        limiter = SlidingWindowRateLimiter(max_requests=50, window_seconds=60)
        errors = []

        def writer():
            now = time.monotonic()
            for _ in range(20):
                try:
                    limiter.record_request("10.0.0.2", now)
                except Exception as e:
                    errors.append(e)

        def reader():
            for _ in range(20):
                try:
                    limiter.remaining("10.0.0.2")
                except Exception as e:
                    errors.append(e)

        threads = [threading.Thread(target=writer) for _ in range(3)]
        threads += [threading.Thread(target=reader) for _ in range(3)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        assert not errors, f"Thread safety errors: {errors}"

    def test_concurrent_is_blocked(self):
        limiter = SlidingWindowRateLimiter(max_requests=5, window_seconds=60)
        now = time.monotonic()
        for _ in range(5):
            limiter.record_request("10.0.0.3", now)
        for _ in range(3):
            limiter.record_request("10.0.0.3", now)

        errors = []

        def checker():
            for _ in range(20):
                try:
                    limiter.is_blocked("10.0.0.3")
                except Exception as e:
                    errors.append(e)

        threads = [threading.Thread(target=checker) for _ in range(4)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        assert not errors, f"Thread safety errors: {errors}"


class TestRedisSlidingWindowRateLimiter:
    def test_factory_returns_in_memory_when_no_redis(self):
        with patch("config.settings.REDIS_URL", ""):
            limiter = create_rate_limiter("test", 10, 60)
            assert isinstance(limiter, SlidingWindowRateLimiter)

    def test_factory_returns_redis_when_redis_available(self):
        redis_mock = MagicMock()
        redis_mock.ping.return_value = True
        with patch("config.settings.REDIS_URL", "redis://localhost:6379/0"):
            with patch("redis.from_url", return_value=redis_mock):
                limiter = create_rate_limiter("test_redis", 10, 60)
                assert isinstance(limiter, RedisSlidingWindowRateLimiter)

    def test_redis_fallback_on_connection_error(self):
        with patch("config.settings.REDIS_URL", "redis://localhost:6379/0"):
            with patch("redis.from_url", side_effect=Exception("Connection refused")):
                limiter = create_rate_limiter("test_fallback", 10, 60)
                assert isinstance(limiter, SlidingWindowRateLimiter)

    def test_redis_record_request(self):
        redis_mock = MagicMock()
        redis_mock.zremrangebyscore.return_value = 0
        redis_mock.zcard.return_value = 1
        redis_mock.zadd.return_value = 1

        limiter = RedisSlidingWindowRateLimiter(max_requests=10, window_seconds=60)
        limiter._redis = redis_mock

        result = limiter.record_request("10.0.0.1", time.monotonic())
        assert result is True
        redis_mock.zadd.assert_called_once()

    def test_redis_block_when_over_limit(self):
        redis_mock = MagicMock()
        redis_mock.zremrangebyscore.return_value = 0
        redis_mock.zcard.return_value = 10

        limiter = RedisSlidingWindowRateLimiter(max_requests=10, window_seconds=60)
        limiter._redis = redis_mock

        result = limiter.record_request("10.0.0.1", time.monotonic())
        assert result is False

    def test_redis_remaining(self):
        redis_mock = MagicMock()
        redis_mock.zremrangebyscore.return_value = 0
        redis_mock.zcard.return_value = 3

        limiter = RedisSlidingWindowRateLimiter(max_requests=10, window_seconds=60)
        limiter._redis = redis_mock

        remaining = limiter.remaining("10.0.0.1")
        assert remaining == 7

    def test_redis_failure_falls_open(self):
        limiter = RedisSlidingWindowRateLimiter(max_requests=10, window_seconds=60)

        result = limiter.record_request("10.0.0.1", time.monotonic())
        assert result is True

        remaining = limiter.remaining("10.0.0.1")
        assert remaining == 10

    def test_redis_reset_ip(self):
        redis_mock = MagicMock()
        limiter = RedisSlidingWindowRateLimiter(max_requests=10, window_seconds=60)
        limiter._redis = redis_mock

        limiter.reset_ip("10.0.0.1")
        redis_mock.delete.assert_called_once()


class TestRateLimiterFactory:
    def test_factory_returns_limiter(self):
        limiter = create_rate_limiter("factory_test", 50, 30)
        assert limiter is not None
        assert hasattr(limiter, "record_request")
        assert hasattr(limiter, "remaining")
        assert hasattr(limiter, "is_blocked")

    def test_factory_defaults(self):
        limiter = create_rate_limiter()
        assert isinstance(limiter, SlidingWindowRateLimiter)
        assert limiter.max_requests == 100
        assert limiter.window_seconds == 60

    def test_factory_custom_params(self):
        limiter = create_rate_limiter("custom", 5, 10)
        assert limiter.max_requests == 5
        assert limiter.window_seconds == 10


class TestOCRCleanup:
    def test_shutdown_ocr_pool_does_not_raise(self):
        from ocr import shutdown_ocr_pool
        try:
            shutdown_ocr_pool()
            shutdown_ocr_pool()
        except Exception as e:
            pytest.fail(f"shutdown_ocr_pool raised: {e}")


class TestConnectorPoolCleanup:
    def test_shutdown_connector_pool_does_not_raise(self):
        from connectors.manager import shutdown_connector_pool
        try:
            shutdown_connector_pool()
            shutdown_connector_pool()
        except Exception as e:
            pytest.fail(f"shutdown_connector_pool raised: {e}")


class TestLifespan:
    @pytest.mark.asyncio
    async def test_lifespan_context_manager_imports(self):
        from main import lifespan
        assert lifespan is not None


class TestAuthRateLimitHeaders:
    def test_rate_limit_header_function_exists(self):
        from routers.auth import _add_rate_limit_headers
        assert callable(_add_rate_limit_headers)
