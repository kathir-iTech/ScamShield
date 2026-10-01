import os
import tempfile

import pytest
from fastapi.testclient import TestClient

os.environ["SCAMSHIELD_ENVIRONMENT"] = "testing"
os.environ["SCAMSHIELD_AUTH_ENABLED"] = "false"
os.environ.setdefault("SCAMSHIELD_RATE_LIMIT_MAX", "200")
os.environ.setdefault(
    "SCAMSHIELD_DB_PATH",
    os.path.join(tempfile.mkdtemp(prefix="scamshield-sec-"), "security.db"),
)


@pytest.fixture
def client():
    from main import app

    with TestClient(app) as c:
        yield c


@pytest.fixture
def storage():
    """Isolated database handle with per-test rate-limit state cleared."""
    from core.storage.db import get_db

    db = get_db()
    db.execute("DELETE FROM rate_limits")
    db.execute("DELETE FROM users")
    db.execute("DELETE FROM auth_tokens")
    yield db
