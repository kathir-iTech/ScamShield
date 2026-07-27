from collections import Counter, defaultdict
from typing import Any, Dict, List, Tuple, Optional


def profile_failure_patterns(
    false_positives: List[Dict],
    false_negatives: List[Dict],
    wrong_category: List[Dict],
    entity_failures: List[Dict],
) -> Dict[str, Any]:
    profile: Dict[str, Any] = {
        "fp_by_category": {},
        "fn_by_category": {},
        "fn_obfuscated_url": 0,
        "fn_urgency_high": 0,
        "fn_fake_support": 0,
        "wc_confusions": {},
        "entity_missing_types": {},
    }

    for fp in false_positives:
        cat = fp.get("actual_category", "unknown") or "unknown"
        profile["fp_by_category"][cat] = profile["fp_by_category"].get(cat, 0) + 1

    for fn in false_negatives:
        cat = fn.get("expected_category", "unknown") or "unknown"
        profile["fn_by_category"][cat] = profile["fn_by_category"].get(cat, 0) + 1
        text = (fn.get("text", "") or "").lower()
        if "bit" in text and "dot" in text:
            profile["fn_obfuscated_url"] += 1
        if any(u in text for u in ["urgent", "immediately", "asap"]):
            profile["fn_urgency_high"] += 1
        if any(c in text for c in ["customer care", "help", "support", "helpline"]):
            profile["fn_fake_support"] += 1

    for wc in wrong_category:
        expected = wc.get("expected_category", "unknown")
        actual = wc.get("actual_category", "unknown")
        key = f"{expected} -> {actual}"
        profile["wc_confusions"][key] = profile["wc_confusions"].get(key, 0) + 1

    for ef in entity_failures:
        for missing in ef.get("missing_entities", []):
            profile["entity_missing_types"][missing] = profile["entity_missing_types"].get(missing, 0) + 1

    return profile


def analyze_errors(
    samples: List[Dict[str, Any]],
    predictions: List[Dict[str, Any]],
) -> Dict[str, Any]:
    false_positives: List[Dict] = []
    false_negatives: List[Dict] = []
    wrong_category: List[Dict] = []
    low_confidence: List[Dict] = []
    entity_failures: List[Dict] = []
    per_class: Dict[str, Dict] = defaultdict(lambda: {"tp": 0, "fp": 0, "fn": 0, "total": 0, "correct": 0})

    for sample, pred in zip(samples, predictions):
        sid = sample["id"]
        expected = sample["expected_prediction"]
        actual = pred.get("prediction", "safe")
        expected_cat = sample.get("expected_category", "Unknown")
        actual_cat = pred.get("scam_category", "Unknown")
        confidence = pred.get("confidence", 0.0)
        expected_entities = set(sample.get("expected_entities", []))
        actual_entity_types = set(e.get("type", "") for e in pred.get("entities", []))

        per_class[expected_cat]["total"] += 1

        is_scam_expected = expected == "scam"
        is_scam_actual = actual == "scam"

        entry = {
            "id": sid,
            "text": sample["text"][:100],
            "expected": expected,
            "actual": actual,
            "confidence": confidence,
            "expected_category": expected_cat,
            "actual_category": actual_cat,
            "difficulty": sample.get("difficulty", "unknown"),
        }

        if is_scam_expected and not is_scam_actual:
            false_negatives.append(entry)
            per_class[expected_cat]["fn"] += 1
        elif not is_scam_expected and is_scam_actual:
            false_positives.append(entry)
            per_class[expected_cat]["fp"] += 1
        elif is_scam_expected and is_scam_actual:
            per_class[expected_cat]["tp"] += 1
            correct = True

        if is_scam_expected and is_scam_actual and expected_cat and actual_cat:
            if expected_cat != actual_cat:
                wrong_category.append(entry)

        if is_scam_expected and confidence < 0.4:
            low_confidence.append(entry)

        if expected_entities:
            found = expected_entities & actual_entity_types
            missing = expected_entities - actual_entity_types
            if missing:
                entity_failures.append({
                    **entry,
                    "expected_entities": list(expected_entities),
                    "found_entities": list(found),
                    "missing_entities": list(missing),
                })

    false_positives.sort(key=lambda x: -x["confidence"])
    false_negatives.sort(key=lambda x: -x["confidence"])
    wrong_category.sort(key=lambda x: x["confidence"])
    low_confidence.sort(key=lambda x: x["confidence"])
    entity_failures.sort(key=lambda x: len(x["missing_entities"]), reverse=True)

    return {
        "false_positives": false_positives[:30],
        "false_negatives": false_negatives[:30],
        "wrong_category": wrong_category[:20],
        "low_confidence": low_confidence[:20],
        "entity_failures": entity_failures[:20],
        "fp_count": len(false_positives),
        "fn_count": len(false_negatives),
        "wc_count": len(wrong_category),
        "lc_count": len(low_confidence),
        "ef_count": len(entity_failures),
        "per_class": dict(per_class),
    }
