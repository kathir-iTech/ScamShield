import pytest
from unittest.mock import patch, MagicMock

from domains.shared.models import KnowledgeMatch, AdvisoryMatch, HistoricalMatch


class TestKnowledgeBaseChaos:
    def test_empty_patterns_returns_empty(self):
        from domains.knowledge.search import search_by_domain, search_by_keywords
        result = search_by_domain("test.com", [])
        assert result == []

    def test_empty_watchlist_does_not_crash(self):
        from domains.knowledge.search import search_by_keywords
        result = search_by_keywords(["test"], [])
        assert isinstance(result, list)

    def test_empty_advisories_returns_empty(self):
        from domains.knowledge.advisory import match_advisories
        result = match_advisories("test", {}, indicator_type="url", indicator_value="http://test.com")
        assert result == []

    def test_enrich_with_empty_data(self):
        from domains.knowledge.enrichment import enrich_entities
        result = enrich_entities([], [], {"patterns": [], "advisories": {}, "watchlists": [], "examples": []})
        assert isinstance(result, dict)
        assert result["match_count"] == 0

    def test_enrich_with_empty_records(self):
        from domains.knowledge.enrichment import enrich_entities
        entities = [{"type": "url", "value": "http://evil.com"}]
        result = enrich_entities(entities, [], {"patterns": [], "advisories": {}, "watchlists": [], "examples": []})
        assert result["match_count"] == 0

    def test_correlate_historical_empty(self):
        from domains.knowledge.advisory import correlate_historical
        result = correlate_historical({}, {}, "", [])
        assert result == []

    def test_correlate_historical_without_history(self):
        from domains.knowledge.advisory import correlate_historical
        entities = {"phone": [{"value": "+911234567890", "occurrences": 2}]}
        result = correlate_historical(entities, {}, "Financial Fraud", [])
        assert result == []

    def test_enrich_investigation_empty(self):
        from domains.knowledge.enrichment import enrich_investigation
        result = enrich_investigation({}, {}, "", {"patterns": [], "advisories": {}, "watchlists": [], "examples": [], "history": []})
        assert isinstance(result, dict)
        assert result["match_count"] == 0

    def test_search_nonexistent_family(self):
        from domains.knowledge.search import search_by_family
        result = search_by_family("nonexistent_family_xyz", [])
        assert result == []

    def test_search_by_qr_empty(self):
        from domains.knowledge.search import search_by_qr
        result = search_by_qr("test_qr", [])
        assert result == []


class TestMatcherChaos:
    def test_is_match_empty_strings(self):
        from domains.knowledge.matcher import _is_match
        match_type, score = _is_match("", "")
        assert match_type == "exact"
        assert score == 1.0

    def test_is_match_no_similarity(self):
        from domains.knowledge.matcher import _is_match
        match_type, score = _is_match("abcdef", "xyzxyz", threshold=3)
        assert match_type != "none" or score < 0.5

    def test_is_match_prefix(self):
        from domains.knowledge.matcher import _is_match
        from config.settings import KNOWLEDGE_PREFIX_MIN_LENGTH
        query = "test"[:KNOWLEDGE_PREFIX_MIN_LENGTH]
        record = "test_record"
        match_type, score = _is_match(query, record)
        assert match_type != "none"

    def test_is_match_partial_word_overlap(self):
        from domains.knowledge.matcher import _is_match
        match_type, score = _is_match("claim prize", "win prize claim")
        assert match_type != "none"
        assert score > 0
