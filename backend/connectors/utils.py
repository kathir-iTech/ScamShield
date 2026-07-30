import unicodedata
from typing import List


def normalize_indicator(indicator: str, indicator_type: str = "") -> str:
    result = unicodedata.normalize("NFKC", indicator).strip().lower()
    if indicator_type in ("url", "domain"):
        for prefix in ["http://", "https://", "www."]:
            result = result.replace(prefix, "")
        result = result.split("/")[0]
        result = result.split("?")[0]
    elif indicator_type == "phone":
        result = "".join(c for c in result if c.isdigit())
    elif indicator_type == "email":
        result = result.strip().lower()
    return result


def indicators_overlap(
    a_indicators: List[str], b_indicators: List[str]
) -> float:
    if not a_indicators or not b_indicators:
        return 0.0
    a_set = set(normalize_indicator(x) for x in a_indicators)
    b_set = set(normalize_indicator(x) for x in b_indicators)
    if not a_set or not b_set:
        return 0.0
    intersection = a_set & b_set
    return len(intersection) / min(len(a_set), len(b_set))


def merge_evidence(existing: List[dict], new: List[dict]) -> List[dict]:
    seen = set()
    merged = list(existing)
    for item in existing:
        seen.add(str(item))
    for item in new:
        key = str(item)
        if key not in seen:
            seen.add(key)
            merged.append(item)
    return merged


def calculate_aggregate_confidence(scores: List[float]) -> float:
    if not scores:
        return 0.0
    if len(scores) == 1:
        return scores[0]
    weighted_sum = 0.0
    total_weight = 0.0
    for i, score in enumerate(scores):
        weight = 1.0 / (i + 1)
        weighted_sum += score * weight
        total_weight += weight
    result = weighted_sum / total_weight if total_weight > 0 else 0.0
    return min(max(result, 0.0), 1.0)
