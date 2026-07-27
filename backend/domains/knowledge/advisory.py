from typing import Dict, List

from intelligence.schemas import AdvisoryRecord, HistoricalInvestigation
from domains.shared.models import AdvisoryMatch, HistoricalMatch
from domains.shared.utils import normalise, digits_only
from config.settings import (
    KNOWLEDGE_LEVENSHTEIN_THRESHOLD,
    KNOWLEDGE_MAX_MATCHES,
)
from .matcher import _is_match


def match_advisories(
    query: str,
    advisories_by_source: Dict[str, List[AdvisoryRecord]],
    indicator_type: str = "",
    indicator_value: str = "",
    max_matches: int = KNOWLEDGE_MAX_MATCHES,
) -> List[AdvisoryMatch]:
    results: List[AdvisoryMatch] = []
    q_norm = normalise(query)
    seen_ids: set = set()

    for source, advisories in advisories_by_source.items():
        for adv in advisories:
            if adv.advisory_id in seen_ids:
                continue
            relevance = 0.0
            matched_indicators = []

            for ai in adv.affected_indicators:
                ai_norm = normalise(ai)
                mt, mc = _is_match(q_norm, ai_norm, threshold=2)
                if mt != "none":
                    relevance = max(relevance, mc * 0.8)
                    matched_indicators.append(ai)

            if indicator_value:
                iv_norm = normalise(indicator_value)
                for ai in adv.affected_indicators:
                    ai_norm = normalise(ai)
                    mt, mc = _is_match(iv_norm, ai_norm, threshold=2)
                    if mt != "none":
                        relevance = max(relevance, mc * 0.7)
                        if ai not in matched_indicators:
                            matched_indicators.append(ai)

            if indicator_type and not adv.indicator_types:
                relevance *= 0.9
            elif indicator_type and adv.indicator_types:
                if indicator_type in adv.indicator_types:
                    relevance = max(relevance, 0.5)

            if relevance >= 0.3 or matched_indicators:
                seen_ids.add(adv.advisory_id)
                results.append(AdvisoryMatch(
                    advisory_id=adv.advisory_id,
                    title=adv.title,
                    source=adv.source,
                    date=adv.date,
                    summary=adv.summary,
                    recommendation=adv.recommendation,
                    relevance=round(relevance, 3),
                    severity=adv.severity,
                    matched_indicators=matched_indicators[:5],
                ))

    results.sort(key=lambda x: -x.relevance)
    return results[:max_matches]


def correlate_historical(
    entities: Dict[str, List[Dict]],
    indicators: Dict[str, int],
    dominant_family: str,
    history_records: List[HistoricalInvestigation],
    max_matches: int = KNOWLEDGE_MAX_MATCHES,
) -> List[HistoricalMatch]:
    if not history_records:
        return []
    results: List[HistoricalMatch] = []

    current_phones = set()
    current_domains = set()
    current_upis = set()
    current_emails = set()
    current_keywords = set()

    for etype, entity_list in entities.items():
        for ent in entity_list:
            val = ent.get("value", "").lower().strip() if isinstance(ent, dict) else str(ent).lower().strip()
            if etype == "phone":
                current_phones.add(digits_only(val))
            elif etype in ("url", "domain"):
                current_domains.add(val)
            elif etype == "upi":
                current_upis.add(val)
            elif etype == "email":
                current_emails.add(val)
            elif etype in ("keyword", "indicator"):
                current_keywords.add(val)

    current_indicator_set = set(k.lower().strip() for k in indicators.keys())

    for hist in history_records:
        matched_entities = []
        matched_indicators = []
        hist_phones = set()
        hist_domains = set()
        hist_upis = set()
        hist_emails = set()
        hist_keywords = set()

        for etype, entity_list in hist.entities.items():
            for ent in entity_list:
                val = ent.get("value", "").lower().strip() if isinstance(ent, dict) else str(ent).lower().strip()
                if etype == "phone":
                    hist_phones.add(digits_only(val))
                elif etype in ("url", "domain"):
                    hist_domains.add(val)
                elif etype == "upi":
                    hist_upis.add(val)
                elif etype == "email":
                    hist_emails.add(val)
                elif etype in ("keyword", "indicator"):
                    hist_keywords.add(val)

        shared_phones = current_phones & hist_phones
        for p in shared_phones:
            matched_entities.append({"type": "phone", "value": p, "match_type": "exact"})
        shared_domains = current_domains & hist_domains
        for d in shared_domains:
            matched_entities.append({"type": "domain", "value": d, "match_type": "exact"})
        shared_upis = current_upis & hist_upis
        for u in shared_upis:
            matched_entities.append({"type": "upi", "value": u, "match_type": "exact"})
        shared_emails = current_emails & hist_emails
        for e in shared_emails:
            matched_entities.append({"type": "email", "value": e, "match_type": "exact"})

        shared_indicator_set = current_indicator_set & set(k.lower().strip() for k in hist.indicators.keys())
        for ind in shared_indicator_set:
            matched_indicators.append({"indicator": ind, "match_type": "exact"})

        total_shared = len(matched_entities) + len(matched_indicators)
        if total_shared == 0:
            continue

        campaign_overlap = hist.campaign_detected
        family_match = dominant_family and normalise(dominant_family) == normalise(hist.dominant_family)

        confidence = 0.0
        confidence += min(total_shared * 0.15, 0.6)
        if campaign_overlap:
            confidence += 0.2
        if family_match:
            confidence += 0.15
        confidence = min(confidence, 1.0)

        results.append(HistoricalMatch(
            investigation_id=hist.investigation_id,
            date=hist.date,
            overall_risk=hist.overall_risk,
            overall_score=hist.overall_score,
            dominant_family=hist.dominant_family,
            matched_entities=matched_entities[:5],
            matched_indicators=matched_indicators[:5],
            shared_indicator_count=total_shared,
            campaign_overlap=campaign_overlap,
            confidence=round(confidence, 3),
            summary=hist.summary,
        ))

    results.sort(key=lambda x: -x.confidence)
    return results[:max_matches]
