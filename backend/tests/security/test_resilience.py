import time

import pytest

from core.resilience import CircuitBreaker, retry, get_circuit_breaker


class TestCircuitBreaker:
    def test_initial_state_closed(self):
        cb = CircuitBreaker("test", failure_threshold=3, recovery_timeout=1)
        assert cb.state == "closed"
        assert cb.allow_request() is True

    def test_opens_after_threshold(self):
        cb = CircuitBreaker("test", failure_threshold=3, recovery_timeout=60)
        for _ in range(3):
            cb.record_failure()
        assert cb.state == "open"
        assert cb.allow_request() is False

    def test_half_open_after_recovery(self):
        cb = CircuitBreaker("test", failure_threshold=2, recovery_timeout=0.1)
        cb.record_failure()
        cb.record_failure()
        assert cb.state == "open"
        time.sleep(0.15)
        assert cb.allow_request() is True
        assert cb.state == "half-open"

    def test_closes_after_success_in_half_open(self):
        cb = CircuitBreaker("test", failure_threshold=2, recovery_timeout=0.1)
        cb.record_failure()
        cb.record_failure()
        time.sleep(0.15)
        cb.allow_request()
        cb.record_success()
        assert cb.state == "closed"

    def test_get_circuit_breaker_singleton(self):
        cb1 = get_circuit_breaker("shared")
        cb2 = get_circuit_breaker("shared")
        assert cb1 is cb2


class TestRetry:
    def test_retry_success_first_try(self):
        call_count = 0

        @retry(max_retries=2, delay_seconds=0.01)
        def succeed():
            nonlocal call_count
            call_count += 1
            return "ok"

        result = succeed()
        assert result == "ok"
        assert call_count == 1

    def test_retry_after_failures(self):
        call_count = 0

        @retry(max_retries=3, delay_seconds=0.01)
        def fail_then_succeed():
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                raise ValueError("not yet")
            return "ok"

        result = fail_then_succeed()
        assert result == "ok"
        assert call_count == 3

    def test_retry_exhausted(self):
        call_count = 0

        @retry(max_retries=2, delay_seconds=0.01)
        def always_fail():
            nonlocal call_count
            call_count += 1
            raise ValueError("always fail")

        with pytest.raises(ValueError, match="always fail"):
            always_fail()
        assert call_count == 3
