import threading
import time

from core.cache import (
    RedisCache,
    TTLCache,
    cached,
    configure_cache,
    get_cache,
    reset_cache,
)


class TestTTLCacheBasics:
    def test_set_and_get(self):
        cache = TTLCache(maxsize=10, ttl=60)
        cache.set("key", {"value": 1})
        assert cache.get("key") == {"value": 1}

    def test_get_miss_returns_default(self):
        cache = TTLCache(maxsize=10, ttl=60)
        assert cache.get("missing") is None
        assert cache.get("missing", "fallback") == "fallback"

    def test_overwrite_moves_to_end(self):
        cache = TTLCache(maxsize=2, ttl=60)
        cache.set("a", 1)
        cache.set("b", 2)
        cache.set("a", 11)
        cache.set("c", 3)
        assert cache.get("b") is None
        assert cache.get("a") == 11
        assert cache.get("c") == 3

    def test_maxsize_eviction_is_lru(self):
        cache = TTLCache(maxsize=3, ttl=60)
        cache.set("a", 1)
        cache.set("b", 2)
        cache.set("c", 3)
        assert cache.get("a") == 1
        cache.set("d", 4)
        assert cache.get("b") is None
        assert cache.get("a") == 1
        assert cache.get("c") == 3
        assert cache.get("d") == 4
        assert cache.stats()["evictions"] == 1

    def test_ttl_expiry(self):
        cache = TTLCache(maxsize=10, ttl=0.3)
        cache.set("key", "value")
        assert cache.get("key") == "value"
        time.sleep(0.4)
        assert cache.get("key") is None

    def test_per_entry_ttl_override(self):
        cache = TTLCache(maxsize=10, ttl=60)
        cache.set("short", "value", ttl=0.3)
        time.sleep(0.4)
        assert cache.get("short") is None

    def test_pop_removes_entry(self):
        cache = TTLCache(maxsize=10, ttl=60)
        cache.set("key", "value")
        assert cache.pop("key") == "value"
        assert cache.get("key") is None
        assert cache.pop("key", "default") == "default"

    def test_contains_and_len_purge_expired(self):
        cache = TTLCache(maxsize=10, ttl=0.3)
        cache.set("a", 1)
        cache.set("b", 2)
        assert "a" in cache
        assert len(cache) == 2
        time.sleep(0.4)
        assert "a" not in cache
        assert len(cache) == 0

    def test_purge_expired_count(self):
        cache = TTLCache(maxsize=10, ttl=0.3)
        cache.set("a", 1)
        cache.set("b", 2)
        time.sleep(0.4)
        assert cache.purge_expired() == 2
        assert cache.purge_expired() == 0

    def test_clear(self):
        cache = TTLCache(maxsize=10, ttl=60)
        cache.set("a", 1)
        cache.clear()
        assert len(cache) == 0
        assert cache.get("a") is None

    def test_stats_counters(self):
        cache = TTLCache(maxsize=2, ttl=60)
        cache.set("a", 1)
        cache.set("b", 2)
        cache.get("a")
        cache.get("z")
        cache.set("c", 3)
        stats = cache.stats()
        assert stats["hits"] == 1
        assert stats["misses"] == 1
        assert stats["evictions"] == 1
        assert stats["size"] == 2
        assert stats["maxsize"] == 2

    def test_thread_safety_smoke(self):
        cache = TTLCache(maxsize=64, ttl=60)
        errors = []

        def worker(offset):
            try:
                for i in range(200):
                    cache.set(f"key-{offset}-{i % 32}", i)
                    cache.get(f"key-{offset}-{i % 32}")
            except Exception as exc:  # pragma: no cover
                errors.append(exc)

        threads = [threading.Thread(target=worker, args=(n,)) for n in range(8)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()
        assert not errors
        assert len(cache) <= 64


class TestCachedDecorator:
    def test_caches_result_per_arguments(self):
        calls = []

        @cached("probe", ttl=60)
        def compute(value):
            calls.append(value)
            return value * 2

        assert compute(2) == 4
        assert compute(2) == 4
        assert compute(3) == 6
        assert calls == [2, 3]

    def test_cache_hit_skips_execution(self):
        calls = []

        @cached("probe-once", ttl=60)
        def compute():
            calls.append(1)
            return "result"

        compute()
        compute()
        compute()
        assert len(calls) == 1


class TestConfigureCache:
    def test_configure_defaults_to_memory_cache(self):
        reset_cache()
        try:
            cache = configure_cache(ttl=45, maxsize=7, redis_url="")
            assert isinstance(cache, TTLCache)
            assert cache.ttl == 45
            assert cache.maxsize == 7
            assert get_cache() is cache
        finally:
            reset_cache()

    def test_configure_with_redis_url_is_lazy_and_fails_open(self):
        reset_cache()
        try:
            cache = configure_cache(ttl=45, maxsize=7, redis_url="redis://localhost:6399/0")
            assert isinstance(cache, RedisCache)
            assert get_cache() is cache
            assert cache.get("anything") is None
            cache.set("anything", {"ok": True})
            assert cache.get("anything") is None
            assert cache.stats()["misses"] >= 1
        finally:
            reset_cache()

    def test_reset_cache_restores_memory_default(self):
        configure_cache(ttl=45, maxsize=7, redis_url="redis://localhost:6399/0")
        reset_cache()
        cache = get_cache()
        assert isinstance(cache, TTLCache)
        assert cache.ttl == 300.0
        assert cache.maxsize == 1024


class TestOrchestratorCacheConfig:
    def test_env_configuration_applied(self, monkeypatch):
        from services.orchestrator import _configure_cache_from_env

        monkeypatch.setenv("SCAMSHIELD_CACHE_TTL", "120")
        monkeypatch.setenv("SCAMSHIELD_CACHE_MAXSIZE", "64")
        monkeypatch.setenv("SCAMSHIELD_REDIS_URL", "")
        try:
            _configure_cache_from_env()
            cache = get_cache()
            assert cache.ttl == 120
            assert cache.maxsize == 64
        finally:
            reset_cache()

    def test_invalid_env_values_fall_back_to_defaults(self, monkeypatch):
        from services.orchestrator import _configure_cache_from_env

        monkeypatch.setenv("SCAMSHIELD_CACHE_TTL", "not-a-number")
        monkeypatch.setenv("SCAMSHIELD_CACHE_MAXSIZE", "not-a-number")
        monkeypatch.setenv("SCAMSHIELD_REDIS_URL", "")
        try:
            _configure_cache_from_env()
            cache = get_cache()
            assert cache.ttl == 300.0
            assert cache.maxsize == 1024
        finally:
            reset_cache()


class TestDiagnosticsCacheExposure:
    def test_diagnostics_reports_cache_stats(self):
        from core.diagnostics import get_diagnostics

        reset_cache()
        get_cache().set("diag-probe", {"ok": True})
        diagnostics = get_diagnostics()
        cache_stats = diagnostics["observability"]["cache"]
        assert set(cache_stats) == {"hits", "misses", "evictions", "size", "maxsize"}
        assert cache_stats["size"] == 1
        reset_cache()

    def test_pipeline_summary_derived_from_registry(self):
        import services.orchestrator  # noqa: F401
        from core.diagnostics import get_diagnostics

        summary = get_diagnostics()["pipeline_summary"]
        assert summary["total_stages"] == len(summary["stages"])
        assert summary["total_stages"] >= 7
