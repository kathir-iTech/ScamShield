from typing import Tuple

from domains.shared.utils import normalise, levenshtein
from config.settings import (
    KNOWLEDGE_PREFIX_MIN_LENGTH,
    KNOWLEDGE_SUFFIX_MIN_LENGTH,
)


def _is_match(
    query: str,
    record_value: str,
    threshold: int = 3,
) -> Tuple[str, float]:
    q = normalise(query)
    r = normalise(record_value)

    if q == r:
        return ("exact", 1.0)
    if len(q) >= KNOWLEDGE_PREFIX_MIN_LENGTH and r.startswith(q):
        return ("prefix", 0.85)
    if len(q) >= KNOWLEDGE_SUFFIX_MIN_LENGTH and r.endswith(q):
        return ("suffix", 0.75)
    if len(r) >= KNOWLEDGE_PREFIX_MIN_LENGTH and q.startswith(r):
        return ("prefix", 0.80)
    if len(r) >= KNOWLEDGE_SUFFIX_MIN_LENGTH and q.endswith(r):
        return ("suffix", 0.70)
    if len(r) >= 3 and r in q:
        return ("contains", 0.65)
    q_words = set(q.split())
    r_words = set(r.split())
    if q_words and r_words:
        overlap = q_words & r_words
        if overlap:
            overlap_ratio = len(overlap) / max(len(q_words), len(r_words))
            if overlap_ratio >= 0.5:
                return ("word_overlap", 0.60 * overlap_ratio)
    dist = levenshtein(q, r)
    max_len = max(len(q), len(r))
    if max_len > 0 and dist <= max(threshold, int(max_len * 0.2)):
        sim = 1.0 - (dist / max_len)
        return ("levenshtein", max(0.5, sim))
    return ("none", 0.0)
