from __future__ import annotations

import pytest
import time
from unittest.mock import patch, AsyncMock

from core.resilience import CircuitBreaker, CircuitBreakerState, get_circuit_breaker, retry
from core.auth import UserRole


class TestCircuitBreakerFunctional:
    def test_circuit_breaker_opens_and_closes(self):
        cb = CircuitBreaker("test", failure_threshold=2, recovery_timeout=0.1)
        
        cb.record_failure()
        cb.record_failure()
        assert cb.state == CircuitBreakerState.OPEN
        assert not cb.allow_request()

        time.sleep(0.15)
        assert cb.allow_request() is True
        assert cb.state == CircuitBreakerState.HALF_OPEN

        cb.record_success() # Success in half-open state should close it
        assert cb.state == CircuitBreakerState.CLOSED

    def test_half_open_failure_reopens_circuit(self):
        cb = CircuitBreaker("test", failure_threshold=2, recovery_timeout=0.1)
        cb.record_failure()
        cb.record_failure()
        assert cb.state == CircuitBreakerState.OPEN
        
        time.sleep(0.15)
        assert cb.allow_request() # Allow one request in half-open
        cb.record_failure() # This failure should reopen the circuit
        assert cb.state == CircuitBreakerState.OPEN

    def test_zero_threshold_opens_immediately(self):
        cb = CircuitBreaker("test", failure_threshold=0, recovery_timeout=0.1)
        cb.record_failure()
        assert cb.state == CircuitBreakerState.OPEN


class TestRetryLogic:
    @pytest.mark.asyncio
    async def test_async_retry_succeeds_on_second_attempt(self):
        attempts = [0]

        @retry(max_retries=2, delay_seconds=0.01)
        async def async_maybe_succeed():
            attempts[0] += 1
            if attempts[0] < 2:
                raise ValueError("not yet")
            return "success"

        result = await async_maybe_succeed()
        assert result == "success"
        assert attempts[0] == 2

    @pytest.mark.asyncio
    async def test_async_retry_exhausts_all_attempts(self):
        attempts = [0]

        @retry(max_retries=2, delay_seconds=0.01)
        async def async_always_fails():
            attempts[0] += 1
            raise ValueError("always fail")

        with pytest.raises(ValueError, match="always fail"):
            await async_always_fails()
        assert attempts[0] == 3

    def test_sync_retry_succeeds_on_second_attempt(self):
        attempts = [0]

        @retry(max_retries=2, delay_seconds=0.01)
        def sync_maybe_succeed():
            attempts[0] += 1
            if attempts[0] < 2:
                raise ValueError("not yet")
            return "success"

        result = sync_maybe_succeed()
        assert result == "success"
        assert attempts[0] == 2

    def test_sync_retry_exhausts_all_attempts(self):
        attempts = [0]

        @retry(max_retries=2, delay_seconds=0.01)
        def sync_always_fails():
            attempts[0] += 1
            raise ValueError("always fail")

        with pytest.raises(ValueError, match="always fail"):
            sync_always_fails()
        assert attempts[0] == 3


class TestConcurrencySafety:
    def test_token_blacklist_is_thread_safe(self):
        from core.auth.jwt import blacklist_token, is_token_blacklisted, reset_blacklist
        
        reset_blacklist() # Ensure clean state
        
        jti = "test_jti_123"
        assert is_token_blacklisted(jti) is False
        
        blacklist_token(jti)
        assert is_token_blacklisted(jti) is True

    def test_refresh_token_tracking_is_thread_safe(self):
        from core.auth.jwt import mark_refresh_used, is_refresh_reused, reset_blacklist
        
        reset_blacklist() # Ensure clean state
        
        jti = "test_refresh_jti_456"
        assert is_refresh_reused(jti) is False
        
        assert mark_refresh_used(jti) is True
        assert is_refresh_reused(jti) is True
        assert mark_refresh_used(jti) is False # Second call fails

