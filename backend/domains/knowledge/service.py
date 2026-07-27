from typing import Dict, List

from intelligence.loader import load_all
from intelligence.schemas import ThreatRecord, AdvisoryRecord, HistoricalInvestigation
from domains.shared.models import KnowledgeMatch, AdvisoryMatch, HistoricalMatch
from config.settings import KNOWLEDGE_MAX_MATCHES
from .matcher import _is_match
from .search import (
    search_by_url as _search_by_url,
    search_by_domain as _search_by_domain,
    search_by_phone as _search_by_phone,
    search_by_email as _search_by_email,
    search_by_upi as _search_by_upi,
    search_by_bank as _search_by_bank,
    search_by_qr as _search_by_qr,
    search_by_keywords as _search_by_keywords,
    search_by_family as _search_by_family,
)
from .advisory import match_advisories as _match_advisories, correlate_historical as _correlate_historical
from .enrichment import enrich_entities as _enrich_entities, enrich_investigation as _enrich_investigation


class KnowledgeService:

    def __init__(self) -> None:
        self._patterns: List[ThreatRecord] = []
        self._advisories: Dict[str, List[AdvisoryRecord]] = {}
        self._watchlists: List[ThreatRecord] = []
        self._examples: List[ThreatRecord] = []
        self._history: List[HistoricalInvestigation] = []
        self._loaded = False

    def load(self) -> None:
        patterns, advisories, watchlists, examples, history = load_all()
        self._patterns = patterns
        self._advisories = advisories
        self._watchlists = watchlists
        self._examples = examples
        self._history = history
        self._loaded = True

    def _ensure_loaded(self) -> None:
        if not self._loaded:
            self.load()

    def _get_records_data(self) -> Dict:
        return {
            "patterns": self._patterns,
            "advisories": self._advisories,
            "watchlists": self._watchlists,
            "examples": self._examples,
            "history": self._history,
        }

    def search_by_url(self, url: str) -> List[KnowledgeMatch]:
        self._ensure_loaded()
        all_records = self._patterns + self._watchlists + self._examples
        return _search_by_url(url, all_records, KNOWLEDGE_MAX_MATCHES)

    def search_by_domain(self, domain: str) -> List[KnowledgeMatch]:
        self._ensure_loaded()
        all_records = self._patterns + self._watchlists + self._examples
        return _search_by_domain(domain, all_records, KNOWLEDGE_MAX_MATCHES)

    def search_by_phone(self, phone: str) -> List[KnowledgeMatch]:
        self._ensure_loaded()
        all_records = self._patterns + self._watchlists + self._examples
        return _search_by_phone(phone, all_records, KNOWLEDGE_MAX_MATCHES)

    def search_by_email(self, email: str) -> List[KnowledgeMatch]:
        self._ensure_loaded()
        all_records = self._patterns + self._watchlists + self._examples
        return _search_by_email(email, all_records, KNOWLEDGE_MAX_MATCHES)

    def search_by_upi(self, upi: str) -> List[KnowledgeMatch]:
        self._ensure_loaded()
        all_records = self._patterns + self._watchlists + self._examples
        return _search_by_upi(upi, all_records, KNOWLEDGE_MAX_MATCHES)

    def search_by_bank(self, bank: str) -> List[KnowledgeMatch]:
        self._ensure_loaded()
        all_records = self._patterns + self._watchlists + self._examples
        return _search_by_bank(bank, all_records, KNOWLEDGE_MAX_MATCHES)

    def search_by_qr(self, qr: str) -> List[KnowledgeMatch]:
        self._ensure_loaded()
        all_records = self._patterns + self._watchlists + self._examples
        return _search_by_qr(qr, all_records, KNOWLEDGE_MAX_MATCHES)

    def search_by_keywords(self, keywords: List[str]) -> List[KnowledgeMatch]:
        self._ensure_loaded()
        all_records = self._patterns + self._watchlists + self._examples
        return _search_by_keywords(keywords, all_records, KNOWLEDGE_MAX_MATCHES)

    def search_by_family(self, family: str) -> List[KnowledgeMatch]:
        self._ensure_loaded()
        all_records = self._patterns + self._watchlists + self._examples
        return _search_by_family(family, all_records, KNOWLEDGE_MAX_MATCHES)

    def match_advisories(
        self,
        query: str,
        indicator_type: str = "",
        indicator_value: str = "",
    ) -> List[AdvisoryMatch]:
        self._ensure_loaded()
        return _match_advisories(query, self._advisories, indicator_type, indicator_value, KNOWLEDGE_MAX_MATCHES)

    def correlate_historical(
        self,
        entities: Dict[str, List[Dict]],
        indicators: Dict[str, int],
        dominant_family: str = "",
    ) -> List[HistoricalMatch]:
        self._ensure_loaded()
        return _correlate_historical(entities, indicators, dominant_family, self._history, KNOWLEDGE_MAX_MATCHES)

    def enrich_entities(
        self,
        entities: List[Dict],
        detected_indicators: List[str],
    ) -> Dict:
        self._ensure_loaded()
        return _enrich_entities(entities, detected_indicators, self._get_records_data(), KNOWLEDGE_MAX_MATCHES)

    def enrich_investigation(
        self,
        merged_entities: Dict[str, List[Dict]],
        repeated_indicators: Dict[str, int],
        dominant_family: str,
    ) -> Dict:
        self._ensure_loaded()
        return _enrich_investigation(merged_entities, repeated_indicators, dominant_family, self._get_records_data(), KNOWLEDGE_MAX_MATCHES)


_service_instance = None


def get_service() -> "KnowledgeService":
    global _service_instance
    if _service_instance is None:
        _service_instance = KnowledgeService()
        _service_instance.load()
    return _service_instance
