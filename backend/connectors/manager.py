import concurrent.futures
import time
import threading
from typing import Dict, List, Optional

from config.settings import (
    CONNECTOR_ENABLED,
    CONNECTOR_TIMEOUT,
    CONNECTOR_RETRY_COUNT,
    CONNECTOR_PARALLELISM,
    CONNECTOR_MAX_RESULTS,
)
from connectors.base import BaseConnector
from connectors.cache import ConnectorCache
from connectors.exceptions import ConnectorTimeoutError, ConnectorUnavailableError
from connectors.models import LookupResult
from connectors.registry import ConnectorRegistry
from connectors.utils import (
    calculate_aggregate_confidence,
    merge_evidence,
    normalize_indicator,
)


class ConnectorManager:
    def __init__(self) -> None:
        self._cache = ConnectorCache()
        self._lock = threading.Lock()
        self._loaded = False

    def load_connectors(self) -> int:
        with self._lock:
            if self._loaded:
                return len(ConnectorRegistry.get_all())
            discovered = ConnectorRegistry.discover()
            self._loaded = True
            return len(discovered)

    @property
    def cache(self) -> ConnectorCache:
        return self._cache

    def _check_health(self, connector: BaseConnector) -> bool:
        try:
            health = connector.health()
            return health.get("status") in ("healthy", "ok", "available")
        except Exception:
            return False

    def _execute_with_retry(
        self, connector: BaseConnector, indicator: str, indicator_type: str
    ) -> LookupResult:
        last_error: Optional[str] = None
        for attempt in range(max(1, CONNECTOR_RETRY_COUNT + 1)):
            try:
                start = time.perf_counter()
                result = connector.lookup(indicator, indicator_type)
                elapsed = (time.perf_counter() - start) * 1000
                result.latency = elapsed
                return result
            except Exception as exc:
                last_error = str(exc)
                if attempt < CONNECTOR_RETRY_COUNT:
                    continue
        return LookupResult(
            indicator=indicator,
            indicator_type=indicator_type,
            matched=False,
            risk="UNKNOWN",
            confidence=0.0,
            source=connector.name,
            error=f"All {CONNECTOR_RETRY_COUNT + 1} attempts failed: {last_error}",
        )

    def _lookup_single(
        self, connector: BaseConnector, indicator: str, indicator_type: str
    ) -> LookupResult:
        if not self._check_health(connector):
            return LookupResult(
                indicator=indicator,
                indicator_type=indicator_type,
                matched=False,
                risk="UNKNOWN",
                confidence=0.0,
                source=connector.name,
                error="Connector unhealthy",
            )
        cached = self._cache.get(connector.name, indicator, indicator_type)
        if cached is not None:
            return cached
        result = self._execute_with_retry(connector, indicator, indicator_type)
        self._cache.set(connector.name, indicator, indicator_type, result)
        return result

    def lookup(
        self,
        indicator: str,
        indicator_type: str,
    ) -> List[LookupResult]:
        if not CONNECTOR_ENABLED:
            return []
        norm = normalize_indicator(indicator, indicator_type)
        if not norm:
            return []
        connectors = ConnectorRegistry.get_by_indicator(indicator_type)
        if not connectors:
            return []
        lookup_limit = min(len(connectors), CONNECTOR_PARALLELISM)
        active = connectors[:lookup_limit]
        results: List[LookupResult] = []
        with concurrent.futures.ThreadPoolExecutor(max_workers=lookup_limit) as executor:
            future_map = {
                executor.submit(
                    self._lookup_single, conn, indicator, indicator_type
                ): conn
                for conn in active
            }
            for future in concurrent.futures.as_completed(future_map, timeout=CONNECTOR_TIMEOUT + 5):
                conn = future_map[future]
                try:
                    result = future.result(timeout=CONNECTOR_TIMEOUT)
                    results.append(result)
                except concurrent.futures.TimeoutError:
                    results.append(LookupResult(
                        indicator=indicator,
                        indicator_type=indicator_type,
                        matched=False,
                        risk="UNKNOWN",
                        confidence=0.0,
                        source=conn.name,
                        error=f"Timeout after {CONNECTOR_TIMEOUT}s",
                    ))
                except Exception as exc:
                    results.append(LookupResult(
                        indicator=indicator,
                        indicator_type=indicator_type,
                        matched=False,
                        risk="UNKNOWN",
                        confidence=0.0,
                        source=conn.name,
                        error=str(exc),
                    ))
        return self._merge_results(results, indicator, indicator_type)

    def _merge_results(
        self,
        results: List[LookupResult],
        indicator: str,
        indicator_type: str,
    ) -> List[LookupResult]:
        matched = [r for r in results if r.matched and not r.error]
        unmatched = [r for r in results if not r.matched or r.error]
        if not matched:
            if unmatched:
                best_unmatched = min(unmatched, key=lambda r: (bool(r.error), r.latency))
                return [best_unmatched]
            return []
        seen_sources: set = set()
        deduped: List[LookupResult] = []
        for r in matched:
            if r.source not in seen_sources:
                seen_sources.add(r.source)
                deduped.append(r)
        deduped.sort(key=lambda r: (-r.confidence, r.latency))
        for r in unmatched:
            if r.source not in seen_sources:
                seen_sources.add(r.source)
                deduped.append(r)
        return deduped[:CONNECTOR_MAX_RESULTS]

    def lookup_all(
        self,
        indicators: Dict[str, List[str]],
    ) -> Dict[str, List[LookupResult]]:
        if not CONNECTOR_ENABLED:
            return {}
        results: Dict[str, List[LookupResult]] = {}
        for indicator_type, values in indicators.items():
            for val in values:
                key = f"{indicator_type}:{normalize_indicator(val, indicator_type)}"
                if key not in results:
                    results[key] = self.lookup(val, indicator_type)
        return results

    def health_summary(self) -> Dict[str, Dict]:
        summary: Dict[str, Dict] = {}
        for name, connector in ConnectorRegistry.get_all().items():
            try:
                h = connector.health()
                summary[name] = h
            except Exception as exc:
                summary[name] = {"status": "error", "error": str(exc)}
        return summary


_manager: Optional[ConnectorManager] = None


def get_manager() -> ConnectorManager:
    global _manager
    if _manager is None:
        _manager = ConnectorManager()
        _manager.load_connectors()
    return _manager


def enrich_with_connectors(analysis: Dict) -> List[Dict]:
    manager = get_manager()
    entities = analysis.get("entities", [])
    detected_indicators = analysis.get("detected_indicators", [])
    indicators_map: Dict[str, List[str]] = {}
    for ent in entities:
        etype = ent.get("type", "")
        value = ent.get("value", "")
        if not value:
            continue
        mapped = _map_entity_type(etype)
        if mapped:
            indicators_map.setdefault(mapped, []).append(value)
    for ind in detected_indicators:
        if isinstance(ind, str) and ind.strip():
            indicators_map.setdefault("keyword", []).append(ind)
    all_results = manager.lookup_all(indicators_map)
    flat: List[Dict] = []
    seen_sources: set = set()
    for key, results in all_results.items():
        for r in results:
            if r.source not in seen_sources:
                seen_sources.add(r.source)
                flat.append(r.to_dict())
    return flat


def _map_entity_type(entity_type: str) -> str:
    mapping = {
        "url": "url",
        "domain": "domain",
        "phone": "phone",
        "phone_indian": "phone",
        "phone_international": "phone",
        "email": "email",
        "upi_id": "upi",
        "bank_name": "bank",
        "bank_account": "bank",
        "ifsc_code": "bank",
        "qr": "qr",
    }
    return mapping.get(entity_type, entity_type)
