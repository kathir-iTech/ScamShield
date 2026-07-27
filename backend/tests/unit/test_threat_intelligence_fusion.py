from services.threat_intelligence_service import (
    fuse_connector_results,
    _deduplicate_results,
    _cluster_indicators,
    _rank_evidence,
    _detect_conflicts,
    _compute_agreement,
    _get_source_weight,
    _risk_score,
    FuseResult,
    EvidenceRank,
    ConflictRecord,
)


def _match(src: str, indicator: str = "https://evil.com", itype: str = "url",
           matched: bool = True, risk: str = "HIGH", confidence: float = 0.85,
           error: str = None) -> dict:
    r = {
        "source": src,
        "indicator": indicator,
        "indicator_type": itype,
        "matched": matched,
        "risk": risk,
        "confidence": confidence,
        "summary": f"{'Threat' if matched else 'No threat'} from {src}",
        "latency": 50.0,
    }
    if error:
        r["error"] = error
    return r


class TestSourceWeights:
    def test_known_source_weight(self):
        assert _get_source_weight("google_safe_browsing") == 0.90
        assert _get_source_weight("mock_threat") == 0.80

    def test_unknown_source_weight(self):
        assert _get_source_weight("unknown") == 0.50


class TestRiskScore:
    def test_risk_scores(self):
        assert _risk_score("CRITICAL") == 5
        assert _risk_score("HIGH") == 4
        assert _risk_score("MEDIUM") == 3
        assert _risk_score("LOW") == 2
        assert _risk_score("UNKNOWN") == 1

    def test_unknown_risk_default(self):
        assert _risk_score("UNKNOWN") == 1


class TestDeduplicate:
    def test_exact_duplicate_removed(self):
        a = _match("gsb")
        b = _match("gsb")
        results = _deduplicate_results([a, b])
        assert len(results) == 1

    def test_different_sources_not_deduped(self):
        a = _match("gsb")
        b = _match("mock_threat")
        results = _deduplicate_results([a, b])
        assert len(results) == 2

    def test_different_indicators_not_deduped(self):
        a = _match("gsb", indicator="https://evil.com")
        b = _match("gsb", indicator="https://evil2.com")
        results = _deduplicate_results([a, b])
        assert len(results) == 2


class TestCluster:
    def test_same_indicator_clustered(self):
        a = _match("gsb", indicator="https://evil.com")
        b = _match("mock", indicator="https://evil.com")
        clustered = _cluster_indicators([a, b])
        key = "url:https://evil.com"
        assert key in clustered
        assert len(clustered[key]) == 2

    def test_different_indicators_separate(self):
        a = _match("gsb", indicator="https://evil.com")
        b = _match("gsb", indicator="https://evil2.com")
        clustered = _cluster_indicators([a, b])
        assert len(clustered) == 2


class TestEvidenceRank:
    def test_critical_rank(self):
        item = _match("gsb", risk="HIGH", confidence=0.9)
        rank = _rank_evidence(item)
        assert rank.rank == "critical"
        assert rank.matched

    def test_strong_rank(self):
        item = _match("gsb", risk="MEDIUM", confidence=0.7)
        rank = _rank_evidence(item)
        assert rank.rank == "strong"

    def test_supporting_rank(self):
        item = _match("gsb", risk="LOW", confidence=0.4)
        rank = _rank_evidence(item)
        assert rank.rank == "supporting"

    def test_weak_rank_with_error(self):
        item = _match("gsb", matched=False, risk="UNKNOWN", error="Connection failed")
        rank = _rank_evidence(item)
        assert rank.rank == "weak"
        assert "Connection failed" in rank.rank_reason

    def test_informational_rank(self):
        item = _match("gsb", matched=False, risk="UNKNOWN", confidence=0.0)
        rank = _rank_evidence(item)
        assert rank.rank == "informational"


class TestConflictDetection:
    def test_no_conflict_all_match(self):
        a = _match("gsb")
        b = _match("mock")
        conflicts, score = _detect_conflicts({"url:evil.com": [a, b]})
        assert len(conflicts) == 0
        assert score == 0.0

    def test_no_conflict_all_clean(self):
        a = _match("gsb", matched=False, risk="UNKNOWN")
        b = _match("mock", matched=False, risk="UNKNOWN")
        conflicts, score = _detect_conflicts({"url:evil.com": [a, b]})
        assert len(conflicts) == 0

    def test_conflict_detected(self):
        a = _match("gsb", matched=True, risk="HIGH")
        b = _match("mock", matched=False, risk="UNKNOWN")
        conflicts, score = _detect_conflicts({"url:evil.com": [a, b]})
        assert len(conflicts) >= 1
        assert score > 0.0

    def test_conflict_resolution_prefers_higher_weight(self):
        a = _match("google_safe_browsing", matched=True, risk="HIGH")
        b = _match("mock_threat", matched=False, risk="UNKNOWN")
        conflicts, score = _detect_conflicts({"url:evil.com": [a, b]})
        assert conflicts[0].resolution == "trust_matched"

    def test_conflict_resolution_equal_weight_default_match(self):
        a = _match("mock_threat", matched=False, risk="UNKNOWN")
        b = _match("mock_threat", matched=True, risk="HIGH")
        conflicts, score = _detect_conflicts({"url:evil.com": [a, b]})
        assert conflicts[0].resolution == "trust_matched"


class TestAgreement:
    def test_full_agreement_all_match(self):
        a = _match("gsb")
        b = _match("mock")
        score, agreeing, total = _compute_agreement({"url:evil.com": [a, b]})
        assert score == 1.0

    def test_full_agreement_all_clean(self):
        a = _match("gsb", matched=False)
        b = _match("mock", matched=False)
        score, agreeing, total = _compute_agreement({"url:evil.com": [a, b]})
        assert score == 1.0

    def test_no_agreement(self):
        a = _match("gsb", matched=True)
        b = _match("mock", matched=False)
        score, agreeing, total = _compute_agreement({"url:evil.com": [a, b]})
        assert score == 0.0

    def test_empty_cluster(self):
        score, agreeing, total = _compute_agreement({})
        assert score == 1.0


class TestFuseConnectorResults:
    def test_empty_results(self):
        result = fuse_connector_results([])
        assert result.overall_verdict == "clean"
        assert result.overall_confidence == 0.0
        assert result.sources_consulted == 0

    def test_none_results(self):
        result = fuse_connector_results([])
        assert result.overall_verdict == "clean"

    def test_single_matched_source(self):
        results = [_match("google_safe_browsing")]
        result = fuse_connector_results(results)
        assert result.overall_verdict == "malicious"
        assert result.overall_risk == "HIGH"
        assert result.overall_confidence == 0.85
        assert result.sources_consulted == 1
        assert result.matched_sources == 1

    def test_single_clean_source(self):
        results = [_match("google_safe_browsing", matched=False, risk="UNKNOWN", confidence=0.0)]
        result = fuse_connector_results(results)
        assert result.overall_verdict == "clean"

    def test_multiple_agreeing_malicious(self):
        results = [
            _match("google_safe_browsing", risk="HIGH", confidence=0.9),
            _match("mock_threat", risk="HIGH", confidence=0.85),
        ]
        result = fuse_connector_results(results)
        assert result.overall_verdict == "malicious"
        assert result.overall_risk == "HIGH"
        assert result.agreement_score == 1.0

    def test_multiple_agreeing_clean(self):
        results = [
            _match("google_safe_browsing", matched=False, risk="UNKNOWN", confidence=0.0),
            _match("mock_threat", matched=False, risk="UNKNOWN", confidence=0.0),
        ]
        result = fuse_connector_results(results)
        assert result.overall_verdict == "clean"

    def test_conflicting_sources(self):
        results = [
            _match("google_safe_browsing", matched=True, risk="HIGH", confidence=0.9),
            _match("mock_threat", matched=False, risk="UNKNOWN", confidence=0.0),
        ]
        result = fuse_connector_results(results)
        assert len(result.conflict_resolution) >= 1
        assert result.conflict_score > 0.0

    def test_source_weights_in_contributing(self):
        results = [_match("google_safe_browsing")]
        result = fuse_connector_results(results)
        assert len(result.contributing_sources) == 1
        src = result.contributing_sources[0]
        assert src["source"] == "google_safe_browsing"
        assert src["weight"] == 0.90

    def test_evidence_ranking_ordering(self):
        results = [
            _match("mock_threat", risk="LOW", confidence=0.4),
            _match("google_safe_browsing", risk="HIGH", confidence=0.95),
        ]
        result = fuse_connector_results(results)
        assert result.evidence_ranking[0]["rank"] == "critical"
        assert result.evidence_ranking[1]["rank"] == "supporting"

    def test_error_source_contributes(self):
        results = [
            _match("google_safe_browsing", matched=False, error="Timeout"),
        ]
        result = fuse_connector_results(results)
        assert result.sources_consulted == 1
        assert result.overall_verdict == "clean"

    def test_partial_error(self):
        results = [
            _match("google_safe_browsing", matched=False, error="Timeout"),
            _match("mock_threat", matched=True, risk="HIGH", confidence=0.8),
        ]
        result = fuse_connector_results(results)
        assert result.overall_verdict == "malicious"
        assert result.sources_consulted == 2

    def test_missing_evidence_types(self):
        results = [_match("google_safe_browsing")]
        result = fuse_connector_results(results)
        # url is covered, others like phone, email, domain, upi may be missing
        missing = result.missing_evidence
        assert any("phone" in m for m in missing)
        assert any("email" in m for m in missing)

    def test_to_dict(self):
        result = fuse_connector_results([_match("google_safe_browsing")])
        d = result.to_dict()
        assert d["overall_verdict"] == "malicious"
        assert d["overall_risk"] == "HIGH"
        assert "evidence_ranking" in d
        assert "conflict_resolution" in d
        assert "contributing_sources" in d

    def test_deterministic(self):
        results = [
            _match("google_safe_browsing", risk="HIGH", confidence=0.9),
            _match("mock_threat", risk="MEDIUM", confidence=0.7),
        ]
        r1 = fuse_connector_results(results)
        r2 = fuse_connector_results(results)
        assert r1.to_dict() == r2.to_dict()

    def test_suspicious_verdict_partial_match(self):
        results = [
            _match("google_safe_browsing", matched=True, risk="LOW", confidence=0.4),
            _match("mock_threat", matched=False, risk="UNKNOWN", confidence=0.0),
        ]
        result = fuse_connector_results(results)
        assert result.overall_verdict in ("suspicious", "malicious")

    def test_conflict_resolution_record(self):
        results = [
            _match("google_safe_browsing", matched=True, risk="HIGH"),
            _match("mock_threat", matched=False, risk="UNKNOWN"),
        ]
        result = fuse_connector_results(results)
        for cr in result.conflict_resolution:
            assert "resolution" in cr
            assert "resolution_reason" in cr
            assert "source_a" in cr
            assert "source_b" in cr

    def test_low_confidence_does_not_produce_malicious(self):
        results = [
            _match("google_safe_browsing", matched=True, risk="UNKNOWN", confidence=0.2),
        ]
        result = fuse_connector_results(results)
        assert result.overall_verdict == "suspicious"
        assert result.overall_confidence == 0.2

    def test_sources_consulted_deduplicated(self):
        results = [
            _match("google_safe_browsing", indicator="https://evil.com"),
            _match("google_safe_browsing", indicator="https://evil2.com"),
        ]
        result = fuse_connector_results(results)
        assert result.sources_consulted == 1
