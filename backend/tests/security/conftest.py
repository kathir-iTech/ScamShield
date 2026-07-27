import os

import pytest
from fastapi.testclient import TestClient

os.environ["SCAMSHIELD_ENVIRONMENT"] = "testing"
os.environ["SCAMSHIELD_AUTH_ENABLED"] = "false"
os.environ.setdefault("SCAMSHIELD_RATE_LIMIT_MAX", "200")


@pytest.fixture
def client():
    from main import app
    with TestClient(app) as c:
        yield c
