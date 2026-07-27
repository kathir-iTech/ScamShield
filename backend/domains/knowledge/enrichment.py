from typing import Dict, List

from domains.shared.models import KnowledgeMatch, AdvisoryMatch, HistoricalMatch
from config.settings import KNOWLEDGE_MAX_MATCHES
from .search import (
    search_by_url,
    search_by_domain,
    search_by_phone,
    search_by_email,
    search_by_upi,
    search_by_bank,
    search_by_keywords,
)
from .advisory import match_advisories, correlate_historical


def enrich_entities(
    entities: List[Dict],
    detected_indicators: List[str],
    records_data: Dict,
    max_matches: int = KNOWLEDGE_MAX_MATCHES,
) -> Dict:
    patterns = records_data.get("patterns", [])
    advisories = records_data.get("advisories", {})
    watchlists = records_data.get("watchlists", [])
    examples = records_data.get("examples", [])
    all_records = patterns + watchlists + examples

    knowledge_matches: List[Dict] = []
    advisory_matches: List[Dict] = []

    for ent in entities:
        etype = ent.get("type", "")
        value = ent.get("value", "")

        if etype in ("url",):
            matches = search_by_url(value, all_records, max_matches)
            for m in matches:
                km = m.to_dict()
                if km not in knowledge_matches:
                    knowledge_matches.append(km)
            advisories_result = match_advisories(value, advisories, indicator_type="url", indicator_value=value, max_matches=max_matches)
            for a in advisories_result:
                am = a.to_dict()
                if am not in advisory_matches:
                    advisory_matches.append(am)

        elif etype in ("domain",):
            matches = search_by_domain(value, all_records, max_matches)
            for m in matches:
                km = m.to_dict()
                if km not in knowledge_matches:
                    knowledge_matches.append(km)
            advisories_result = match_advisories(value, advisories, indicator_type="domain", indicator_value=value, max_matches=max_matches)
            for a in advisories_result:
                am = a.to_dict()
                if am not in advisory_matches:
                    advisory_matches.append(am)

        elif etype in ("phone_indian", "phone_international", "phone"):
            matches = search_by_phone(value, all_records, max_matches)
            for m in matches:
                km = m.to_dict()
                if km not in knowledge_matches:
                    knowledge_matches.append(km)
            advisories_result = match_advisories(value, advisories, indicator_type="phone", indicator_value=value, max_matches=max_matches)
            for a in advisories_result:
                am = a.to_dict()
                if am not in advisory_matches:
                    advisory_matches.append(am)

        elif etype == "email":
            matches = search_by_email(value, all_records, max_matches)
            for m in matches:
                km = m.to_dict()
                if km not in knowledge_matches:
                    knowledge_matches.append(km)

        elif etype == "upi_id":
            matches = search_by_upi(value, all_records, max_matches)
            for m in matches:
                km = m.to_dict()
                if km not in knowledge_matches:
                    knowledge_matches.append(km)

        elif etype in ("bank_name", "bank_account", "ifsc_code"):
            matches = search_by_bank(value, all_records, max_matches)
            for m in matches:
                km = m.to_dict()
                if km not in knowledge_matches:
                    knowledge_matches.append(km)

    keyword_matches = search_by_keywords(detected_indicators, all_records, max_matches)
    for m in keyword_matches:
        km = m.to_dict()
        if km not in knowledge_matches:
            knowledge_matches.append(km)

    for ind in detected_indicators:
        advisories_result = match_advisories(ind, advisories, indicator_type="keyword", indicator_value=ind, max_matches=max_matches)
        for a in advisories_result:
            am = a.to_dict()
            if am not in advisory_matches:
                advisory_matches.append(am)

    knowledge_matches.sort(key=lambda x: -x["confidence"])
    advisory_matches.sort(key=lambda x: -x["relevance"])

    return {
        "knowledge_matches": knowledge_matches[:max_matches],
        "advisory_references": advisory_matches[:max_matches],
        "match_count": len(knowledge_matches),
        "advisory_count": len(advisory_matches),
    }


def enrich_investigation(
    merged_entities: Dict[str, List[Dict]],
    repeated_indicators: Dict[str, int],
    dominant_family: str,
    records_data: Dict,
    max_matches: int = KNOWLEDGE_MAX_MATCHES,
) -> Dict:
    patterns = records_data.get("patterns", [])
    advisories = records_data.get("advisories", {})
    watchlists = records_data.get("watchlists", [])
    examples = records_data.get("examples", [])
    history = records_data.get("history", [])
    all_records = patterns + watchlists + examples

    knowledge_matches: List[Dict] = []
    advisory_matches: List[Dict] = []
    seen_km: set = set()
    seen_am: set = set()

    for etype, entity_list in merged_entities.items():
        for ent in entity_list:
            value = ent.get("value", "") if isinstance(ent, dict) else str(ent)
            if etype in ("url",):
                matches = search_by_url(value, all_records, max_matches)
            elif etype == "domain":
                matches = search_by_domain(value, all_records, max_matches)
            elif etype == "phone":
                matches = search_by_phone(value, all_records, max_matches)
            elif etype == "email":
                matches = search_by_email(value, all_records, max_matches)
            elif etype == "upi_id":
                matches = search_by_upi(value, all_records, max_matches)
            elif etype in ("bank_name", "bank_account", "ifsc_code"):
                matches = search_by_bank(value, all_records, max_matches)
            else:
                continue

            for m in matches:
                kid = m.indicator_id
                if kid not in seen_km:
                    seen_km.add(kid)
                    knowledge_matches.append(m.to_dict())

            advisories_result = match_advisories(value, advisories, indicator_type=etype, indicator_value=value, max_matches=max_matches)
            for a in advisories_result:
                aid = a.advisory_id
                if aid not in seen_am:
                    seen_am.add(aid)
                    advisory_matches.append(a.to_dict())

    if repeated_indicators:
        for ind in list(repeated_indicators.keys())[:10]:
            keyword_matches = search_by_keywords([ind], all_records, max_matches)
            for m in keyword_matches:
                kid = m.indicator_id
                if kid not in seen_km:
                    seen_km.add(kid)
                    knowledge_matches.append(m.to_dict())
            advisories_result = match_advisories(ind, advisories, indicator_type="keyword", indicator_value=ind, max_matches=max_matches)
            for a in advisories_result:
                aid = a.advisory_id
                if aid not in seen_am:
                    seen_am.add(aid)
                    advisory_matches.append(a.to_dict())

    historical = correlate_historical(merged_entities, repeated_indicators, dominant_family, history, max_matches)

    knowledge_matches.sort(key=lambda x: -x["confidence"])
    advisory_matches.sort(key=lambda x: -x["relevance"])

    return {
        "knowledge_matches": knowledge_matches[:max_matches],
        "advisory_references": advisory_matches[:max_matches],
        "historical_matches": [h.to_dict() for h in historical[:max_matches]],
        "match_count": len(knowledge_matches),
        "advisory_count": len(advisory_matches),
        "historical_count": len(historical),
    }
