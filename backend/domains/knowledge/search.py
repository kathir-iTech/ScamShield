from typing import Callable, Dict, List, Optional, Tuple

from intelligence.schemas import ThreatRecord
from domains.shared.models import KnowledgeMatch
from domains.shared.utils import normalise, digits_only, levenshtein, domain_from_url
from config.settings import (
    KNOWLEDGE_LEVENSHTEIN_THRESHOLD,
    KNOWLEDGE_MAX_MATCHES,
)
from .matcher import _is_match


def _search_records(
    query: str,
    records: List[ThreatRecord],
    match_fn: Optional[Callable[[str, str], Tuple[str, float]]] = None,
    max_matches: int = KNOWLEDGE_MAX_MATCHES,
) -> List[KnowledgeMatch]:
    results: List[KnowledgeMatch] = []
    seen_ids: set = set()
    q_norm = normalise(query)

    for rec in records:
        if rec.indicator_id in seen_ids:
            continue
        matched_value = rec.value
        match_type: str = ""
        match_conf: float = 0.0

        if match_fn:
            match_type, match_conf = match_fn(q_norm, normalise(rec.value))
            if match_type == "none" and rec.aliases:
                for alias in rec.aliases:
                    mt, mc = match_fn(q_norm, normalise(alias))
                    if mt != "none" and mc > match_conf:
                        match_type = mt
                        match_conf = mc
                        matched_value = alias
            if match_type == "none":
                continue
        else:
            if q_norm == normalise(rec.value):
                match_type = "exact"
                match_conf = 1.0
            else:
                for alias in rec.aliases:
                    if q_norm == normalise(alias):
                        match_type = "exact"
                        match_conf = 1.0
                        matched_value = alias
                        break
            if not match_type:
                continue

        seen_ids.add(rec.indicator_id)
        results.append(KnowledgeMatch(
            indicator_id=rec.indicator_id,
            type=rec.type,
            value=rec.value,
            matched_value=matched_value,
            match_type=match_type,
            confidence=round(match_conf * rec.confidence, 3),
            family=rec.family,
            subfamily=rec.subfamily,
            risk=rec.risk,
            source=rec.source,
            description=rec.description,
            related_indicators=rec.related_indicators,
            references=[{"title": r.title, "url": r.url, "source": r.source, "date": r.date} for r in rec.references],
        ))

    results.sort(key=lambda x: -x.confidence)
    return results[:max_matches]


def search_by_url(
    url: str,
    all_records: List[ThreatRecord],
    max_matches: int = KNOWLEDGE_MAX_MATCHES,
) -> List[KnowledgeMatch]:
    domain = domain_from_url(url)
    url_records = [r for r in all_records if r.type in ("url", "domain")]
    results = []

    for rec in url_records:
        match_type, match_conf = ("none", 0.0)
        matched_value = rec.value
        rec_domain = normalise(rec.value)

        if normalise(url) == rec_domain:
            match_type, match_conf = "exact", 1.0
        elif domain and normalise(domain) == rec_domain:
            match_type, match_conf = "domain_match", 0.90
        elif domain and rec_domain and domain.endswith("." + rec_domain):
            match_type, match_conf = "subdomain_match", 0.80
        elif rec_domain and domain and rec_domain.endswith("." + domain):
            match_type, match_conf = "parent_domain_match", 0.70
        else:
            mt, mc = _is_match(normalise(url), rec_domain, threshold=KNOWLEDGE_LEVENSHTEIN_THRESHOLD)
            if mt != "none":
                match_type, match_conf = mt, mc

        if match_type != "none":
            results.append(KnowledgeMatch(
                indicator_id=rec.indicator_id,
                type=rec.type,
                value=rec.value,
                matched_value=matched_value,
                match_type=match_type,
                confidence=round(match_conf * rec.confidence, 3),
                family=rec.family,
                subfamily=rec.subfamily,
                risk=rec.risk,
                source=rec.source,
                description=rec.description,
                related_indicators=rec.related_indicators,
                references=[{"title": r.title, "url": r.url, "source": r.source, "date": r.date} for r in rec.references],
            ))

    results.sort(key=lambda x: -x.confidence)
    return results[:max_matches]


def search_by_domain(
    domain: str,
    all_records: List[ThreatRecord],
    max_matches: int = KNOWLEDGE_MAX_MATCHES,
) -> List[KnowledgeMatch]:
    domain_records = [r for r in all_records if r.type in ("url", "domain")]
    return _search_records(domain, domain_records, max_matches=max_matches)


def search_by_phone(
    phone: str,
    all_records: List[ThreatRecord],
    max_matches: int = KNOWLEDGE_MAX_MATCHES,
) -> List[KnowledgeMatch]:
    phone_digits = digits_only(phone)
    phone_records = [r for r in all_records if r.type == "phone"]

    def match_phone(q: str, r: str) -> Tuple[str, float]:
        r_digits = digits_only(r)
        if not r_digits:
            return ("none", 0.0)
        if phone_digits == r_digits:
            return ("exact", 1.0)
        if len(phone_digits) >= 10 and len(r_digits) >= 10:
            if phone_digits[-10:] == r_digits[-10:]:
                return ("exact", 1.0)
        if len(phone_digits) >= 7 and len(r_digits) >= 7:
            if phone_digits[-7:] == r_digits[-7:]:
                return ("suffix", 0.80)
        return ("none", 0.0)

    return _search_records(phone, phone_records, match_fn=match_phone, max_matches=max_matches)


def search_by_email(
    email: str,
    all_records: List[ThreatRecord],
    max_matches: int = KNOWLEDGE_MAX_MATCHES,
) -> List[KnowledgeMatch]:
    email_records = [r for r in all_records if r.type == "email"]
    return _search_records(email, email_records, max_matches=max_matches)


def search_by_upi(
    upi: str,
    all_records: List[ThreatRecord],
    max_matches: int = KNOWLEDGE_MAX_MATCHES,
) -> List[KnowledgeMatch]:
    upi_records = [r for r in all_records if r.type == "upi"]

    def match_upi(q: str, r: str) -> Tuple[str, float]:
        qn = normalise(q)
        rn = normalise(r)
        if qn == rn:
            return ("exact", 1.0)
        q_parts = qn.split("@")
        r_parts = rn.split("@")
        if len(q_parts) == 2 and len(r_parts) == 2:
            if rn.endswith("@" + q_parts[1]):
                return ("suffix", 0.75)
            if qn.endswith("@" + r_parts[1]):
                return ("prefix", 0.75)
        dist = levenshtein(qn, rn)
        max_len = max(len(qn), len(rn))
        if max_len > 0 and dist <= max(KNOWLEDGE_LEVENSHTEIN_THRESHOLD, int(max_len * 0.2)):
            sim = 1.0 - (dist / max_len)
            return ("levenshtein", max(0.5, sim))
        return ("none", 0.0)

    return _search_records(upi, upi_records, match_fn=match_upi, max_matches=max_matches)


def search_by_bank(
    bank: str,
    all_records: List[ThreatRecord],
    max_matches: int = KNOWLEDGE_MAX_MATCHES,
) -> List[KnowledgeMatch]:
    bank_records = [r for r in all_records if r.type in ("bank", "bank_account", "ifsc")]
    return _search_records(bank, bank_records, max_matches=max_matches)


def search_by_qr(
    qr: str,
    all_records: List[ThreatRecord],
    max_matches: int = KNOWLEDGE_MAX_MATCHES,
) -> List[KnowledgeMatch]:
    qr_records = [r for r in all_records if r.type == "qr"]
    return _search_records(qr, qr_records, max_matches=max_matches)


def search_by_keywords(
    keywords: List[str],
    all_records: List[ThreatRecord],
    max_matches: int = KNOWLEDGE_MAX_MATCHES,
) -> List[KnowledgeMatch]:
    keyword_records = [r for r in all_records if r.type == "keyword"]
    seen_ids: set = set()
    results: List[KnowledgeMatch] = []

    for kw in keywords:
        kw_norm = normalise(kw)
        for rec in keyword_records:
            if rec.indicator_id in seen_ids:
                continue
            mt, mc = _is_match(kw_norm, normalise(rec.value), threshold=2)
            if mt == "none" and rec.aliases:
                for alias in rec.aliases:
                    mt2, mc2 = _is_match(kw_norm, normalise(alias), threshold=2)
                    if mt2 != "none" and mc2 > mc:
                        mt, mc = mt2, mc2
            if mt != "none":
                seen_ids.add(rec.indicator_id)
                results.append(KnowledgeMatch(
                    indicator_id=rec.indicator_id,
                    type=rec.type,
                    value=rec.value,
                    matched_value=rec.value,
                    match_type=mt,
                    confidence=round(mc * rec.confidence, 3),
                    family=rec.family,
                    subfamily=rec.subfamily,
                    risk=rec.risk,
                    source=rec.source,
                    description=rec.description,
                    related_indicators=rec.related_indicators,
                    references=[{"title": r.title, "url": r.url, "source": r.source, "date": r.date} for r in rec.references],
                ))

    results.sort(key=lambda x: -x.confidence)
    return results[:max_matches]


def search_by_family(
    family: str,
    all_records: List[ThreatRecord],
    max_matches: int = KNOWLEDGE_MAX_MATCHES,
) -> List[KnowledgeMatch]:
    results = []
    for rec in all_records:
        if normalise(rec.family) == normalise(family) or normalise(rec.subfamily) == normalise(family):
            results.append(KnowledgeMatch(
                indicator_id=rec.indicator_id,
                type=rec.type,
                value=rec.value,
                matched_value=rec.value,
                match_type="family_match",
                confidence=rec.confidence,
                family=rec.family,
                subfamily=rec.subfamily,
                risk=rec.risk,
                source=rec.source,
                description=rec.description,
                related_indicators=rec.related_indicators,
                references=[{"title": r.title, "url": r.url, "source": r.source, "date": r.date} for r in rec.references],
            ))
    results.sort(key=lambda x: -x.confidence)
    return results[:max_matches]
