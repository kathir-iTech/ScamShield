from typing import Any, Dict, List, Optional, Tuple

from core.constants import (
    CONFIDENCE_HIGH,
    CONFIDENCE_LOW,
    CONFIDENCE_MEDIUM,
    ML_LABEL_SAFE,
    ML_LABEL_SCAM,
    RISK_HIGH,
    RISK_LOW,
    RISK_MEDIUM,
    UNKNOWN_CATEGORY,
)
from domains.shared.models import ReasoningResult, RefinementResult, EvidenceNode, EvidenceEdge

from .graph import (
    _classify_family,
    _build_evidence_nodes,
    _build_edges,
    _rank_evidence,
    _build_decision_trace,
    _build_summary as _build_graph_summary,
)
from .refinement import (
    _compute_fp_adjustment,
    _compute_fn_adjustment,
    _adjust_assessment_score,
    _map_confidence,
    _check_decision_stability,
    _build_summary as _build_refinement_summary,
    ALL_RULES,
    check_decision_stability,
)


def reason(
    analysis: Dict[str, Any],
    assessment: Dict[str, Any],
    refinement_result: Optional[Dict[str, Any]] = None,
) -> ReasoningResult:
    prediction = analysis.get("prediction", ML_LABEL_SAFE)
    ml_confidence = analysis.get("confidence", 0.0)
    category = analysis.get("scam_category", UNKNOWN_CATEGORY)
    indicators = analysis.get("detected_indicators", [])
    entities = analysis.get("entities", [])
    supporting = analysis.get("supporting_evidence", [])
    conflicting = analysis.get("conflicting_evidence", [])
    reasons = analysis.get("reasons", [])

    family, subfamily, family_conf = _classify_family(
        category, indicators, prediction, ml_confidence,
    )

    nodes, node_types = _build_evidence_nodes(
        supporting, conflicting, entities, indicators, reasons,
    )
    edges = _build_edges(nodes, node_types, indicators, entities)

    evidence_ranks = _rank_evidence(
        nodes, edges, prediction, ml_confidence,
    )

    decision_trace = _build_decision_trace(
        family, subfamily, family_conf, evidence_ranks,
        nodes, edges, prediction, ml_confidence, category,
    )

    summary = _build_graph_summary(family, subfamily, evidence_ranks, category)

    dominant = evidence_ranks["primary"][:3] if evidence_ranks["primary"] else evidence_ranks["supporting"][:2]
    evidence_chain = dominant + evidence_ranks["supporting"][:3]

    graph = {
        "nodes": [
            {"id": n.node_id, "type": n.node_type, "label": n.label, "severity": n.severity}
            for n in nodes[:20]
        ],
        "edges": [
            {
                "source": e.source_id,
                "target": e.target_id,
                "relationship": e.relationship,
                "weight": e.weight,
                "reason": e.reason,
            }
            for e in edges[:30]
        ],
    }

    return ReasoningResult(
        family=family,
        subfamily=subfamily,
        family_confidence=family_conf,
        primary_evidence=evidence_ranks["primary"],
        supporting_evidence=evidence_ranks["supporting"],
        weak_evidence=evidence_ranks["weak"],
        contradictory_evidence=evidence_ranks["contradictory"],
        ignored_evidence=evidence_ranks["ignored"],
        evidence_graph=graph,
        decision_trace=decision_trace,
        reasoning_summary=summary,
        dominant_evidence_chain=[e["label"] for e in evidence_chain],
    )


def refine(analysis: Dict[str, Any], assessment: Dict[str, Any]) -> RefinementResult:
    original_prediction = analysis.get("prediction", ML_LABEL_SAFE)
    original_score = assessment.get("assessment_score", 0)
    original_confidence = assessment.get("assessment_confidence", CONFIDENCE_LOW)

    fp_adjustment, applied_fp = _compute_fp_adjustment(analysis)
    fn_adjustment, applied_fn = _compute_fn_adjustment(analysis)

    refined_score = _adjust_assessment_score(original_score, fp_adjustment, fn_adjustment)

    has_conflict = len(analysis.get("conflicting_evidence", [])) > 0
    refined_confidence = _map_confidence(refined_score, has_conflict)

    fp_overrides_fp = fp_adjustment >= 15 and fn_adjustment == 0
    if fp_overrides_fp and original_prediction == ML_LABEL_SCAM and refined_score < 40:
        refined_prediction = ML_LABEL_SAFE
    else:
        refined_prediction = original_prediction

    fn_overrides = fn_adjustment >= 15 and fp_adjustment == 0
    if fn_overrides and original_prediction == ML_LABEL_SAFE and refined_score >= 15:
        refined_prediction = ML_LABEL_SCAM

    stable, stability_concerns = _check_decision_stability(analysis)

    refined_review_required = assessment.get("review_required", False)
    if not stable and not refined_review_required:
        refined_review_required = True

    all_applied = applied_fp + applied_fn
    summary = _build_refinement_summary(applied_fp, applied_fn, stable)

    return RefinementResult(
        refined_prediction=refined_prediction,
        refined_assessment_score=refined_score,
        refined_assessment_confidence=refined_confidence,
        refined_review_required=refined_review_required,
        decision_stable=stable,
        stability_concerns=stability_concerns,
        applied_rules=all_applied,
        refinement_summary=summary,
    )


def get_all_rules() -> List[Dict[str, Any]]:
    result = []
    for rule in ALL_RULES:
        result.append({
            "rule_id": rule.rule_id,
            "description": rule.description,
            "category": rule.category,
            "priority": rule.priority,
            "confidence_impact": rule.confidence_impact,
            "reason": rule.reason,
        })
    return result


def profile_errors(errors: Dict[str, Any]) -> Dict[str, Any]:
    profile: Dict[str, Any] = {
        "fp_patterns": {},
        "fn_patterns": {},
        "wc_patterns": {},
        "entity_patterns": {},
    }

    for fp in errors.get("false_positives", []):
        text = (fp.get("text", "") or "")[:200].lower()
        category = fp.get("actual_category", "unknown")
        profile["fp_patterns"][category] = profile["fp_patterns"].get(category, 0) + 1

    for fn in errors.get("false_negatives", []):
        text = (fn.get("text", "") or "")[:200].lower()
        category = fn.get("expected_category", "unknown")
        profile["fn_patterns"][category] = profile["fn_patterns"].get(category, 0) + 1

        if any(r in text for r in ["bit", "dot", "hxxp"]):
            profile["fn_patterns"]["obfuscated_url"] = profile["fn_patterns"].get("obfuscated_url", 0) + 1
        if any(u in text for u in ["urgent", "immediately", "asap"]):
            profile["fn_patterns"]["urgency_high"] = profile["fn_patterns"].get("urgency_high", 0) + 1
        if any(c in text for c in ["customer care", "help", "support"]):
            profile["fn_patterns"]["fake_support"] = profile["fn_patterns"].get("fake_support", 0) + 1

    for wc in errors.get("wrong_category", []):
        expected = wc.get("expected_category", "unknown")
        actual = wc.get("actual_category", "unknown")
        key = f"{expected} -> {actual}"
        profile["wc_patterns"][key] = profile["wc_patterns"].get(key, 0) + 1

    for ef in errors.get("entity_failures", []):
        for missing in ef.get("missing_entities", []):
            profile["entity_patterns"][missing] = profile["entity_patterns"].get(missing, 0) + 1

    return profile
