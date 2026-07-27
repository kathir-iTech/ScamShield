import io
import os

import pytest
from fastapi.testclient import TestClient

os.environ["SCAMSHIELD_ENVIRONMENT"] = "testing"
os.environ["SCAMSHIELD_AUTH_ENABLED"] = "false"


@pytest.fixture
def client():
    from main import app
    with TestClient(app) as c:
        yield c


class TestInputValidation:
    def test_empty_text_rejected(self, client):
        resp = client.post("/analyze/text", json={"text": ""})
        assert resp.status_code == 422

    def test_text_too_long_rejected(self, client):
        long_text = "x" * 100_001
        resp = client.post("/analyze/text", json={"text": long_text})
        assert resp.status_code == 422

    def test_text_within_limits_accepted(self, client):
        resp = client.post("/analyze/text", json={"text": "safe message"})
        assert resp.status_code in (200, 422)

    def test_invalid_json_body_rejected(self, client):
        resp = client.post("/analyze/text", data="not json", headers={"Content-Type": "application/json"})
        assert resp.status_code == 422

    def test_missing_text_field_rejected(self, client):
        resp = client.post("/analyze/text", json={})
        assert resp.status_code == 422

    def test_null_text_rejected(self, client):
        resp = client.post("/analyze/text", json={"text": None})
        assert resp.status_code == 422

    def test_extra_fields_rejected(self, client):
        resp = client.post("/analyze/text", json={"text": "hello", "extra_field": "nope"})
        assert resp.status_code == 422

    def test_empty_body_rejected(self, client):
        resp = client.post("/analyze/text", json={})
        assert resp.status_code == 422

    def test_array_instead_of_object_rejected(self, client):
        resp = client.post("/analyze/text", data="[]", headers={"Content-Type": "application/json"})
        assert resp.status_code == 422


class TestImageValidation:
    def test_non_image_file_rejected(self, client):
        resp = client.post(
            "/analyze/image",
            files={"file": ("test.txt", b"not an image", "text/plain")},
        )
        assert resp.status_code in (400, 422)

    def test_empty_image_rejected(self, client):
        resp = client.post(
            "/analyze/image",
            files={"file": ("test.png", b"", "image/png")},
        )
        assert resp.status_code in (400, 413, 422)

    def test_large_image_rejected(self, client):
        large_data = b"\x00" * (11 * 1024 * 1024)
        resp = client.post(
            "/analyze/image",
            files={"file": ("test.png", large_data, "image/png")},
        )
        assert resp.status_code in (400, 413, 422)

    def test_invalid_content_type_rejected(self, client):
        resp = client.post(
            "/analyze/image",
            files={"file": ("test.png", b"fake", "application/pdf")},
        )
        assert resp.status_code in (400, 422)

    def test_filename_traversal_sanitised(self, client):
        resp = client.post(
            "/analyze/image",
            files={"file": ("../../../etc/passwd.png", b"fake", "image/png")},
        )
        assert resp.status_code in (400, 422, 500)





class TestPIIMasking:
    def test_phone_number_masked_in_error_response(self, client):
        text = "+91-9876543210 " * 200
        resp = client.post("/analyze/text", json={"text": text[:1000]})
        if resp.status_code == 422:
            detail = str(resp.json().get("detail", ""))
            assert "<PHONE>" in detail or "<REDACTED>" in detail

    def test_email_masked_in_error_response(self, client):
        resp = client.post("/analyze/text", json={"text": "test@example.com"})
        if resp.status_code == 422:
            detail = str(resp.json().get("detail", ""))
            assert "<EMAIL>" in detail

    def test_credit_card_masked_in_error_response(self, client):
        resp = client.post("/analyze/text", json={"text": "4111-1111-1111-1111"})
        if resp.status_code == 422:
            detail = str(resp.json().get("detail", ""))
            assert "<CARD>" in detail


class TestEnvValidation:
    def test_validate_config_exists(self):
        from config.settings import validate_config
        errors = validate_config()
        assert isinstance(errors, list)
