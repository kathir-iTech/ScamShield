from typing import Any, Dict, List

from .models import InvestigationArtefact, MergedEntity, _ARTEFACT_TYPES


def _validate_artefacts(artefacts: List[Dict]) -> List[Dict]:
    validated = []
    for i, artefact in enumerate(artefacts):
        text = artefact.get("text", "").strip()
        atype = artefact.get("type", "text").lower()
        if atype not in _ARTEFACT_TYPES:
            atype = "text"
        if not text:
            continue
        validated.append({"index": i, "text": text, "type": atype})
    return validated


def _normalise_url(url: str) -> str:
    return url.lower().rstrip("/")


def _normalise_phone(phone: str) -> str:
    digits = "".join(c for c in phone if c.isdigit())
    return digits[-10:] if len(digits) >= 10 else digits


def _normalise_email(email: str) -> str:
    return email.lower().strip()


def _normalise_upi(upi: str) -> str:
    return upi.lower().strip()


def _merge_entities(artefacts: List[InvestigationArtefact]) -> Dict[str, List[Dict]]:
    merged: Dict[str, Dict[str, MergedEntity]] = {}

    for art in artefacts:
        entities = art.analysis.get("entities", [])
        for ent in entities:
            etype = ent.get("type", "unknown")
            raw_value = ent.get("value", "")
            risk = ent.get("risk", "LOW")
            if not raw_value:
                continue

            if etype in ("url", "domain"):
                key_val = _normalise_url(raw_value)
            elif etype in ("phone_indian", "phone_international", "phone"):
                key_val = _normalise_phone(raw_value)
                etype = "phone"
            elif etype == "email":
                key_val = _normalise_email(raw_value)
            elif etype == "upi_id":
                key_val = _normalise_upi(raw_value)
            else:
                key_val = raw_value.lower().strip()

            if etype not in merged:
                merged[etype] = {}
            if key_val not in merged[etype]:
                merged[etype][key_val] = MergedEntity(
                    value=raw_value,
                    entity_type=etype,
                    occurrences=0,
                    first_seen=art.index,
                    sources=[],
                    max_risk="LOW",
                )
            me = merged[etype][key_val]
            me.occurrences += 1
            if art.index not in me.sources:
                me.sources.append(art.index)
            risk_order = {"HIGH": 3, "MEDIUM": 2, "LOW": 1}
            if risk_order.get(risk, 0) > risk_order.get(me.max_risk, 0):
                me.max_risk = risk

    result: Dict[str, List[Dict]] = {}
    for etype, entities in merged.items():
        result[etype] = []
        for key_val, me in entities.items():
            result[etype].append({
                "value": me.value,
                "normalised": key_val,
                "occurrences": me.occurrences,
                "first_seen_artefact": me.first_seen,
                "sources": me.sources,
                "max_risk": me.max_risk,
            })
        result[etype].sort(key=lambda x: -x["occurrences"])
    return result


def _detect_repeated_indicators(artefacts: List[InvestigationArtefact]) -> Dict[str, int]:
    indicator_counts: Dict[str, int] = {}
    for art in artefacts:
        for ind in art.analysis.get("detected_indicators", []):
            indicator_counts[ind] = indicator_counts.get(ind, 0) + 1
    return {k: v for k, v in sorted(indicator_counts.items(), key=lambda x: -x[1]) if v > 1}
