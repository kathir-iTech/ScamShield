from __future__ import annotations

import pytest
from fastapi.testclient import TestClient
from main import app
from core.auth import UserRole, create_access_token


@pytest.fixture(autouse=True)
def _configure_auth_for_tests():
    from core.auth import configure_auth
    configure_auth(secret_key="test-secret-key-sprint3", access_ttl=3600, refresh_ttl=86400 * 30, clock_skew=30)


@pytest.fixture
def admin_client():
    admin_token = create_access_token(subject="admin_user_sprint3", role=UserRole.ADMIN)
    client = TestClient(app)
    client.headers.update({"Authorization": f"Bearer {admin_token}"})
    yield client


class TestEndToEndInvestigation:
    def test_investigation_workflow_from_analysis_to_report(self, admin_client):
        # Step 1: Analyze text to get initial findings
        analysis_resp = admin_client.post("/analyze/text", json={
            "text": "URGENT: Your bank account is compromised. Click http://scam.link to verify."
        })
        assert analysis_resp.status_code == 200
        analysis_data = analysis_resp.json()
        assert analysis_data["prediction"] in ("scam", "safe")
        assert "entities" in analysis_data
        assert "supporting_evidence" in analysis_data

        artefacts = []
        if "entities" in analysis_data:
            for entity in analysis_data["entities"]:
                artefacts.append({"text": entity["value"], "type": entity["type"]})

        if "supporting_evidence" in analysis_data:
             for evidence in analysis_data["supporting_evidence"]:
                 artefacts.append({"text": evidence.get("description", "no desc"), "type": "evidence"})

        if not artefacts:
             artefacts.append({"text": "fallback investigation query", "type": "text"})

        investigation_req = {"artefacts": artefacts[:10]}

        investigation_resp = admin_client.post("/analyze/investigation", json=investigation_req)
        assert investigation_resp.status_code == 200
        investigation_data = investigation_resp.json()

        assert "investigation_id" in investigation_data
        assert "global_assessment" in investigation_data
        assert "campaign" in investigation_data
        assert "overall_risk" in investigation_data["global_assessment"]
