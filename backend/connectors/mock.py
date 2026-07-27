import time
from typing import Dict, List

from connectors.base import BaseConnector
from connectors.models import LookupResult
from connectors.utils import normalize_indicator


class MockThreatConnector(BaseConnector):

    @property
    def name(self) -> str:
        return "mock_threat"

    @property
    def version(self) -> str:
        return "1.0.0"

    @property
    def priority(self) -> int:
        return 0

    def supported_indicators(self) -> List[str]:
        return ["url", "domain", "phone", "email", "upi", "keyword"]

    def health(self) -> Dict:
        return {
            "status": "ok",
            "connector": self.name,
            "version": self.version,
            "latency_ms": 0.5,
        }

    def _load_data(self) -> Dict[str, List[Dict]]:
        data: Dict[str, List[Dict]] = {
            "url": [],
            "domain": [],
            "phone": [],
            "email": [],
            "upi": [],
            "keyword": [],
        }
        try:
            from intelligence.loader import load_all
            patterns, _advisories, watchlists, examples, _history = load_all()
            for rec in patterns + watchlists + examples:
                t = rec.type
                if t in data:
                    data[t].append({
                        "indicator_id": rec.indicator_id,
                        "value": rec.value,
                        "family": rec.family,
                        "risk": rec.risk,
                        "confidence": rec.confidence,
                        "description": rec.description,
                    })
        except Exception:
            pass
        return data

    def lookup(self, indicator: str, indicator_type: str) -> LookupResult:
        start = time.perf_counter()
        norm = normalize_indicator(indicator, indicator_type)
        if not norm:
            elapsed = (time.perf_counter() - start) * 1000
            return LookupResult(
                indicator=indicator,
                indicator_type=indicator_type,
                matched=False,
                risk="UNKNOWN",
                confidence=0.0,
                source=self.name,
                latency=elapsed,
            )
        data = self._load_data()
        records = data.get(indicator_type, [])
        if indicator_type == "keyword":
            candidates = data.get("keyword", [])
        else:
            candidates = records
        best_match = None
        best_score = 0.0
        for rec in candidates:
            rec_norm = normalize_indicator(rec["value"], indicator_type)
            score = self._match_score(norm, rec_norm, indicator_type)
            if score > best_score:
                best_score = score
                best_match = rec
        elapsed = (time.perf_counter() - start) * 1000
        if best_match and best_score > 0.5:
            return LookupResult(
                indicator=indicator,
                indicator_type=indicator_type,
                matched=True,
                risk=best_match["risk"],
                confidence=round(best_score * best_match["confidence"], 3),
                source=self.name,
                summary=best_match.get("description", f"Known {indicator_type} indicator"),
                evidence=[{
                    "indicator_id": best_match["indicator_id"],
                    "value": best_match["value"],
                    "match_score": best_score,
                    "family": best_match.get("family", ""),
                }],
                latency=elapsed,
            )
        return LookupResult(
            indicator=indicator,
            indicator_type=indicator_type,
            matched=False,
            risk="UNKNOWN",
            confidence=0.0,
            source=self.name,
            latency=elapsed,
        )

    def _match_score(self, query: str, record: str, indicator_type: str) -> float:
        if query == record:
            return 1.0
        if indicator_type == "phone":
            if len(query) >= 10 and len(record) >= 10 and query[-10:] == record[-10:]:
                return 0.95
            if len(query) >= 7 and len(record) >= 7 and query[-7:] == record[-7:]:
                return 0.75
        if indicator_type in ("url", "domain"):
            if record and query.endswith("." + record):
                return 0.85
            if query and record.endswith("." + query):
                return 0.70
        q_words = set(query.split())
        r_words = set(record.split())
        if q_words and r_words:
            overlap = q_words & r_words
            if overlap:
                ratio = len(overlap) / max(len(q_words), len(r_words))
                if ratio >= 0.5:
                    return 0.60 * ratio
        if record and len(query) >= 4 and record.startswith(query):
            return 0.80
        if record and len(query) >= 4 and record.endswith(query):
            return 0.70
        if record and record in query:
            return 0.65
        return 0.0
