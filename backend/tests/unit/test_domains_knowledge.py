import pytest

from domains.shared.models import KnowledgeMatch, AdvisoryMatch, HistoricalMatch


class TestKnowledgeMatch:
    def test_creation(self):
        km = KnowledgeMatch(
            indicator_id="id-001",
            type="email",
            value="test@example.com",
            matched_value="test@example.com",
            match_type="exact",
            confidence=0.95,
        )
        assert km.indicator_id == "id-001"
        assert km.type == "email"
        assert km.confidence == 0.95

    def test_to_dict(self):
        km = KnowledgeMatch(
            indicator_id="id-001",
            type="email",
            value="test@example.com",
            matched_value="test@example.com",
            match_type="exact",
            confidence=0.95,
        )
        d = km.to_dict()
        assert d["indicator_id"] == "id-001"
        assert d["confidence"] == 0.95

    def test_defaults(self):
        km = KnowledgeMatch(
            indicator_id="id-002",
            type="url",
            value="http://evil.com",
            matched_value="http://evil.com",
            match_type="exact",
            confidence=0.8,
        )
        assert km.risk == "MEDIUM"
        assert km.source == "internal"
        assert km.references == []


class TestAdvisoryMatch:
    def test_creation(self):
        am = AdvisoryMatch(
            advisory_id="adv-001",
            title="Test Advisory",
            source="internal",
            date="2024-01-01",
            summary="test summary",
            recommendation="do nothing",
            relevance=0.85,
        )
        assert am.advisory_id == "adv-001"
        assert am.relevance == 0.85

    def test_to_dict(self):
        am = AdvisoryMatch(
            advisory_id="adv-001",
            title="Test",
            source="internal",
            date="2024-01-01",
            summary="s",
            recommendation="r",
            relevance=0.5,
        )
        d = am.to_dict()
        assert d["advisory_id"] == "adv-001"

    def test_empty_matched_indicators(self):
        am = AdvisoryMatch(
            advisory_id="adv-002",
            title="Test",
            source="internal",
            date="2024-01-01",
            summary="s",
            recommendation="r",
            relevance=0.0,
        )
        assert am.matched_indicators == []


class TestHistoricalMatch:
    def test_creation(self):
        hm = HistoricalMatch(
            investigation_id="inv-001",
            date="2024-01-01",
            overall_risk="HIGH",
            overall_score=75,
            dominant_family="Financial Fraud",
        )
        assert hm.investigation_id == "inv-001"
        assert hm.confidence == 0.0

    def test_to_dict(self):
        hm = HistoricalMatch(
            investigation_id="inv-001",
            date="2024-01-01",
            overall_risk="HIGH",
            overall_score=75,
            dominant_family="Financial Fraud",
            confidence=0.85,
        )
        d = hm.to_dict()
        assert d["investigation_id"] == "inv-001"
        assert d["confidence"] == 0.85
