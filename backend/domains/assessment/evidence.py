from typing import Dict, FrozenSet, List, Tuple

from core.constants import (
    DECISION_CRITICAL,
    DECISION_HIGH_RISK,
    DECISION_LOW_RISK,
    DECISION_SAFE,
    DECISION_SUSPICIOUS,
    EVIDENCE_CORRELATIONS,
    EVIDENCE_TYPE_CONFLICT,
    EVIDENCE_TYPE_CORRELATION,
    ENTITY_INDICATOR_MAP,
    HIGH_RISK_REASON_KEYWORDS,
    INDICATOR_ACCOUNT_THREAT,
    INDICATOR_BANK_IMPERSONATION,
    INDICATOR_COURIER_CUSTOMS,
    INDICATOR_CRYPTO,
    INDICATOR_CUSTOMER_CARE,
    INDICATOR_GOVT_IMPERSONATION,
    INDICATOR_INVESTMENT_OFFER,
    INDICATOR_JOB_OFFER,
    INDICATOR_KYC_UPDATE,
    INDICATOR_LOAN_EMI,
    INDICATOR_OTP_REQUEST,
    INDICATOR_PAYMENT_REQUEST,
    INDICATOR_PRIZE_LOTTERY,
    INDICATOR_QR_CODE_REQUEST,
    INDICATOR_SHORTENED_URL,
    INDICATOR_SUSPICIOUS_URL,
    INDICATOR_URGENCY_LANGUAGE,
    INDICATOR_UTILITY_BILL,
    ML_LABEL_SAFE,
    ML_LABEL_SCAM,
    PRIORITY_HIGH,
    PRIORITY_LOW,
    PRIORITY_NORMAL,
    PRIORITY_URGENT,
    RISK_HIGH,
    RISK_LOW,
    RISK_MEDIUM,
    RISK_TYPES,
    SEVERITY_HIGH,
    SEVERITY_LOW,
    SEVERITY_MEDIUM,
)
from config.settings import (
    CONFIDENCE_BREAKDOWN_ENTITIES_WEIGHT,
    CONFIDENCE_BREAKDOWN_EXPLANATION_WEIGHT,
    CONFIDENCE_BREAKDOWN_ML_WEIGHT,
    CONFIDENCE_BREAKDOWN_RULES_WEIGHT,
    DECISION_CONFLICT_PENALTY,
    DECISION_HIGH_BONUS,
    DECISION_HIGH_BONUS2_THRESHOLD,
    DECISION_HIGH_BONUS_THRESHOLD,
    DECISION_MAX_WEIGHT,
    EVIDENCE_MAX_HIGH_ENTITIES,
    EVIDENCE_MAX_MEDIUM_ENTITIES,
)

_SEV_MAP: Dict[str, str] = {RISK_HIGH: SEVERITY_HIGH, RISK_MEDIUM: SEVERITY_MEDIUM, RISK_LOW: SEVERITY_LOW}

_INDICATOR_SEVERITY_RULES: List[Tuple[str, str, int]] = [
    (INDICATOR_OTP_REQUEST, SEVERITY_HIGH, 20),
    (INDICATOR_ACCOUNT_THREAT, SEVERITY_HIGH, 20),
    (INDICATOR_PAYMENT_REQUEST, SEVERITY_HIGH, 20),
    (INDICATOR_SUSPICIOUS_URL, SEVERITY_HIGH, 18),
    (INDICATOR_SHORTENED_URL, SEVERITY_HIGH, 18),
    (INDICATOR_QR_CODE_REQUEST, SEVERITY_HIGH, 18),
]

_IndicatorRiskRule = Tuple[str, Dict[str, int], FrozenSet[str]]
_INDICATOR_RISK_RULES: List[_IndicatorRiskRule] = [
    (INDICATOR_OTP_REQUEST, {"credential_theft": 30, "identity_theft": 20}, frozenset()),
    (INDICATOR_BANK_IMPERSONATION, {"credential_theft": 25, "financial_loss": 15}, frozenset()),
    (INDICATOR_PAYMENT_REQUEST, {"financial_loss": 35}, frozenset()),
    (INDICATOR_SUSPICIOUS_URL, {"social_engineering": 25}, frozenset()),
    (INDICATOR_SHORTENED_URL, {"social_engineering": 20}, frozenset({"shortened_url"})),
    (INDICATOR_PRIZE_LOTTERY, {"financial_loss": 25, "social_engineering": 15}, frozenset()),
    (INDICATOR_INVESTMENT_OFFER, {"financial_loss": 30}, frozenset()),
    (INDICATOR_JOB_OFFER, {"financial_loss": 20, "identity_theft": 15}, frozenset()),
    (INDICATOR_GOVT_IMPERSONATION, {"identity_theft": 25, "social_engineering": 15}, frozenset()),
    (INDICATOR_KYC_UPDATE, {"identity_theft": 30, "credential_theft": 20}, frozenset()),
    (INDICATOR_ACCOUNT_THREAT, {"social_engineering": 20}, frozenset()),
    (INDICATOR_CRYPTO, {"financial_loss": 25}, frozenset()),
    (INDICATOR_QR_CODE_REQUEST, {"financial_loss": 20}, frozenset()),
    (INDICATOR_CUSTOMER_CARE, {"social_engineering": 20, "credential_theft": 15}, frozenset()),
    (INDICATOR_COURIER_CUSTOMS, {"financial_loss": 25, "social_engineering": 10}, frozenset()),
    (INDICATOR_UTILITY_BILL, {"financial_loss": 20, "social_engineering": 15}, frozenset()),
    (INDICATOR_LOAN_EMI, {"financial_loss": 20, "identity_theft": 10}, frozenset()),
]

_ENTITY_RISK_RULES: List[Tuple[FrozenSet[str], Dict[str, int]]] = [
    (frozenset({"UPI ID", "upi_id"}), {"financial_loss": 30, "credential_theft": 15}),
    (frozenset({"email"}), {"social_engineering": 15}),
    (frozenset({"phone_indian", "phone_international"}), {"social_engineering": 15}),
]

_CORRELATION_RISK_RULES: List[Tuple[str, Dict[str, int]]] = [
    ("Credential Theft", {"credential_theft": 20}),
    ("Payment Fraud", {"financial_loss": 20}),
    ("Phishing", {"social_engineering": 15, "credential_theft": 15}),
    ("Financial Scam", {"financial_loss": 20}),
]

_DECISION_LEVEL_CUTOFFS: List[Tuple[int, str]] = [
    (80, DECISION_CRITICAL),
    (60, DECISION_HIGH_RISK),
    (35, DECISION_SUSPICIOUS),
    (15, DECISION_LOW_RISK),
    (0, DECISION_SAFE),
]

_PRIORITY_CUTOFFS: List[Tuple[int, str]] = [
    (70, PRIORITY_URGENT),
    (50, PRIORITY_HIGH),
    (25, PRIORITY_NORMAL),
    (0, PRIORITY_LOW),
]


class EvidenceCollector:
    def __init__(self) -> None:
        self.items: List[Dict] = []
        self._next_id: int = 0

    def add(self, etype: str, source: str, desc: str, severity: str, conf: float, weight: int) -> None:
        self._next_id += 1
        self.items.append({
            "id": f"ev_{self._next_id:03d}",
            "type": etype,
            "source": source,
            "description": desc,
            "severity": severity,
            "confidence": round(conf, 2),
            "weight": weight,
        })


def build_evidence(analysis: dict) -> Dict:
    prediction = analysis.get("prediction", ML_LABEL_SAFE)
    confidence = analysis.get("confidence", 0.0)
    rule_score = analysis.get("rule_score", 0.0)
    rule_label = analysis.get("rule_label", RISK_LOW)
    reasons = analysis.get("reasons", [])
    indicators = analysis.get("detected_indicators", [])
    category = analysis.get("scam_category", "Unknown Scam")
    entities = analysis.get("entities", [])
    entity_summary = analysis.get("entity_summary", {})
    entity_risk = analysis.get("entity_risk", {})

    collector = EvidenceCollector()

    collector.add(
        "ml_prediction", "ml",
        f"ML model classifies message as '{prediction}' with {confidence:.0%} confidence",
        SEVERITY_HIGH if prediction == ML_LABEL_SCAM else SEVERITY_LOW,
        confidence,
        20 if prediction == ML_LABEL_SCAM else 0,
    )

    collector.add(
        "rule_score", "rules",
        f"Rule engine score: {rule_score}/100 ({rule_label} risk)",
        _SEV_MAP.get(rule_label, SEVERITY_LOW),
        min(rule_score / 100 + 0.2, 0.99),
        min(int(rule_score * 0.3), 25),
    )

    for reason in reasons:
        desc_lower = reason.lower()
        sev = SEVERITY_MEDIUM
        w = 10
        if any(kw in desc_lower for kw in HIGH_RISK_REASON_KEYWORDS):
            sev = SEVERITY_HIGH
            w = 18
        collector.add("rule_indicator", "rules", reason, sev, 0.80, w)

    indicator_set = set(indicators)
    for indicator in indicators:
        sev = SEVERITY_MEDIUM
        w = 12
        for name, high_sev, high_w in _INDICATOR_SEVERITY_RULES:
            if indicator == name:
                sev = high_sev
                w = high_w
                break
        collector.add("indicator", "explanation", f"Detected: {indicator}", sev, 0.85, w)

    high_entities = entity_risk.get("high", [])
    medium_entities = entity_risk.get("medium", [])

    for ent in high_entities[:EVIDENCE_MAX_HIGH_ENTITIES]:
        collector.add("entity_high", "intel", f"High-risk entity: {ent['type']} ({ent['value']})", SEVERITY_HIGH, 0.90, 22)

    for ent in medium_entities[:EVIDENCE_MAX_MEDIUM_ENTITIES]:
        collector.add("entity_medium", "intel", f"Medium-risk entity: {ent['type']} ({ent['value']})", SEVERITY_MEDIUM, 0.80, 14)

    total_entities = entity_summary.get("total_entities", 0)
    if total_entities >= 3:
        collector.add("entity_volume", "intel", f"Multiple entities detected: {total_entities} total", SEVERITY_MEDIUM, 0.75, 12)

    threat_indicators = entity_summary.get("threat_indicators", [])
    for ti in threat_indicators:
        collector.add("threat_indicator", "intel", f"Threat indicator: {ti}", SEVERITY_HIGH, 0.85, 16)

    correlations = correlate_evidence(indicators, entities)
    for corr in correlations:
        collector.add("correlation", "evidence", corr["description"], SEVERITY_HIGH, 0.88, 22)

    conflicts = detect_conflicts(prediction, confidence, rule_label, rule_score, indicators, entities)
    for conflict in conflicts:
        collector.add("conflict", "evidence", conflict["description"], SEVERITY_MEDIUM, 0.70, 10)

    decision_score = calculate_decision_score(collector.items)
    decision_level = get_decision_level(decision_score)
    reasoning = generate_reasoning(prediction, rule_label, indicators, correlations, conflicts, category)
    confidence_breakdown = build_confidence_breakdown(prediction, confidence, rule_label, rule_score, indicators, entities)
    risk_breakdown = build_risk_breakdown(indicators, entities, category, correlations)
    priority = get_priority(decision_score, decision_level)

    supporting = [e for e in collector.items if e["severity"] in (SEVERITY_HIGH, SEVERITY_MEDIUM) and e["type"] != EVIDENCE_TYPE_CONFLICT]
    conflicting = [e for e in collector.items if e["type"] == EVIDENCE_TYPE_CONFLICT]

    return {
        "decision_score": decision_score,
        "decision_level": decision_level,
        "decision_reasoning": reasoning,
        "supporting_evidence": supporting[:8],
        "conflicting_evidence": conflicting,
        "confidence_breakdown": confidence_breakdown,
        "risk_breakdown": risk_breakdown,
        "recommended_priority": priority,
    }


def correlate_evidence(indicators: List[str], entities: List[Dict]) -> List[Dict]:
    found: List[Dict] = []
    entity_types = {e["type"] for e in entities}
    indicator_set = set(indicators)
    seen = set()

    for key, corr in EVIDENCE_CORRELATIONS.items():
        has_required = corr["required"].issubset(indicator_set) if corr["required"] else True
        if not has_required:
            continue
        optional_matches = corr["optional"] & indicator_set
        optional_from_entities = set()
        for etype, indicator_label in ENTITY_INDICATOR_MAP.items():
            if etype in entity_types:
                optional_from_entities.add(indicator_label)

        all_optional = optional_matches | optional_from_entities
        if len(all_optional) >= corr["min_optional"]:
            if corr["label"] not in seen:
                seen.add(corr["label"])
                found.append({
                    "type": EVIDENCE_TYPE_CORRELATION,
                    "label": corr["label"],
                    "description": corr["description"],
                })
    return found


def detect_conflicts(
    prediction: str, confidence: float, rule_label: str, rule_score: float,
    indicators: List[str], entities: List[Dict],
) -> List[Dict]:
    conflicts: List[Dict] = []
    high_risk_entities = [e for e in entities if e.get("risk") == "HIGH"]

    if prediction == ML_LABEL_SAFE and rule_label == RISK_HIGH:
        conflicts.append({
            "type": "ml_vs_rules",
            "description": "ML classifies as safe but rule engine reports high risk. Rule engine detected strong scam signals that the ML model may have missed.",
        })
    if prediction == ML_LABEL_SAFE and high_risk_entities:
        conflicts.append({
            "type": "ml_vs_entities",
            "description": f"ML classifies as safe but {len(high_risk_entities)} high-risk indicator(s) were extracted from the message.",
        })
    if prediction == ML_LABEL_SAFE and confidence > 0.9 and rule_label == RISK_MEDIUM:
        conflicts.append({
            "type": "high_confidence_safe_with_risk",
            "description": "ML is highly confident the message is safe, but rule engine detected moderate risk signals.",
        })
    if prediction == ML_LABEL_SCAM and rule_label == RISK_LOW and confidence < 0.7:
        conflicts.append({
            "type": "ml_vs_rules_low_conf",
            "description": "ML classifies as scam with low confidence while rule engine found no significant indicators.",
        })
    if prediction == ML_LABEL_SCAM and confidence > 0.9 and not indicators and not high_risk_entities:
        conflicts.append({
            "type": "ml_high_conf_no_evidence",
            "description": "ML is highly confident this is a scam but no concrete indicators or entities were detected.",
        })
    return conflicts


def calculate_decision_score(evidence_list: List[Dict]) -> int:
    if not evidence_list:
        return 0
    total_weight = sum(e["weight"] for e in evidence_list)
    raw = min(total_weight, DECISION_MAX_WEIGHT)
    bonus = 0
    high_count = sum(1 for e in evidence_list if e["severity"] == SEVERITY_HIGH)
    if high_count >= DECISION_HIGH_BONUS_THRESHOLD:
        bonus += DECISION_HIGH_BONUS
    if high_count >= DECISION_HIGH_BONUS2_THRESHOLD:
        bonus += DECISION_HIGH_BONUS
    conflict_count = sum(1 for e in evidence_list if e["type"] == EVIDENCE_TYPE_CONFLICT)
    if conflict_count > 0:
        bonus = max(bonus - DECISION_CONFLICT_PENALTY, 0)
    return min(raw + bonus, 100)


def get_decision_level(score: int) -> str:
    for cutoff, level in _DECISION_LEVEL_CUTOFFS:
        if score >= cutoff:
            return level
    return DECISION_SAFE


def generate_reasoning(
    prediction: str, rule_label: str, indicators: List[str],
    correlations: List[Dict], conflicts: List[Dict], category: str,
) -> str:
    parts: List[str] = []

    if prediction == ML_LABEL_SCAM:
        parts.append("the ML model classifies this message as a scam")
    if rule_label == RISK_HIGH:
        parts.append("the rule engine reports high-risk indicators")
    elif rule_label == RISK_MEDIUM:
        parts.append("the rule engine found moderate risk signals")

    if indicators:
        high_indicators = [i for i in indicators if i in (INDICATOR_OTP_REQUEST, INDICATOR_PAYMENT_REQUEST, INDICATOR_ACCOUNT_THREAT, INDICATOR_SHORTENED_URL, INDICATOR_SUSPICIOUS_URL, INDICATOR_QR_CODE_REQUEST, INDICATOR_BANK_IMPERSONATION)]
        if high_indicators:
            parts.append(f"detected {', '.join(high_indicators[:4]).lower()}")

    if correlations:
        corr_labels = [c["label"] for c in correlations[:3]]
        parts.append(f"evidence correlates to {', '.join(corr_labels).lower()}")

    if conflicts and prediction == ML_LABEL_SAFE:
        parts.append("however there is conflicting evidence that warrants caution")

    base = "The message combines " if parts else "No significant indicators were detected in this message."
    if parts:
        base = "The message combines " + ", ".join(parts) + ". "

    if correlations:
        base += f"Multiple evidence streams support a {correlations[0]['label'].lower()} assessment."
    elif prediction == ML_LABEL_SCAM:
        base += "Multiple high-confidence indicators support a scam assessment."
    elif rule_label != RISK_LOW:
        base += "Exercise caution when responding to this message."
    else:
        base = "No significant scam indicators were detected. The message appears benign."

    return base


def build_confidence_breakdown(
    prediction: str, confidence: float, rule_label: str, rule_score: float,
    indicators: List[str], entities: List[Dict],
) -> Dict:
    ml_score = round(confidence * 100)
    if rule_label == RISK_HIGH:
        rules_score = 85
    elif rule_label == RISK_MEDIUM:
        rules_score = 55
    else:
        rules_score = 15

    entity_count = len(entities)
    if entity_count >= 4:
        entities_score = 80
    elif entity_count >= 2:
        entities_score = 55
    elif entity_count >= 1:
        entities_score = 30
    else:
        entities_score = 10

    indicator_count = len(indicators)
    if indicator_count >= 4:
        explanation_score = 85
    elif indicator_count >= 2:
        explanation_score = 60
    elif indicator_count >= 1:
        explanation_score = 35
    else:
        explanation_score = 10

    overall = round(
        ml_score * CONFIDENCE_BREAKDOWN_ML_WEIGHT
        + rules_score * CONFIDENCE_BREAKDOWN_RULES_WEIGHT
        + entities_score * CONFIDENCE_BREAKDOWN_ENTITIES_WEIGHT
        + explanation_score * CONFIDENCE_BREAKDOWN_EXPLANATION_WEIGHT
    )

    return {
        "ml": ml_score,
        "rules": rules_score,
        "entities": entities_score,
        "explanation": explanation_score,
        "overall": overall,
    }


def build_risk_breakdown(
    indicators: List[str], entities: List[Dict], category: str, correlations: List[Dict],
) -> Dict:
    risks = {k: 0 for k in RISK_TYPES}
    indicator_set = set(indicators)
    entity_types = {e["type"] for e in entities}
    corr_labels = {c["label"] for c in correlations}

    for indicator, risk_map, entity_types_needed in _INDICATOR_RISK_RULES:
        if indicator in indicator_set or (entity_types_needed and entity_types_needed & entity_types):
            for key, value in risk_map.items():
                risks[key] += value

    for entity_types_required, risk_map in _ENTITY_RISK_RULES:
        if entity_types_required & entity_types:
            for key, value in risk_map.items():
                risks[key] += value

    for corr_label, risk_map in _CORRELATION_RISK_RULES:
        if corr_label in corr_labels:
            for key, value in risk_map.items():
                risks[key] += value

    for k in risks:
        risks[k] = min(risks[k], 100)

    return risks


def get_priority(score: int, level: str) -> str:
    for cutoff, priority in _PRIORITY_CUTOFFS:
        if score >= cutoff:
            return priority
    return PRIORITY_LOW
