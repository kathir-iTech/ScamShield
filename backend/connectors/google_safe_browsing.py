import json
import time
import urllib.error
import urllib.request
from typing import Dict, List, Optional

from config.settings import (
    SAFE_BROWSING_ENABLED,
    SAFE_BROWSING_API_KEY,
    SAFE_BROWSING_TIMEOUT,
    SAFE_BROWSING_CACHE_TTL,
    SAFE_BROWSING_MAX_BATCH,
)
from connectors.base import BaseConnector
from connectors.models import LookupResult

_API_BASE: str = "https://safebrowsing.googleapis.com/v4/threatMatches:find"

_THREAT_TYPES: List[str] = [
    "MALWARE",
    "SOCIAL_ENGINEERING",
    "UNWANTED_SOFTWARE",
    "POTENTIALLY_HARMFUL_APPLICATION",
    "THREAT_TYPE_UNSPECIFIED",
]

_RISK_MAP: Dict[str, str] = {
    "MALWARE": "HIGH",
    "SOCIAL_ENGINEERING": "HIGH",
    "UNWANTED_SOFTWARE": "MEDIUM",
    "POTENTIALLY_HARMFUL_APPLICATION": "MEDIUM",
    "THREAT_TYPE_UNSPECIFIED": "UNKNOWN",
}

_CONFIDENCE_MAP: Dict[str, float] = {
    "MALWARE": 0.90,
    "SOCIAL_ENGINEERING": 0.85,
    "UNWANTED_SOFTWARE": 0.70,
    "POTENTIALLY_HARMFUL_APPLICATION": 0.65,
    "THREAT_TYPE_UNSPECIFIED": 0.30,
}


def _normalise_url(url: str) -> str:
    url = url.strip().lower()
    if not url.startswith("http://") and not url.startswith("https://"):
        url = "http://" + url
    return url


def _domain_from_url(url: str) -> str:
    url = _normalise_url(url)
    url = url.replace("http://", "").replace("https://", "")
    url = url.split("/")[0]
    url = url.split("?")[0]
    return url


def _build_request_body(urls: List[str]) -> bytes:
    entries = [{"url": u} for u in urls]
    body = {
        "client": {
            "clientId": "scamshield",
            "clientVersion": "1.0.0",
        },
        "threatInfo": {
            "threatTypes": _THREAT_TYPES,
            "platformTypes": ["ANY_PLATFORM"],
            "threatEntryTypes": ["URL"],
            "threatEntries": entries,
        },
    }
    return json.dumps(body).encode("utf-8")


class GoogleSafeBrowsingConnector(BaseConnector):

    def __init__(self) -> None:
        self._api_key: str = SAFE_BROWSING_API_KEY
        self._enabled: bool = SAFE_BROWSING_ENABLED and bool(self._api_key)
        self._timeout: int = SAFE_BROWSING_TIMEOUT
        self._cache_ttl: int = SAFE_BROWSING_CACHE_TTL
        self._max_batch: int = SAFE_BROWSING_MAX_BATCH

    @property
    def name(self) -> str:
        return "google_safe_browsing"

    @property
    def version(self) -> str:
        return "1.0.0"

    @property
    def enabled(self) -> bool:
        return self._enabled

    @property
    def priority(self) -> int:
        return 50

    def supported_indicators(self) -> List[str]:
        return ["url", "domain"]

    def health(self) -> Dict:
        if not self._enabled:
            return {
                "status": "disabled",
                "connector": self.name,
                "reason": "No API key configured",
            }
        try:
            resp = _call_api(self._api_key, [_normalise_url("https://example.com")], self._timeout)
            return {
                "status": "ok",
                "connector": self.name,
                "version": self.version,
            }
        except Exception as exc:
            return {
                "status": "unhealthy",
                "connector": self.name,
                "error": str(exc),
            }

    def lookup(self, indicator: str, indicator_type: str) -> LookupResult:
        start = time.perf_counter()
        if not self._enabled:
            elapsed = (time.perf_counter() - start) * 1000
            return LookupResult(
                indicator=indicator,
                indicator_type=indicator_type,
                matched=False,
                risk="UNKNOWN",
                confidence=0.0,
                source=self.name,
                summary="Google Safe Browsing is disabled (no API key)",
                latency=elapsed,
            )
        if indicator_type == "domain":
            indicator = _normalise_url(indicator)
        url = _normalise_url(indicator)
        if not url:
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
        try:
            matches = _call_api(self._api_key, [url], self._timeout)
            elapsed = (time.perf_counter() - start) * 1000
            return _normalise_response(
                indicator=indicator,
                indicator_type=indicator_type,
                url=url,
                matches=matches,
                source=self.name,
                latency=elapsed,
            )
        except Exception as exc:
            elapsed = (time.perf_counter() - start) * 1000
            return LookupResult(
                indicator=indicator,
                indicator_type=indicator_type,
                matched=False,
                risk="UNKNOWN",
                confidence=0.0,
                source=self.name,
                error=str(exc),
                latency=elapsed,
            )

    def lookup_batch(self, indicators: List[str], indicator_type: str) -> List[LookupResult]:
        start = time.perf_counter()
        if not self._enabled or not indicators:
            return []
        results: List[LookupResult] = []
        urls: List[str] = []
        original_map: List[str] = []
        for ind in indicators:
            u = _normalise_url(ind)
            if u:
                urls.append(u)
                original_map.append(ind)
        if not urls:
            return []
        for i in range(0, len(urls), self._max_batch):
            batch = urls[i:i + self._max_batch]
            batch_originals = original_map[i:i + self._max_batch]
            try:
                matches = _call_api(self._api_key, batch, self._timeout)
                batch_end = time.perf_counter()
                batch_latency = (batch_end - start) * 1000
                for idx, url in enumerate(batch):
                    url_matches = [m for m in matches if m.get("threat", {}).get("url", "").strip("/").lower() == url.strip("/").lower()]
                    results.append(_normalise_response(
                        indicator=batch_originals[idx],
                        indicator_type=indicator_type,
                        url=url,
                        matches=url_matches,
                        source=self.name,
                        latency=batch_latency,
                    ))
            except Exception as exc:
                for idx in range(len(batch)):
                    results.append(LookupResult(
                        indicator=batch_originals[idx],
                        indicator_type=indicator_type,
                        matched=False,
                        risk="UNKNOWN",
                        confidence=0.0,
                        source=self.name,
                        error=str(exc),
                    ))
        return results


def _call_api(api_key: str, urls: List[str], timeout: int) -> List[Dict]:
    if not api_key or not urls:
        return []
    body = _build_request_body(urls)
    full_url = f"{_API_BASE}?key={api_key}"
    req = urllib.request.Request(
        full_url,
        data=body,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    max_retries = 2
    last_exc: Optional[Exception] = None
    for attempt in range(max_retries + 1):
        try:
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                raw = resp.read().decode("utf-8")
                if not raw.strip():
                    return []
                data = json.loads(raw)
                return data.get("matches", [])
        except urllib.error.HTTPError as exc:
            if exc.code == 403:
                raise RuntimeError("Google Safe Browsing: Invalid API key (403)") from exc
            if exc.code == 429 and attempt < max_retries:
                wait = 2 ** (attempt + 1)
                time.sleep(wait)
                last_exc = exc
                continue
            raise RuntimeError(f"Google Safe Browsing API error: HTTP {exc.code}") from exc
        except urllib.error.URLError as exc:
            if attempt < max_retries:
                wait = 2 ** (attempt + 1)
                time.sleep(wait)
                last_exc = exc
                continue
            raise RuntimeError(f"Google Safe Browsing: {exc.reason}") from exc
        except json.JSONDecodeError as exc:
            raise RuntimeError(f"Google Safe Browsing: Invalid JSON response") from exc
        except Exception as exc:
            if attempt < max_retries:
                wait = 2 ** (attempt + 1)
                time.sleep(wait)
                last_exc = exc
                continue
            raise
    if last_exc:
        raise RuntimeError(f"Google Safe Browsing: All retries failed") from last_exc
    return []


def _normalise_response(
    indicator: str,
    indicator_type: str,
    url: str,
    matches: List[Dict],
    source: str,
    latency: float,
) -> LookupResult:
    if not matches:
        return LookupResult(
            indicator=indicator,
            indicator_type=indicator_type,
            matched=False,
            risk="UNKNOWN",
            confidence=0.0,
            source=source,
            summary="No threats detected by Google Safe Browsing",
            latency=latency,
        )
    threat_types = [m.get("threatType", "THREAT_TYPE_UNSPECIFIED") for m in matches]
    unique_types = list(dict.fromkeys(threat_types))
    max_risk = "UNKNOWN"
    max_conf = 0.0
    for t in unique_types:
        r = _RISK_MAP.get(t, "UNKNOWN")
        c = _CONFIDENCE_MAP.get(t, 0.0)
        if _risk_rank(r) > _risk_rank(max_risk):
            max_risk = r
        if c > max_conf:
            max_conf = c
    evidence = []
    for m in matches:
        evidence.append({
            "threat_type": m.get("threatType", "UNKNOWN"),
            "platform_type": m.get("platformType", ""),
            "threat_entry_type": m.get("threatEntryType", ""),
            "matched_url": m.get("threat", {}).get("url", url),
            "cache_duration": m.get("cacheDuration", ""),
        })
    return LookupResult(
        indicator=indicator,
        indicator_type=indicator_type,
        matched=True,
        risk=max_risk,
        confidence=max_conf,
        source=source,
        summary=f"Google Safe Browsing flagged: {', '.join(unique_types)}",
        evidence=evidence,
        references=[{
            "source": "Google Safe Browsing",
            "url": "https://safebrowsing.google.com/",
            "threat_types": unique_types,
        }],
        latency=latency,
    )


def _risk_rank(risk: str) -> int:
    ranks = {"CRITICAL": 5, "HIGH": 4, "MEDIUM": 3, "LOW": 2, "UNKNOWN": 1}
    return ranks.get(risk, 0)
