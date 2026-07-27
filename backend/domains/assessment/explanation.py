import re
from typing import Dict, List, Tuple

from core.constants import (
    CATEGORY_KEYWORDS,
    CATEGORY_RECOMMENDATIONS,
    CATEGORY_THREATS,
    CRITICAL_INDICATORS,
    HIGH_RISK_INDICATORS,
    HIGH_WEIGHT_KEYWORDS,
    INDICATOR_PATTERNS,
    MEDIUM_WEIGHT_KEYWORDS,
    ML_LABEL_SCAM,
    ML_LABEL_SAFE,
    RISK_HIGH,
    RISK_LOW,
    RISK_MEDIUM,
    SEVERITY_CRITICAL,
    SEVERITY_HIGH,
    SEVERITY_LOW,
    SEVERITY_MEDIUM,
    SEVERITY_VERY_LOW,
    UNKNOWN_CATEGORY,
)
from config.settings import HIGH_CONFIDENCE_THRESHOLD, MEDIUM_CONFIDENCE_THRESHOLD

_INDICATOR_REGEXES: List[Tuple[re.Pattern, str]] = [
    (re.compile(p, re.IGNORECASE), label) for p, label in INDICATOR_PATTERNS
]

_CategoryEntry = Tuple[str, re.Pattern, int]

def _weight_for_keyword(kw: str) -> int:
    if kw in HIGH_WEIGHT_KEYWORDS:
        return 3
    if kw in MEDIUM_WEIGHT_KEYWORDS:
        return 2
    return 1

_CATEGORY_REGEXES: Dict[str, List[_CategoryEntry]] = {}
for cat, keywords in CATEGORY_KEYWORDS.items():
    entries = []
    for kw in keywords:
        pat = r"\b" + re.escape(kw) + r"\b" if " " not in kw else re.escape(kw)
        entries.append((kw, re.compile(pat, re.IGNORECASE), _weight_for_keyword(kw)))
    _CATEGORY_REGEXES[cat] = entries


def detect_category(text: str, reasons: List[str]) -> Tuple[str, float]:
    text_lower = text.lower()
    weighted_scores: Dict[str, int] = {}

    for cat, entries in _CATEGORY_REGEXES.items():
        score = 0
        for kw, pat, weight in entries:
            matches = len(pat.findall(text_lower))
            if matches:
                score += matches * weight
        if score > 0:
            weighted_scores[cat] = score

    for reason in reasons:
        r_lower = reason.lower()
        for cat, entries in _CATEGORY_REGEXES.items():
            for kw, pat, weight in entries:
                if pat.search(r_lower):
                    weighted_scores[cat] = weighted_scores.get(cat, 0) + 2

    if not weighted_scores:
        return UNKNOWN_CATEGORY, 0.0

    best_cat = max(weighted_scores, key=weighted_scores.get)
    total = sum(weighted_scores.values())
    certainty = round(weighted_scores[best_cat] / total, 2) if total > 0 else 0.0
    return best_cat, certainty


def detect_indicators(text: str, reasons: List[str]) -> List[str]:
    seen = set()
    indicators: List[str] = []
    text_lower = text.lower()
    for pattern, label in _INDICATOR_REGEXES:
        if label not in seen and pattern.search(text_lower):
            indicators.append(label)
            seen.add(label)
    for reason in reasons:
        r_lower = reason.lower()
        for pattern, label in _INDICATOR_REGEXES:
            if label not in seen and pattern.search(r_lower):
                indicators.append(label)
                seen.add(label)
    return indicators


def extract_threats(category: str) -> Dict[str, str]:
    return dict(CATEGORY_THREATS.get(category, CATEGORY_THREATS[UNKNOWN_CATEGORY]))


def extract_recommendations(category: str) -> List[str]:
    return list(CATEGORY_RECOMMENDATIONS.get(category, CATEGORY_RECOMMENDATIONS[UNKNOWN_CATEGORY]))


def calculate_severity(
    ml_label: str,
    confidence: float,
    rule_score: float,
    rule_label: str,
    indicators: List[str],
) -> str:
    has_critical = any(i in indicators for i in CRITICAL_INDICATORS)
    indicator_count = len(indicators)
    has_high_risk = any(i in indicators for i in HIGH_RISK_INDICATORS)

    if rule_label == RISK_HIGH and has_critical:
        return SEVERITY_CRITICAL
    if ml_label == ML_LABEL_SCAM and rule_score >= 35 and has_critical:
        return SEVERITY_CRITICAL

    if rule_label == RISK_HIGH:
        return SEVERITY_HIGH
    if ml_label == ML_LABEL_SCAM and confidence > 0.9:
        return SEVERITY_HIGH
    if ml_label == ML_LABEL_SCAM and rule_score >= 20:
        return SEVERITY_HIGH
    if has_critical and (ml_label == ML_LABEL_SCAM or indicator_count >= 2):
        return SEVERITY_HIGH

    if ml_label == ML_LABEL_SCAM or rule_score >= 20:
        return SEVERITY_MEDIUM
    if has_critical:
        return SEVERITY_MEDIUM
    if indicator_count >= 2:
        return SEVERITY_MEDIUM
    if has_high_risk:
        return SEVERITY_MEDIUM
    if rule_score > 0:
        return SEVERITY_LOW
    return SEVERITY_VERY_LOW


def build_summary(
    category: str, severity: str, ml_label: str, rule_label: str, indicators: List[str]
) -> str:
    if ml_label == ML_LABEL_SCAM and rule_label == RISK_HIGH:
        return (
            f"Highly suspicious {category.lower()} detected. "
            "Both ML and rule engine independently confirm scam indicators."
        )
    if ml_label == ML_LABEL_SCAM:
        return (
            f"Suspicious message potentially related to {category.lower()}. "
            "ML classifier detects scam patterns."
        )
    if rule_label == RISK_HIGH:
        return (
            f"Message flagged with high-risk indicators related to {category.lower()}. "
            "Rule engine detects strong scam signals."
        )
    if rule_label == RISK_MEDIUM:
        return (
            f"Message shows moderate risk indicators potentially related to {category.lower()}. "
            "Exercise caution before responding."
        )
    if indicators:
        return (
            f"Message contains some suspicious elements but no confirmed scam classification. "
            f"Detected: {', '.join(indicators[:3])}."
        )
    return "Message appears safe with no significant scam indicators."


def generate_explanation(text: str, analysis_result: dict) -> dict:
    prediction = analysis_result.get("prediction", ML_LABEL_SAFE)
    confidence = analysis_result.get("confidence", 0.0)
    rule_score = analysis_result.get("rule_score", 0.0)
    rule_label = analysis_result.get("rule_label", RISK_LOW)
    reasons = analysis_result.get("reasons", [])

    category, category_confidence = detect_category(text, reasons)
    indicators = detect_indicators(text, reasons)
    severity = calculate_severity(prediction, confidence, rule_score, rule_label, indicators)
    threats = extract_threats(category)
    recommendations = extract_recommendations(category)
    summary = build_summary(category, severity, prediction, rule_label, indicators)

    if prediction == ML_LABEL_SCAM and confidence > HIGH_CONFIDENCE_THRESHOLD:
        confidence_reason = (
            "High confidence because both ML and rule engine independently "
            "classified the message as suspicious."
        )
    elif prediction == ML_LABEL_SCAM:
        confidence_reason = (
            "Moderate confidence based on ML classification and detected scam indicators."
        )
    elif rule_score >= 35:
        confidence_reason = (
            "Low ML confidence but rule engine detected several suspicious indicators."
        )
    else:
        confidence_reason = (
            "No significant scam indicators detected across ML and rule analysis."
        )

    return {
        "summary": summary,
        "risk_level": severity,
        "scam_category": category,
        "confidence_reason": confidence_reason,
        "detected_indicators": indicators,
        "threats": [threats["primary"], threats["secondary"]],
        "recommended_actions": recommendations,
    }
