from typing import Dict, List

from domains.shared.models import KnowledgeMatch

_service_instance = None


def _get_service():
    global _service_instance
    if _service_instance is None:
        from .service import KnowledgeService
        _service_instance = KnowledgeService()
        _service_instance.load()
    return _service_instance


def enrich_analysis(analysis: Dict) -> Dict:
    service = _get_service()
    entities = analysis.get("entities", [])
    indicators = analysis.get("detected_indicators", [])
    return service.enrich_entities(entities, indicators)


def enrich_investigation_result(
    merged_entities: Dict[str, List[Dict]],
    repeated_indicators: Dict[str, int],
    dominant_family: str,
) -> Dict:
    service = _get_service()
    return service.enrich_investigation(merged_entities, repeated_indicators, dominant_family)


def search_by_indicator(indicator_type: str, value: str) -> List[KnowledgeMatch]:
    service = _get_service()
    search_map = {
        "url": service.search_by_url,
        "domain": service.search_by_domain,
        "phone": service.search_by_phone,
        "email": service.search_by_email,
        "upi": service.search_by_upi,
        "upi_id": service.search_by_upi,
        "bank": service.search_by_bank,
        "bank_name": service.search_by_bank,
        "bank_account": service.search_by_bank,
        "ifsc": service.search_by_bank,
        "ifsc_code": service.search_by_bank,
        "qr": service.search_by_qr,
    }
    if indicator_type == "keyword":
        return service.search_by_keywords([value])
    searcher = search_map.get(indicator_type)
    if searcher:
        return searcher(value)
    return []
