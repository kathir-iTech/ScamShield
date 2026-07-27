from typing import Any, Dict, List, Optional, Tuple

from core.constants import (
    ML_LABEL_SAFE,
    ML_LABEL_SCAM,
    RISK_HIGH,
    RISK_MEDIUM,
    RISK_LOW,
    UNKNOWN_CATEGORY,
)
from domains.shared.models import EvidenceNode, EvidenceEdge


SCAM_FAMILY_TAXONOMY: Dict[str, Dict[str, Any]] = {
    "Financial Fraud": {
        "subfamilies": {
            "Banking": frozenset({
                "Bank KYC Scam", "Account Suspension", "OTP Scam",
            }),
            "UPI": frozenset({
                "UPI Scam", "QR Code Scam",
            }),
            "Loan": frozenset({
                "Loan Scam",
            }),
            "Investment": frozenset({
                "Investment Scam",
            }),
            "Crypto": frozenset({
                "Crypto Scam",
            }),
        },
        "indicators": frozenset({
            "Payment Request", "Bank Impersonation", "Account Threat",
            "Suspicious URL", "UPI ID", "Payment App Mention",
            "Investment Offer", "Cryptocurrency Mention", "Loan/EMI Mention",
            "QR Code Request",
        }),
    },
    "Credential Theft": {
        "subfamilies": {
            "KYC": frozenset({
                "Bank KYC Scam", "Phishing",
            }),
            "OTP": frozenset({
                "OTP Scam",
            }),
            "Fake Login": frozenset({
                "Phishing",
            }),
            "Identity Theft": frozenset({
                "Government Scheme Scam", "Job Scam",
            }),
        },
        "indicators": frozenset({
            "OTP Request", "KYC Update Request", "Suspicious URL",
            "Bank Impersonation", "Government Impersonation", "Job Offer",
        }),
    },
    "Social Engineering": {
        "subfamilies": {
            "Fake Support": frozenset({
                "Fake Customer Care", "Fake Support",
            }),
            "Government": frozenset({
                "Government Scheme Scam",
            }),
            "Delivery": frozenset({
                "Courier Scam",
            }),
            "Customs": frozenset({
                "Customs Scam",
            }),
        },
        "indicators": frozenset({
            "Urgency Language", "Courier/Customs Mention",
            "Government Impersonation", "Customer Care Impersonation",
            "Payment Request", "Suspicious URL",
        }),
    },
    "Consumer Fraud": {
        "subfamilies": {
            "Lottery": frozenset({
                "Lottery Scam",
            }),
            "Subscription": frozenset({
                "Subscription Scam", "Electricity Bill Scam",
            }),
            "Prize": frozenset({
                "Lottery Scam",
            }),
        },
        "indicators": frozenset({
            "Prize/Lottery Mention", "Payment Request",
            "Urgency Language", "Utility Bill Mention",
        }),
    },
    "Legitimate": {
        "subfamilies": {
            "Safe": frozenset({"Legitimate"}),
        },
        "indicators": frozenset(),
    },
}


def _extract_entity_types(entities: List[Dict]) -> Dict[str, List[str]]:
    by_type: Dict[str, List[str]] = {}
    for e in entities:
        etype = e.get("type", "unknown")
        value = e.get("value", "")
        if etype not in by_type:
            by_type[etype] = []
        by_type[etype].append(value)
    return by_type


def _evidence_label_for_type(etype: str) -> str:
    mapping = {
        "url": "URL", "shortened_url": "URL", "suspicious_tld": "URL",
        "email": "Email", "phone_indian": "Phone", "phone_international": "Phone",
        "upi_id": "UPI", "bank_name": "Bank", "government_entity": "Government",
        "currency_amount": "Currency", "otp_code": "OTP", "qr_keyword": "QR",
        "ip_address": "IP", "social_handle": "Social",
        "ifsc_code": "Bank", "bank_account": "Bank",
        "tracking_id": "Tracking", "transaction_id": "Transaction",
    }
    return mapping.get(etype, "Entity")


def _classify_family(
    category: str,
    indicators: List[str],
    prediction: str,
    confidence: float,
) -> Tuple[str, str, float]:
    if prediction == ML_LABEL_SAFE and not indicators:
        return "Legitimate", "Safe", 0.95

    indicator_set = set(indicator.lower() for indicator in indicators)
    scores: Dict[str, float] = {}
    subfamily_scores: Dict[str, Dict[str, float]] = {}
    for family_name, family_info in SCAM_FAMILY_TAXONOMY.items():
        if family_name == "Legitimate":
            continue
        family_score = 0.0
        matched = family_info["indicators"] & indicator_set
        if matched:
            family_score += len(matched) * 20.0
        for sub_name, sub_categories in family_info["subfamilies"].items():
            if category in sub_categories:
                family_score += 35.0
                if sub_name not in subfamily_scores.setdefault(family_name, {}):
                    subfamily_scores[family_name][sub_name] = 0.0
                subfamily_scores[family_name][sub_name] += 35.0
        if family_score > 0:
            scores[family_name] = family_score

    if category == UNKNOWN_CATEGORY and scores:
        scores = {k: v * 0.5 for k, v in scores.items()}

    if not scores:
        if prediction == ML_LABEL_SCAM:
            return "Financial Fraud", "Banking", 0.4 + confidence * 0.3
        return "Legitimate", "Safe", 0.6

    best_family = max(scores, key=scores.get)
    best_family_score = scores[best_family]
    total_score = sum(scores.values()) or 1
    family_conf = min(best_family_score / max(total_score, 1), 1.0)

    best_subfamily = "General"
    best_sub_conf = 0.0
    if best_family in subfamily_scores:
        subs = subfamily_scores[best_family]
        if subs:
            best_subfamily = max(subs, key=subs.get)
            best_sub_conf = subs[best_subfamily] / max(best_family_score, 1)

    if prediction == ML_LABEL_SCAM:
        family_conf = max(family_conf, confidence * 0.6)
    family_conf = min(family_conf, 1.0)

    return best_family, best_subfamily, round(family_conf, 3)


def _build_evidence_nodes(
    supporting: List[Dict],
    conflicting: List[Dict],
    entities: List[Dict],
    indicators: List[str],
    reasons: List[str],
) -> Tuple[List[EvidenceNode], Dict[str, str]]:
    nodes: List[EvidenceNode] = []
    entity_index: Dict[str, str] = {}
    node_counter: int = 0

    for ev in supporting:
        node_counter += 1
        nid = f"n_{node_counter:03d}"
        nodes.append(EvidenceNode(
            node_id=nid,
            node_type=ev.get("type", "evidence"),
            label=ev.get("description", f"Evidence item")[:80],
            severity=ev.get("severity", "MEDIUM"),
            weight=float(ev.get("weight", 5)),
            confidence=ev.get("confidence", 0.5),
            source=ev.get("source", "unknown"),
            description=ev.get("description", ""),
        ))
        entity_index[nid] = ev.get("type", "evidence")

    for ev in conflicting:
        node_counter += 1
        nid = f"n_{node_counter:03d}"
        nodes.append(EvidenceNode(
            node_id=nid,
            node_type="conflict",
            label=ev.get("description", "Conflicting evidence")[:80],
            severity="MEDIUM",
            weight=8.0,
            confidence=0.7,
            source="evidence",
            description=ev.get("description", ""),
        ))
        entity_index[nid] = "conflict"

    entity_types = _extract_entity_types(entities)
    for etype, values in entity_types.items():
        node_counter += 1
        nid = f"n_{node_counter:03d}"
        label = _evidence_label_for_type(etype)
        nodes.append(EvidenceNode(
            node_id=nid,
            node_type=etype,
            label=f"{label}: {', '.join(values[:2])}",
            severity="HIGH" if etype in ("shortened_url", "suspicious_tld", "otp_code") else "MEDIUM",
            weight=6.0 if etype in ("shortened_url", "suspicious_tld") else 4.0,
            confidence=0.85,
            source="intel",
            description=f"{etype} entity: {', '.join(values[:3])}",
        ))
        entity_index[nid] = etype

    for indicator in indicators:
        node_counter += 1
        nid = f"n_{node_counter:03d}"
        nodes.append(EvidenceNode(
            node_id=nid,
            node_type="indicator",
            label=f"Indicator: {indicator}",
            severity="HIGH" if indicator in (
                "OTP Request", "Payment Request", "Account Threat",
                "Suspicious URL", "QR Code Request",
            ) else "MEDIUM",
            weight=7.0 if indicator in (
                "OTP Request", "Payment Request", "Account Threat",
            ) else 5.0,
            confidence=0.85,
            source="explanation",
            description=f"Detected indicator: {indicator}",
        ))
        entity_index[nid] = indicator

    return nodes, entity_index


def _build_edges(
    nodes: List[EvidenceNode],
    node_types: Dict[str, str],
    indicators: List[str],
    entities: List[Dict],
) -> List[EvidenceEdge]:
    edges: List[EvidenceEdge] = []
    indicator_set = set(indicators)
    entity_types = {e.get("type", "") for e in entities}

    for i, ni in enumerate(nodes):
        for nj in nodes[i + 1:]:
            ti = node_types.get(ni.node_id, "")
            tj = node_types.get(nj.node_id, "")
            if ti == "conflict" or tj == "conflict":
                edges.append(EvidenceEdge(
                    source_id=ni.node_id,
                    target_id=nj.node_id,
                    relationship="contradicts",
                    weight=0.3,
                    confidence=0.7,
                    reason="Conflicting evidence detected",
                ))
                continue
            if ti == tj and ti not in ("conflict", ""):
                edges.append(EvidenceEdge(
                    source_id=ni.node_id,
                    target_id=nj.node_id,
                    relationship="duplicates",
                    weight=0.2,
                    confidence=0.8,
                    reason=f"Same evidence type: {ti}",
                ))
                continue
            _strengthening = {
                "ml_prediction": {"rule_score", "indicator", "correlation"},
                "rule_score": {"indicator", "entity_high", "correlation"},
                "indicator": {"rule_indicator", "correlation"},
                "correlation": {"entity_high", "entity_medium"},
            }
            if ti in _strengthening and tj in _strengthening[ti]:
                edges.append(EvidenceEdge(
                    source_id=ni.node_id,
                    target_id=nj.node_id,
                    relationship="strengthens",
                    weight=0.4,
                    confidence=0.75,
                    reason=f"{ti.replace('_', ' ')} strengthens {tj.replace('_', ' ')}",
                ))
                continue
            edges.append(EvidenceEdge(
                source_id=ni.node_id,
                target_id=nj.node_id,
                relationship="supports",
                weight=0.15,
                confidence=0.6,
                reason="General supporting relationship",
            ))

    has_urgency = "Urgency Language" in indicator_set
    has_payment = "Payment Request" in indicator_set
    has_url = any(e in entity_types for e in ("url", "shortened_url", "suspicious_tld"))
    has_bank = "Bank Impersonation" in indicator_set
    has_govt = "Government Impersonation" in indicator_set
    has_otp = "OTP Request" in indicator_set
    has_qr = "QR Code Request" in indicator_set

    if has_urgency and has_payment and has_url:
        edges.append(EvidenceEdge(
            source_id="synthetic_001",
            target_id="synthetic_002",
            relationship="strengthens",
            weight=0.8,
            confidence=0.85,
            reason="Urgency + Payment + URL forms strong scam pattern",
        ))

    if has_bank and has_url and has_otp:
        edges.append(EvidenceEdge(
            source_id="synthetic_003",
            target_id="synthetic_004",
            relationship="strengthens",
            weight=0.85,
            confidence=0.9,
            reason="Bank impersonation + URL + OTP indicates credential theft",
        ))

    if has_govt and has_url:
        edges.append(EvidenceEdge(
            source_id="synthetic_005",
            target_id="synthetic_006",
            relationship="strengthens",
            weight=0.6,
            confidence=0.7,
            reason="Government reference with URL suggests phishing",
        ))

    if has_qr and has_payment:
        edges.append(EvidenceEdge(
            source_id="synthetic_007",
            target_id="synthetic_008",
            relationship="strengthens",
            weight=0.75,
            confidence=0.8,
            reason="QR code with payment request indicates QR scam",
        ))

    return edges


def _rank_evidence(
    nodes: List[EvidenceNode],
    edges: List[EvidenceEdge],
    prediction: str,
    ml_confidence: float,
) -> Dict[str, List[Dict]]:
    node_importance: List[Tuple[float, EvidenceNode]] = []
    for node in nodes:
        importance = node.weight * node.confidence
        if node.severity == "HIGH":
            importance *= 1.5
        if node.source == "ml" and prediction == ML_LABEL_SCAM:
            importance += ml_confidence * 10
        node_importance.append((importance, node))

    node_importance.sort(key=lambda x: -x[0])
    threshold_high = 8.0
    threshold_medium = 4.0

    primary: List[Dict] = []
    supporting: List[Dict] = []
    weak: List[Dict] = []
    contradictory: List[Dict] = []
    ignored: List[Dict] = []

    seen_types: set = set()
    for score, node in node_importance:
        entry = {
            "node_id": node.node_id,
            "type": node.node_type,
            "label": node.label,
            "severity": node.severity,
            "weight": round(node.weight, 1),
            "confidence": node.confidence,
            "source": node.source,
            "importance": round(score, 2),
        }
        ntype = node.node_type
        if ntype == "conflict":
            contradictory.append(entry)
        elif score >= threshold_high:
            primary.append(entry)
            seen_types.add(ntype)
        elif score >= threshold_medium:
            supporting.append(entry)
            seen_types.add(ntype)
        elif ntype in seen_types:
            ignored.append(entry)
        else:
            weak.append(entry)

    return {
        "primary": primary[:5],
        "supporting": supporting[:8],
        "weak": weak[:5],
        "contradictory": contradictory[:5],
        "ignored": ignored[:5],
    }


def _build_decision_trace(
    family: str,
    subfamily: str,
    family_conf: float,
    evidence_ranks: Dict[str, List[Dict]],
    nodes: List[EvidenceNode],
    edges: List[EvidenceEdge],
    prediction: str,
    ml_confidence: float,
    category: str,
) -> Dict:
    steps: List[Dict] = []
    steps.append({
        "step": 1,
        "action": "Evidence collection",
        "detail": f"Collected {len(nodes)} evidence items from pipeline stages",
    })
    steps.append({
        "step": 2,
        "action": "Relationship detection",
        "detail": f"Identified {len(edges)} relationships between evidence items",
    })
    steps.append({
        "step": 3,
        "action": "Family classification",
        "detail": f"Classified as {family} > {subfamily} (confidence: {family_conf:.1%})",
    })
    steps.append({
        "step": 4,
        "action": "Evidence ranking",
        "detail": (
            f"Primary: {len(evidence_ranks['primary'])}, "
            f"Supporting: {len(evidence_ranks['supporting'])}, "
            f"Weak: {len(evidence_ranks['weak'])}, "
            f"Contradictory: {len(evidence_ranks['contradictory'])}, "
            f"Ignored: {len(evidence_ranks['ignored'])}"
        ),
    })
    contradiction_count = len(evidence_ranks["contradictory"])
    if contradiction_count > 0:
        steps.append({
            "step": 5,
            "action": "Contradiction resolution",
            "detail": f"Reducing confidence due to {contradiction_count} contradictory signal(s)",
        })

    dominant = evidence_ranks["primary"][:3] if evidence_ranks["primary"] else evidence_ranks["supporting"][:2]
    discarded = evidence_ranks["ignored"] + evidence_ranks["weak"][:3]

    conf_adjustment = 0.0
    if contradiction_count > 0:
        conf_adjustment -= min(contradiction_count * 0.05, 0.2)
    if len(evidence_ranks["primary"]) >= 2:
        conf_adjustment += 0.05
    if prediction == ML_LABEL_SCAM and ml_confidence > 0.8:
        conf_adjustment += 0.05

    return {
        "reasoning_steps": steps,
        "graph_summary": {
            "total_nodes": len(nodes),
            "total_edges": len(edges),
            "node_types": {t: sum(1 for n in nodes if n.node_type == t) for t in set(n.node_type for n in nodes)},
            "edge_relationships": {r: sum(1 for e in edges if e.relationship == r) for r in set(e.relationship for e in edges)},
        },
        "dominant_evidence": [e["label"] for e in dominant],
        "discarded_evidence": [e["label"] for e in discarded],
        "evidence_chain": [e["label"] for e in (dominant + evidence_ranks["supporting"][:3])],
        "confidence_adjustments": {
            "family_classification": family_conf,
            "contradiction_penalty": round(-min(contradiction_count * 0.05, 0.2), 3),
            "evidence_strength_bonus": round(conf_adjustment, 3),
            "net_assessment_impact": round(conf_adjustment - min(contradiction_count * 0.05, 0.2), 3),
        },
    }


def _build_summary(
    family: str,
    subfamily: str,
    evidence_ranks: Dict[str, List[Dict]],
    category: str,
) -> str:
    primary_count = len(evidence_ranks["primary"])
    supporting_count = len(evidence_ranks["supporting"])
    contradiction_count = len(evidence_ranks["contradictory"])
    cat_display = category if category != UNKNOWN_CATEGORY else "an unknown scam type"

    parts = [
        f"Reasoning classifies this message under {family} > {subfamily}."
    ]
    if primary_count > 0:
        parts.append(f"{primary_count} primary evidence item(s) support this classification.")
    if supporting_count > 0:
        parts.append(f"{supporting_count} additional piece(s) of supporting evidence were found.")
    if contradiction_count > 0:
        parts.append(f"However, {contradiction_count} contradictory signal(s) reduce confidence.")
    if cat_display:
        parts.append(f"The detected category is {cat_display}.")

    return " ".join(parts)
