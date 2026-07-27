import pytest

from domains.investigation.models import CampaignIndicators, MergedEntity, TimelineEvent, InvestigationArtefact
from domains.shared.models import KnowledgeMatch, AdvisoryMatch, HistoricalMatch, ReasoningResult, RefinementResult, RefinementRule, EvidenceNode, EvidenceEdge
from domains.reasoning.service import reason, refine, get_all_rules
from domains.reasoning.graph import _classify_family
from domains.reasoning.refinement import ALL_RULES, FP_RULES, FN_RULES, check_decision_stability


class TestInvestigationModels:
    def test_campaign_indicators_defaults(self):
        ci = CampaignIndicators()
        assert ci.shared_phones == []
        assert ci.repeated_wording is False

    def test_campaign_indicators_with_values(self):
        ci = CampaignIndicators()
        ci.shared_phones.append("+911234567890")
        ci.same_scam_family = True
        assert "+911234567890" in ci.shared_phones
        assert ci.same_scam_family is True

    def test_merged_entity_creation(self):
        me = MergedEntity(
            value="test@example.com",
            entity_type="EMAIL",
            occurrences=2,
            first_seen=0,
            sources=[0, 1],
            max_risk="HIGH",
        )
        assert me.value == "test@example.com"
        assert me.occurrences == 2

    def test_timeline_event_creation(self):
        te = TimelineEvent(
            index=1,
            artefact_index=0,
            event_type="classification",
            description="Classified as scam",
            details="Score 85/100",
        )
        assert te.event_type == "classification"

    def test_investigation_artefact_creation(self):
        art = InvestigationArtefact(
            index=0,
            artefact_type="sms",
            text="test message",
            analysis={"prediction": "scam"},
        )
        assert art.text == "test message"
        assert art.analysis["prediction"] == "scam"


class TestSharedModels:
    def test_knowledge_match_to_dict(self):
        km = KnowledgeMatch(
            indicator_id="km-1",
            type="url",
            value="http://evil.com",
            matched_value="http://evil.com",
            match_type="exact",
            confidence=0.95,
        )
        d = km.to_dict()
        assert d["indicator_id"] == "km-1"

    def test_advisory_match_defaults(self):
        am = AdvisoryMatch(
            advisory_id="adv-1",
            title="Test",
            source="internal",
            date="2024-01-01",
            summary="s",
            recommendation="r",
            relevance=0.5,
        )
        assert am.severity == "MEDIUM"

    def test_historical_match_creation(self):
        hm = HistoricalMatch(
            investigation_id="inv-1",
            date="2024-01-01",
            overall_risk="HIGH",
            overall_score=80,
            dominant_family="Financial Fraud",
        )
        assert hm.confidence == 0.0

    def test_reasoning_result_defaults(self):
        rr = ReasoningResult()
        assert rr.family == ""
        assert rr.primary_evidence == []

    def test_refinement_result_creation(self):
        rr = RefinementResult(
            refined_prediction="safe",
            refined_assessment_score=30,
            refined_assessment_confidence="LOW",
            refined_review_required=False,
            decision_stable=True,
        )
        assert rr.refined_prediction == "safe"

    def test_refinement_rule_creation(self):
        rule = RefinementRule(
            rule_id="TST-001",
            description="test rule",
            category="fp_reduction",
            priority="HIGH",
            confidence_impact=-0.1,
            condition=lambda x: True,
            reason="test reason",
        )
        assert rule.rule_id == "TST-001"

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


class TestReasoningService:
    def test_reason_returns_reasoning_result(self):
        analysis = {
            "prediction": "scam",
            "confidence": 0.85,
            "scam_category": "Phishing",
            "detected_indicators": ["Suspicious URL"],
            "entities": [{"type": "url", "value": "http://evil.com", "risk": "HIGH"}],
            "supporting_evidence": [],
            "conflicting_evidence": [],
            "reasons": ["test"],
        }
        assessment = {"assessment_score": 75}
        result = reason(analysis, assessment)
        assert isinstance(result, ReasoningResult)

    def test_reason_with_empty_evidence(self):
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
            "entities": [],
            "supporting_evidence": [],
            "conflicting_evidence": [],
            "_original_text": "test",
        }
        assessment = {"assessment_score": 75, "assessment_confidence": "HIGH", "review_required": False}
        result = refine(analysis, assessment)
        assert isinstance(result, RefinementResult)

    def test_get_all_rules_returns_list(self):
        rules = get_all_rules()
        assert isinstance(rules, list)
        assert len(rules) > 0


class TestEvidenceGraph:
    def test_classify_family_scam(self):
        family, subfamily, conf = _classify_family(
            "Phishing", ["Suspicious URL", "Payment Request"], "scam", 0.85,
        )
        assert family
        assert conf > 0

    def test_classify_family_safe(self):
        family, subfamily, conf = _classify_family("", [], "safe", 0.95)
        assert family == "Legitimate"
        assert subfamily == "Safe"


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

    def test_check_decision_stability(self):
        analysis = {
            "prediction": "scam",
            "confidence": 0.5,
            "assessment_score": 42,
            "detected_indicators": [],
            "entities": [],
            "supporting_evidence": [],
            "conflicting_evidence": [],
        }
        result = check_decision_stability(analysis)
        assert isinstance(result, dict)
        assert "stable" in result
