from abc import ABC, abstractmethod
from typing import Dict, List

from connectors.models import LookupResult


class BaseConnector(ABC):

    @property
    @abstractmethod
    def name(self) -> str:
        ...

    @property
    @abstractmethod
    def version(self) -> str:
        ...

    @property
    def enabled(self) -> bool:
        return True

    @property
    def priority(self) -> int:
        return 100

    @abstractmethod
    def supported_indicators(self) -> List[str]:
        ...

    @abstractmethod
    def health(self) -> Dict:
        ...

    @abstractmethod
    def lookup(self, indicator: str, indicator_type: str) -> LookupResult:
        ...

    def normalize(self, indicator: str, indicator_type: str) -> str:
        return indicator.strip().lower()

    def confidence(self, raw_result: LookupResult) -> float:
        return raw_result.confidence

    def metadata(self) -> Dict:
        return {
            "name": self.name,
            "version": self.version,
            "enabled": self.enabled,
            "priority": self.priority,
            "supported_indicators": self.supported_indicators(),
        }
