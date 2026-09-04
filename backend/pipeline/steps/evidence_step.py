from typing import Any

from domains.assessment.evidence import build_evidence
from domains.assessment.explanation import derive_threats_from_risk_breakdown

from ..step import AnalysisStep


class EvidenceStep(AnalysisStep):
    def __init__(self) -> None:
        super().__init__(step_id="evidence", name="Evidence Gathering", priority=50, dependencies=["intelligence"])

    def execute(self, context: Any) -> Any:
        evidence = build_evidence(dict(context.shared))
        context.data.decision_score = evidence["decision_score"]
        context.data.decision_level = evidence["decision_level"]
        context.data.decision_reasoning = evidence["decision_reasoning"]
        context.data.supporting_evidence = evidence["supporting_evidence"]
        context.data.conflicting_evidence = evidence["conflicting_evidence"]
        context.data.confidence_breakdown = evidence["confidence_breakdown"]
        context.data.risk_breakdown = evidence["risk_breakdown"]
        context.data.recommended_priority = evidence["recommended_priority"]
        # Evidence-based threat derivation: override category-based threats with
        # real dimension scores when any dimension is nonzero; fallback otherwise.
        try:
            derived = derive_threats_from_risk_breakdown(
                context.data.scam_category, evidence["risk_breakdown"]
            )
            context.data.threats = derived
        except Exception:
            pass
        return self._ok({
            "decision_score": evidence["decision_score"],
            "decision_level": evidence["decision_level"],
            "decision_reasoning": evidence["decision_reasoning"],
            "supporting_evidence": evidence["supporting_evidence"],
            "conflicting_evidence": evidence["conflicting_evidence"],
            "confidence_breakdown": evidence["confidence_breakdown"],
            "risk_breakdown": evidence["risk_breakdown"],
            "recommended_priority": evidence["recommended_priority"],
            "threats": context.data.threats,
        })
