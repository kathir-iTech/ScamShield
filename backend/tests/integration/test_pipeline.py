from services.orchestrator import analyze_text
from schemas.responses import AnalysisResponse


REQUIRED_FIELDS = [
    "prediction", "confidence", "rule_score", "rule_label", "reasons",
    "suggested_action", "summary", "risk_level", "scam_category",
    "detected_indicators", "threats", "recommended_actions",
    "entities", "entity_summary", "entity_risk",
    "decision_score", "decision_level", "decision_reasoning",
    "supporting_evidence", "conflicting_evidence",
    "confidence_breakdown", "risk_breakdown", "recommended_priority",
    "recommended_action",
    "assessment_score", "assessment_band", "assessment_confidence",
    "assessment_summary", "business_reason", "technical_reason",
    "review_required", "manual_review_reason",
]


def test_pipeline_returns_all_required_fields():
    result = analyze_text("Test message")
    for field in REQUIRED_FIELDS:
        assert field in result, f"Missing field: {field}"


def test_pipeline_maps_to_response_model():
    result = analyze_text("Test message")
    response = AnalysisResponse(**result)
    assert response.prediction is not None
    assert response.assessment_score >= 0


def test_pipeline_scam_detection(scam_texts):
    scam_count = 0
    for text in scam_texts:
        result = analyze_text(text)
        if result["prediction"] == "scam":
            scam_count += 1
            assert result["risk_level"] in ("CRITICAL", "HIGH", "MEDIUM")
        assert isinstance(result["assessment_score"], int)
        assert 0 <= result["assessment_score"] <= 100
    assert scam_count >= len(scam_texts) * 0.6, f"Only {scam_count}/{len(scam_texts)} scam texts detected"


def test_pipeline_safe_detection(safe_texts):
    safe_count = 0
    for text in safe_texts:
        result = analyze_text(text)
        if result["prediction"] == "safe":
            safe_count += 1
            assert result["decision_score"] <= 35, f"Safe text decision score too high"
    assert safe_count >= len(safe_texts) * 0.6, f"Only {safe_count}/{len(safe_texts)} safe texts detected"


def test_pipeline_investigation_report(scam_texts):
    result = analyze_text(scam_texts[0])
    report = result.get("investigation_report", {})
    assert report.get("report_id")
    assert len(report["incident_timeline"]) == 6
    assert "user_guidance" in report
    assert report["user_guidance"].get("immediate_actions")


def test_pipeline_evidence_generated(scam_texts):
    result = analyze_text(scam_texts[0])
    assert len(result["supporting_evidence"]) >= 1
    assert "confidence_breakdown" in result
    assert "risk_breakdown" in result


def test_pipeline_entities_extracted(scam_texts):
    result = analyze_text(scam_texts[0])
    assert len(result["entities"]) >= 1
    assert "entity_summary" in result
    assert "entity_risk" in result


def test_pipeline_entity_risk(scam_texts):
    for text in scam_texts:
        result = analyze_text(text)
        risk = result["entity_risk"]
        assert isinstance(risk.get("high"), list)
        assert isinstance(risk.get("medium"), list)
        assert isinstance(risk.get("low"), list)
