import pytest

from domains.shared.models import ReasoningResult, RefinementResult, RefinementRule, EvidenceNode, EvidenceEdge
from domains.reasoning.service import reason, refine, get_all_rules, profile_errors
from domains.reasoning.graph import _classify_family
from domains.reasoning.refinement import ALL_RULES, FP_RULES, FN_RULES, check_decision_stability


class TestReasoningService:
    def test_reason_returns_reasoning_result(self):
        analysis = {
            "prediction": "scam",
            "confidence": 0.85,
            "scam_category": "Phishing",
            "detected_indicators": ["Suspicious URL", "Payment Request"],
            "entities": [{"type": "url", "value": "http://evil.com", "risk": "HIGH"}],
            "supporting_evidence": [],
            "conflicting_evidence": [],
            "reasons": ["test reason"],
        }
        assessment = {"assessment_score": 75}
        result = reason(analysis, assessment)
        assert isinstance(result, ReasoningResult)
        assert result.family
        assert result.reasoning_summary

    def test_reason_safe_message(self):
        analysis = {
            "prediction": "safe",
            "confidence": 0.95,
            "scam_category": "",
            "detected_indicators": [],
            "entities": [],
            "supporting_evidence": [],
            "conflicting_evidence": [],
            "reasons": [],
        }
        assessment = {"assessment_score": 10}
        result = reason(analysis, assessment)
        assert result.family == "Legitimate"

    def test_refine_returns_refinement_result(self):
        analysis = {
            "prediction": "scam",
            "confidence": 0.85,
            "detected_indicators": ["Suspicious URL"],
            "entities": [{"type": "url", "value": "http://evil.com"}],
            "supporting_evidence": [],
            "conflicting_evidence": [],
            "_original_text": "test",
        }
        assessment = {"assessment_score": 75, "assessment_confidence": "HIGH", "review_required": False}
        result = refine(analysis, assessment)
        assert isinstance(result, RefinementResult)
        assert result.refined_prediction in ("scam", "safe")

    def test_get_all_rules_returns_list(self):
        rules = get_all_rules()
        assert isinstance(rules, list)
        assert len(rules) > 0
        for r in rules:
            assert "rule_id" in r
            assert "description" in r

    def test_profile_errors_returns_dict(self):
        result = profile_errors({})
        assert isinstance(result, dict)
        assert "fp_patterns" in result


class TestEvidenceGraph:
    def test_classify_family_scam(self):
        family, subfamily, conf = _classify_family(
            "Phishing", ["Suspicious URL", "Payment Request"], "scam", 0.85,
        )
        assert family
        assert subfamily
        assert conf > 0


class TestRefinementRules:
    def test_all_rules_defined(self):
        assert len(ALL_RULES) > 0
        assert len(FP_RULES) > 0
        assert len(FN_RULES) > 0

    def test_fp_rules_have_negative_impact(self):
        for rule in FP_RULES:
            assert rule.confidence_impact < 0

    def test_fn_rules_have_positive_impact(self):
        for rule in FN_RULES:
            assert rule.confidence_impact > 0

    def test_rule_has_required_attrs(self):
        rule = FP_RULES[0]
        assert rule.rule_id
        assert rule.description
        assert rule.category
        assert rule.priority
        assert callable(rule.condition)

    def test_check_decision_stability_returns_dict(self):
        analysis = {
            "prediction": "scam",
            "confidence": 0.5,
            "assessment_score": 42,
            "detected_indicators": [],
            "entities": [],
            "supporting_evidence": [],
            "conflicting_evidence": [],
            "reasons": [],
        }
        result = check_decision_stability(analysis)
        assert isinstance(result, dict)
        assert "stable" in result
        assert "concerns" in result


class TestSharedModels:
    def test_evidence_node_creation(self):
        node = EvidenceNode(
            node_id="n_001",
            node_type="evidence",
            label="test label",
            severity="HIGH",
            weight=5.0,
            confidence=0.8,
            source="test",
        )
        assert node.node_id == "n_001"

    def test_evidence_edge_creation(self):
        edge = EvidenceEdge(
            source_id="n_001",
            target_id="n_002",
            relationship="supports",
            weight=0.5,
            confidence=0.7,
        )
        assert edge.source_id == "n_001"

    def test_refinement_rule_creation(self):
        rule = RefinementRule(
            rule_id="TST-001",
            description="test",
            category="fp_reduction",
            priority="HIGH",
            confidence_impact=-0.1,
            condition=lambda x: True,
            reason="test reason",
        )
        assert rule.rule_id == "TST-001"

    def test_refinement_result_creation(self):
        result = RefinementResult(
            refined_prediction="safe",
            refined_assessment_score=30,
            refined_assessment_confidence="LOW",
            refined_review_required=False,
            decision_stable=True,
        )
        assert result.refined_prediction == "safe"
