from typing import Dict, List, Tuple

from config.settings import FUSION_SOURCE_WEIGHTS
from .models import EvidenceRank, ConflictRecord, FuseResult


def _get_source_weight(source: str) -> float:
    return FUSION_SOURCE_WEIGHTS.get(source, 0.5)


def _risk_score(risk: str) -> int:
    ranks = {"CRITICAL": 5, "HIGH": 4, "MEDIUM": 3, "LOW": 2, "UNKNOWN": 1}
    return ranks.get(risk, 0)


def _deduplicate_results(results: List[Dict]) -> List[Dict]:
    seen = set()
    deduped: List[Dict] = []
    for r in results:
        key = f"{r.get('source', '')}:{r.get('indicator', '')}:{r.get('indicator_type', '')}"
        if key not in seen:
            seen.add(key)
            deduped.append(r)
    return deduped


def _cluster_indicators(results: List[Dict]) -> Dict[str, List[Dict]]:
    clustered: Dict[str, List[Dict]] = {}
    for r in results:
        ind = r.get("indicator", "")
        itype = r.get("indicator_type", "")
        key = f"{itype}:{ind}"
        clustered.setdefault(key, []).append(r)
    return clustered


def _rank_evidence(item: Dict) -> EvidenceRank:
    matched = item.get("matched", False)
    risk = item.get("risk", "UNKNOWN")
    confidence = item.get("confidence", 0.0)
    error = item.get("error")

    if matched and risk in ("CRITICAL", "HIGH") and confidence >= 0.8:
        rank = "critical"
        reason = f"Matched threat with {risk} risk and {confidence:.0%} confidence"
    elif matched and risk in ("HIGH", "MEDIUM") and confidence >= 0.6:
        rank = "strong"
        reason = f"Matched threat with {risk} risk and {confidence:.0%} confidence"
    elif matched:
        rank = "supporting"
        reason = f"Matched threat with {risk} risk and {confidence:.0%} confidence"
    elif error:
        rank = "weak"
        reason = f"Source unavailable: {error}"
    else:
        rank = "informational"
        reason = "No threat detected"

    return EvidenceRank(
        indicator=item.get("indicator", ""),
        indicator_type=item.get("indicator_type", ""),
        matched=matched,
        risk=risk,
        confidence=confidence,
        source=item.get("source", ""),
        rank=rank,
        rank_reason=reason,
        summary=item.get("summary", ""),
        error=error,
    )


def _detect_conflicts(
    clustered: Dict[str, List[Dict]],
) -> Tuple[List[ConflictRecord], float]:
    conflicts: List[ConflictRecord] = []
    total_pairs = 0
    conflict_pairs = 0

    for key, items in clustered.items():
        matched_sources = [i for i in items if i.get("matched", False)]
        unmatched_sources = [i for i in items if not i.get("matched", False) and not i.get("error")]

        for m in matched_sources:
            for u in unmatched_sources:
                total_pairs += 1
                m_weight = _get_source_weight(m.get("source", ""))
                u_weight = _get_source_weight(u.get("source", ""))
                if m_weight > u_weight:
                    resolution = "trust_matched"
                    reason = (
                        f"Source '{m.get('source')}' (weight {m_weight:.2f}) "
                        f"reports threat with higher reliability than "
                        f"'{u.get('source')}' (weight {u_weight:.2f})"
                    )
                elif u_weight > m_weight:
                    resolution = "trust_unmatched"
                    reason = (
                        f"Source '{u.get('source')}' (weight {u_weight:.2f}) "
                        f"reports safe with higher reliability than "
                        f"'{m.get('source')}' (weight {m_weight:.2f})"
                    )
                else:
                    resolution = "trust_matched"
                    reason = (
                        f"Equal source weights; defaulting to matched verdict "
                        f"from '{m.get('source')}' over unmatched from '{u.get('source')}'"
                    )
                conflict_pairs += 1
                conflicts.append(ConflictRecord(
                    indicator=key,
                    source_a=m.get("source", ""),
                    verdict_a=f"matched ({m.get('risk', 'UNKNOWN')})",
                    source_b=u.get("source", ""),
                    verdict_b="not matched",
                    resolution=resolution,
                    resolution_reason=reason,
                ))

    conflict_score = conflict_pairs / max(total_pairs, 1)
    return conflicts, conflict_score


def _compute_agreement(clustered: Dict[str, List[Dict]]) -> Tuple[float, int, int]:
    total_indicators = len(clustered)
    if total_indicators == 0:
        return 1.0, 0, 0
    agreeing = 0
    for key, items in clustered.items():
        matched = sum(1 for i in items if i.get("matched", False))
        unmatched = sum(1 for i in items if not i.get("matched", False) and not i.get("error"))
        total_sources = len(items) - sum(1 for i in items if i.get("error"))
        if total_sources > 0:
            if matched == 0 or unmatched == 0:
                agreeing += 1
    agreement_score = agreeing / max(total_indicators, 1)
    return agreement_score, agreeing, total_indicators


def _assign_overall_verdict(
    matched_count: int,
    total_count: int,
    weighted_confidence: float,
    agreement_score: float,
    conflict_score: float,
) -> Tuple[str, str]:
    if matched_count == 0:
        return "clean", "UNKNOWN"
    match_ratio = matched_count / max(total_count, 1)
    if match_ratio >= 0.5 and weighted_confidence >= 0.7 and agreement_score >= 0.5:
        return "malicious", "HIGH"
    if match_ratio >= 0.3 or weighted_confidence >= 0.5:
        return "suspicious", "MEDIUM"
    return "clean", "UNKNOWN"


def fuse_connector_results(connector_matches: List[Dict]) -> FuseResult:
    if not connector_matches:
        return FuseResult(
            overall_verdict="clean",
            overall_confidence=0.0,
            overall_risk="UNKNOWN",
            sources_consulted=0,
            matched_sources=0,
        )

    deduped = _deduplicate_results(connector_matches)
    clustered = _cluster_indicators(deduped)

    matched = [r for r in deduped if r.get("matched", False)]
    unmatched = [r for r in deduped if not r.get("matched", False) and not r.get("error")]
    matched_count = len(matched)
    total_non_error = len(matched) + len(unmatched)

    weighted_confidence = 0.0
    total_weight = 0.0
    for r in matched:
        w = _get_source_weight(r.get("source", ""))
        c = r.get("confidence", 0.0)
        weighted_confidence += w * c
        total_weight += w
    overall_confidence = (weighted_confidence / total_weight) if total_weight > 0 else 0.0

    max_risk = "UNKNOWN"
    for r in matched:
        r_risk = r.get("risk", "UNKNOWN")
        if _risk_score(r_risk) > _risk_score(max_risk):
            max_risk = r_risk

    agreement_score, agreeing, total_inds = _compute_agreement(clustered)
    conflicts, conflict_score = _detect_conflicts(clustered)

    overall_verdict, overall_risk = _assign_overall_verdict(
        matched_count, total_non_error, overall_confidence, agreement_score, conflict_score
    )

    if overall_risk == "UNKNOWN" and matched:
        overall_risk = max_risk

    evidence_ranking = [_rank_evidence(r).to_dict() for r in deduped]
    evidence_ranking.sort(key=lambda x: (
        {"critical": 0, "strong": 1, "supporting": 2, "weak": 3, "informational": 4}.get(x.get("rank", "informational"), 5),
        -x.get("confidence", 0.0),
    ))

    contributing_sources = []
    seen_sources = set()
    for r in deduped:
        src = r.get("source", "")
        if src not in seen_sources:
            seen_sources.add(src)
            contributing_sources.append({
                "source": src,
                "weight": _get_source_weight(src),
                "matched": r.get("matched", False),
                "risk": r.get("risk", "UNKNOWN"),
                "confidence": r.get("confidence", 0.0),
                "latency": r.get("latency", 0.0),
                "error": r.get("error"),
            })

    missing_evidence = []
    expected_types = {"url", "domain", "phone", "email", "upi"}
    found_types = set(r.get("indicator_type", "") for r in deduped if not r.get("error"))
    uncovered = expected_types - found_types
    if uncovered:
        for t in sorted(uncovered):
            missing_evidence.append(f"No connector consulted for indicator type '{t}'")

    return FuseResult(
        overall_verdict=overall_verdict,
        overall_confidence=round(overall_confidence, 3),
        overall_risk=overall_risk,
        contributing_sources=contributing_sources,
        agreement_score=round(agreement_score, 3),
        conflict_score=round(conflict_score, 3),
        missing_evidence=missing_evidence,
        evidence_ranking=evidence_ranking,
        conflict_resolution=[c.to_dict() for c in conflicts],
        sources_consulted=len(seen_sources),
        matched_sources=matched_count,
    )
