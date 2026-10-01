from __future__ import annotations

import time

import pytest

from core.storage.db import Database
from core.storage.repositories import (
    AnalysisRepo,
    AuditRepo,
    AuthTokenRepo,
    RateLimitRepo,
)


@pytest.fixture
def db_path(tmp_path):
    return str(tmp_path / "persist.db")


@pytest.fixture
def db(db_path):
    database = Database(db_path)
    yield database
    database.close()


class TestAnalysisPersistence:
    def test_analysis_survives_process_restart(self, db_path):
        repo = AnalysisRepo(Database(db_path))
        analysis_id = repo.insert(
            {
                "request_id": "req-1",
                "user_id": "usr_1",
                "source": "text",
                "input_hash": "abc123",
                "input_preview": "win a free iPhone",
                "prediction": "scam",
                "is_scam": 1,
                "confidence": 0.97,
                "risk_level": "high",
                "category": "UPSCALE",
                "model_version": "v1",
                "duration_ms": 12.5,
                "payload": "{}",
                "created_at": time.time(),
            }
        )

        reopened = Database(db_path)
        try:
            stored = reopened.query_one(
                "SELECT * FROM analyses WHERE id = ?", (analysis_id,)
            )
            assert stored is not None
            assert stored["prediction"] == "scam"
            assert stored["confidence"] == pytest.approx(0.97)
            assert AnalysisRepo(reopened).count() == 1
        finally:
            reopened.close()


class TestAuditChain:
    def test_audit_rows_persist(self, db_path):
        repo = AuditRepo(Database(db_path))
        repo.append({"event": "auth:login", "detail": "first"})
        repo.append({"event": "auth:login", "detail": "second"})

        reopened = Database(db_path)
        try:
            fresh = AuditRepo(reopened)
            assert fresh.count() == 2
            ok, reason = fresh.verify_chain()
            assert ok, reason
        finally:
            reopened.close()

    def test_chain_links_events_in_order(self, db):
        repo = AuditRepo(db)
        first = repo.append({"event": "auth:login", "detail": "a"})
        second = repo.append({"event": "auth:login", "detail": "b"})
        rows = db.query("SELECT prev_hash, hash FROM audit_events ORDER BY seq ASC")
        assert rows[0]["prev_hash"] == "0" * 64
        assert rows[0]["hash"] == first
        assert rows[1]["prev_hash"] == first
        assert rows[1]["hash"] == second

    def test_tampering_is_detected(self, db):
        repo = AuditRepo(db)
        repo.append({"event": "auth:login", "detail": "original"})
        repo.append({"event": "auth:login", "detail": "later"})

        ok, _ = repo.verify_chain()
        assert ok is True

        db.execute(
            "UPDATE audit_events SET detail = 'forged' WHERE seq = "
            "(SELECT MIN(seq) FROM audit_events)"
        )
        ok, reason = repo.verify_chain()
        assert ok is False
        assert "tampered" in reason

    def test_deleting_a_row_breaks_the_chain(self, db):
        repo = AuditRepo(db)
        repo.append({"event": "auth:login", "detail": "one"})
        repo.append({"event": "auth:login", "detail": "two"})
        repo.append({"event": "auth:login", "detail": "three"})
        db.execute(
            "DELETE FROM audit_events WHERE seq = "
            "(SELECT MIN(seq) FROM audit_events)"
        )
        ok, reason = repo.verify_chain()
        assert ok is False
        assert "prev_hash" in reason


class TestTokenRevocation:
    def test_refresh_token_cannot_be_reused(self, db):
        repo = AuthTokenRepo(db)
        assert repo.mark_refresh_used("jti-1") is True
        assert repo.mark_refresh_used("jti-1") is False
        assert repo.is_revoked("jti-1") is True

    def test_reuse_revokes_the_token(self, db):
        repo = AuthTokenRepo(db)
        repo.store("jti-2", "usr_1", "refresh", "authenticated", time.time() + 60)
        repo.mark_refresh_used("jti-2")
        repo.mark_refresh_used("jti-2")
        assert repo.is_revoked("jti-2") is True

    def test_revoke_all_for_user_returns_count(self, db):
        repo = AuthTokenRepo(db)
        repo.store("jti-a", "usr_1", "refresh", "authenticated", time.time() + 60)
        repo.store("jti-b", "usr_1", "refresh", "authenticated", time.time() + 60)
        repo.store("jti-c", "usr_2", "refresh", "authenticated", time.time() + 60)

        assert repo.revoke_all_for_user("usr_1") == 2
        assert repo.is_revoked("jti-a") is True
        assert repo.is_revoked("jti-b") is True
        assert repo.is_revoked("jti-c") is False

    def test_purge_expired_removes_stale_rows(self, db):
        repo = AuthTokenRepo(db)
        repo.store("jti-old", "usr_1", "refresh", "authenticated", time.time() - 10)
        repo.store("jti-new", "usr_1", "refresh", "authenticated", time.time() + 600)
        assert repo.purge_expired(time.time()) == 1
        assert repo.is_revoked("jti-old") is False


class TestPersistentRateLimit:
    def test_limit_is_enforced_then_blocks(self, db):
        repo = RateLimitRepo(db)
        bucket = "ip:1.2.3.4"
        results = []
        blocked_at = None
        for i in range(10):
            state = repo.hit(bucket, 60, 3, 30)
            results.append(state)
            if state["blocked_until"] > time.time():
                blocked_at = i
                break

        assert [r["allowed"] for r in results[:3]] == [True, True, True]
        assert results[0]["remaining"] == 2
        assert blocked_at is not None, "bucket never escalated to a block"
        assert all(r["remaining"] >= 0 for r in results)
        assert repo.hit(bucket, 60, 3, 30)["allowed"] is False

    def test_buckets_are_isolated(self, db):
        repo = RateLimitRepo(db)
        for _ in range(3):
            repo.hit("ip:1.1.1.1", 60, 3, 30)
        other = repo.hit("ip:2.2.2.2", 60, 3, 30)
        assert other["allowed"] is True
        assert other["remaining"] == 2

    def test_limit_survives_reopen(self, db_path):
        repo = RateLimitRepo(Database(db_path))
        for _ in range(3):
            repo.hit("ip:persist", 60, 3, 30)

        reopened = Database(db_path)
        try:
            after = RateLimitRepo(reopened).hit("ip:persist", 60, 3, 30)
            assert after["allowed"] is False
        finally:
            reopened.close()
