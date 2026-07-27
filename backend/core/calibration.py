import math
from typing import Dict, List, Optional, Tuple


LOW_CONFIDENCE_THRESHOLD: float = 0.4
MEDIUM_CONFIDENCE_THRESHOLD: float = 0.6
HIGH_CONFIDENCE_THRESHOLD: float = 0.8

SCORING_WEIGHTS: Dict[str, float] = {
    "ml_confidence": 0.35,
    "rule_score": 0.25,
    "entity_risk": 0.20,
    "explanation_coherence": 0.10,
    "threat_intel": 0.10,
}


def calibrate_confidence(
    raw_confidence: float,
    rules_contribution: float = 0.0,
    entity_risk: float = 0.0,
    historical_fpr: float = 0.0,
) -> float:
    adjusted = raw_confidence * (1.0 - historical_fpr * 0.3)
    boost = (rules_contribution * 0.15 + entity_risk * 0.10)
    adjusted = min(1.0, max(0.0, adjusted + boost))
    return round(adjusted, 4)


def confidence_band(confidence: float) -> str:
    if confidence >= HIGH_CONFIDENCE_THRESHOLD:
        return "HIGH"
    if confidence >= MEDIUM_CONFIDENCE_THRESHOLD:
        return "MEDIUM"
    if confidence >= LOW_CONFIDENCE_THRESHOLD:
        return "LOW"
    return "VERY_LOW"


def recalibrate_thresholds(
    y_true: List[int],
    y_scores: List[float],
    target_fpr: float = 0.10,
) -> Tuple[float, float, float]:
    from sklearn.metrics import roc_curve
    fpr, tpr, thresholds = roc_curve(y_true, y_scores)
    best_idx = -1
    best_f1 = 0.0
    for i in range(len(thresholds)):
        if fpr[i] <= target_fpr:
            tp = tpr[i] * sum(y_true)
            fp = fpr[i] * (len(y_true) - sum(y_true))
            fn = sum(y_true) - tp
            prec = tp / (tp + fp) if (tp + fp) > 0 else 0.0
            rec = tp / (tp + fn) if (tp + fn) > 0 else 0.0
            f1 = 2 * prec * rec / (prec + rec) if (prec + rec) > 0 else 0.0
            if f1 > best_f1:
                best_f1 = f1
                best_idx = i
    if best_idx >= 0:
        return thresholds[best_idx], fpr[best_idx], tpr[best_idx]
    return 0.5, 0.0, 0.0


def optimize_scoring_weights(
    y_true: List[int],
    ml_scores: List[float],
    rule_scores: List[float],
    entity_scores: List[float],
    explanation_scores: List[float],
    threat_scores: List[float],
) -> Dict[str, float]:
    from sklearn.metrics import f1_score
    from itertools import product

    weight_candidates = [0.15, 0.20, 0.25, 0.30, 0.35, 0.40]
    best_weights = SCORING_WEIGHTS.copy()
    best_f1 = 0.0

    for ml_w, rule_w, entity_w in product(weight_candidates, repeat=3):
        remaining = 1.0 - (ml_w + rule_w + entity_w)
        if remaining < 0.05:
            continue
        expl_w = round(remaining * 0.5, 2)
        threat_w = round(remaining - expl_w, 2)
        if abs(ml_w + rule_w + entity_w + expl_w + threat_w - 1.0) > 0.01:
            continue

        final_scores = [
            ml * ml_w + rule * rule_w + entity * entity_w + expl * expl_w + threat * threat_w
            for ml, rule, entity, expl, threat in zip(
                ml_scores, rule_scores, entity_scores, explanation_scores, threat_scores
            )
        ]
        preds = [1 if s >= 0.5 else 0 for s in final_scores]
        f1 = f1_score(y_true, preds)
        if f1 > best_f1:
            best_f1 = f1
            best_weights = {
                "ml_confidence": ml_w,
                "rule_score": rule_w,
                "entity_risk": entity_w,
                "explanation_coherence": expl_w,
                "threat_intel": threat_w,
            }
    return best_weights


def recalibrate_final_score(
    final_score: float,
    ml_confidence: float = 0.0,
    rule_confidence: float = 0.0,
    has_url: bool = False,
    has_urgency: bool = False,
    has_phone: bool = False,
) -> float:
    adjusted = float(final_score)
    if has_url and ml_confidence < 0.3 and rule_confidence < 0.3:
        adjusted = max(0.0, adjusted - 15.0)
    if has_urgency and not has_url and not has_phone:
        adjusted = max(0.0, adjusted - 10.0)
    if ml_confidence >= 0.9:
        adjusted = min(100.0, adjusted + 5.0)
    if rule_confidence < 0.2 and ml_confidence < 0.3:
        adjusted = max(0.0, adjusted - 20.0)
    return round(min(100.0, max(0.0, adjusted)), 1)
