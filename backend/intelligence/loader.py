import json
import os
from typing import Dict, List, Optional, Tuple

from intelligence.schemas import (
    THREAT_TYPES,
    AdvisoryRecord,
    HistoricalInvestigation,
    ThreatRecord,
    ThreatReference,
    validate_schema,
)

_BASE_DIR = os.path.dirname(os.path.abspath(__file__))


def _load_json(filename: str, subdir: str = "") -> List[Dict]:
    path = os.path.join(_BASE_DIR, subdir, filename) if subdir else os.path.join(_BASE_DIR, filename)
    if not os.path.isfile(path):
        return []
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    return data if isinstance(data, list) else []


def _threat_record_from_dict(item: Dict) -> ThreatRecord:
    kwargs = {k: v for k, v in item.items() if k in ThreatRecord.__dataclass_fields__ and k != "references"}
    refs = []
    for r in item.get("references", []):
        if isinstance(r, dict):
            refs.append(ThreatReference(**{k: v for k, v in r.items() if k in ThreatReference.__dataclass_fields__}))
    kwargs["references"] = refs
    return ThreatRecord(**kwargs)


def load_patterns() -> List[ThreatRecord]:
    records = []
    for item in _load_json("known_patterns.json", "patterns"):
        errs = validate_schema(item)
        if not errs:
            records.append(_threat_record_from_dict(item))
    return records


def _load_advisories_from(data: List[Dict]) -> List[AdvisoryRecord]:
    records = []
    for item in data:
        records.append(AdvisoryRecord(**{k: v for k, v in item.items() if k in AdvisoryRecord.__dataclass_fields__}))
    return records


def load_advisories() -> Dict[str, List[AdvisoryRecord]]:
    advisories: Dict[str, List[AdvisoryRecord]] = {}
    sources = {"cert_in.json": "cert-in", "rbi.json": "rbi", "npci.json": "npci", "banks.json": "bank", "internal.json": "internal"}
    for filename, source in sources.items():
        records = _load_advisories_from(_load_json(filename, "advisories"))
        if records:
            advisories[source] = records
    return advisories


def load_watchlist(atype: str) -> List[ThreatRecord]:
    filename_map = {
        "phone": "phone_watchlist.json",
        "domain": "domain_watchlist.json",
        "upi": "upi_watchlist.json",
        "email": "email_watchlist.json",
    }
    filename = filename_map.get(atype, "")
    if not filename:
        return []
    records = []
    for item in _load_json(filename, "watchlists"):
        errs = validate_schema(item)
        if not errs:
            records.append(_threat_record_from_dict(item))
    return records


def load_examples() -> List[ThreatRecord]:
    records = []
    for item in _load_json("known_scam_examples.json", "examples"):
        errs = validate_schema(item)
        if not errs:
            records.append(_threat_record_from_dict(item))
    return records


def load_history() -> List[HistoricalInvestigation]:
    records = []
    for item in _load_json("investigations.json", "history"):
        records.append(HistoricalInvestigation(**{
            k: v for k, v in item.items()
            if k in HistoricalInvestigation.__dataclass_fields__
        }))
    return records


def load_all() -> Tuple[
    List[ThreatRecord],
    Dict[str, List[AdvisoryRecord]],
    List[ThreatRecord],
    List[ThreatRecord],
    List[HistoricalInvestigation],
]:
    patterns = load_patterns()
    advisories = load_advisories()
    phone_wl = load_watchlist("phone")
    domain_wl = load_watchlist("domain")
    upi_wl = load_watchlist("upi")
    email_wl = load_watchlist("email")
    watchlists = phone_wl + domain_wl + upi_wl + email_wl
    examples = load_examples()
    history = load_history()
    return patterns, advisories, watchlists, examples, history
