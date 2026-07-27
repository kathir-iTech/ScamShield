import time

import pytest

from core.api_keys import APIKeyManager, SCOPES


@pytest.fixture
def manager():
    mgr = APIKeyManager()
    mgr._keys.clear()
    return mgr


class TestAPIKeyManager:
    def test_create_key(self, manager):
        key_id, raw_key = manager.create_key("test-key", scopes=["analyze:text"])
        assert key_id.startswith("scm_")
        assert len(raw_key) == 48

    def test_validate_valid_key(self, manager):
        key_id, raw_key = manager.create_key("test-key", scopes=["analyze:text"])
        api_key = manager.validate_key(raw_key)
        assert api_key is not None
        assert api_key.name == "test-key"

    def test_validate_invalid_key(self, manager):
        manager.create_key("test-key")
        api_key = manager.validate_key("invalid-key")
        assert api_key is None

    def test_revoke_key(self, manager):
        key_id, raw_key = manager.create_key("test-key")
        assert manager.revoke_key(key_id) is True
        assert manager.validate_key(raw_key) is None

    def test_rotate_key(self, manager):
        key_id, raw_key = manager.create_key("test-key")
        assert manager.validate_key(raw_key) is not None
        new_key_id, new_raw = manager.rotate_key(key_id)
        assert new_key_id == key_id
        assert new_raw != raw_key
        assert manager.validate_key(raw_key) is None
        assert manager.validate_key(new_raw) is not None

    def test_key_expiration(self, manager):
        key_id, raw_key = manager.create_key("expiring-key", expires_in_seconds=0.01)
        assert manager.validate_key(raw_key) is not None
        time.sleep(0.02)
        assert manager.validate_key(raw_key) is None

    def test_scopes(self, manager):
        key_id, raw_key = manager.create_key("scoped-key", scopes=["analyze:text"])
        api_key = manager.validate_key(raw_key)
        assert api_key is not None
        assert manager.check_scope(api_key, "analyze:text") is True
        assert manager.check_scope(api_key, "analyze:image") is False

    def test_admin_scope_allows_all(self, manager):
        key_id, raw_key = manager.create_key("admin-key", scopes=["admin:all"])
        api_key = manager.validate_key(raw_key)
        assert api_key is not None
        assert manager.check_scope(api_key, "analyze:text") is True
        assert manager.check_scope(api_key, "analyze:image") is True
        assert manager.check_scope(api_key, "metrics:read") is True

    def test_usage_count(self, manager):
        key_id, raw_key = manager.create_key("usage-key")
        manager.validate_key(raw_key)
        manager.validate_key(raw_key)
        info = manager.get_key_info(key_id)
        assert info["usage_count"] == 2

    def test_list_keys(self, manager):
        manager.create_key("key-1")
        manager.create_key("key-2")
        keys = manager.list_keys()
        assert len(keys) == 2

    def test_get_key_info(self, manager):
        key_id, raw_key = manager.create_key("info-key", scopes=["health:read"])
        info = manager.get_key_info(key_id)
        assert info["name"] == "info-key"
        assert "analyze:text" not in info["scopes"]

    def test_revoke_nonexistent_key(self, manager):
        assert manager.revoke_key("nonexistent") is False

    def test_rotate_nonexistent_key(self, manager):
        assert manager.rotate_key("nonexistent") is None

    def test_validate_by_prefix(self, manager):
        key_id, raw_key = manager.create_key("prefix-test")
        prefix = raw_key[:8]
        api_key = manager.validate_key_by_prefix(prefix, raw_key)
        assert api_key is not None
        assert api_key.name == "prefix-test"

    def test_scopes_available(self):
        assert "analyze:text" in SCOPES
        assert "admin:all" in SCOPES
        assert "health:read" in SCOPES
