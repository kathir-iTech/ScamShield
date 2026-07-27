import importlib
import inspect
import pkgutil
from typing import Dict, List, Optional, Type

from connectors.base import BaseConnector
from connectors.exceptions import ConnectorConfigError


class ConnectorRegistry:
    _connectors: Dict[str, BaseConnector] = {}

    @classmethod
    def register(cls, connector: BaseConnector) -> None:
        if not isinstance(connector, BaseConnector):
            raise ConnectorConfigError(
                f"Cannot register {type(connector).__name__}: must be a BaseConnector instance"
            )
        cls._connectors[connector.name] = connector

    @classmethod
    def unregister(cls, name: str) -> None:
        cls._connectors.pop(name, None)

    @classmethod
    def get(cls, name: str) -> Optional[BaseConnector]:
        return cls._connectors.get(name)

    @classmethod
    def get_all(cls) -> Dict[str, BaseConnector]:
        return dict(cls._connectors)

    @classmethod
    def get_sorted(cls) -> List[BaseConnector]:
        return sorted(cls._connectors.values(), key=lambda c: (c.priority, c.name))

    @classmethod
    def get_by_indicator(cls, indicator_type: str) -> List[BaseConnector]:
        return sorted(
            (c for c in cls._connectors.values()
             if c.enabled and indicator_type in c.supported_indicators()),
            key=lambda c: (c.priority, c.name),
        )

    @classmethod
    def discover(cls, package: str = "connectors") -> List[str]:
        discovered = []
        try:
            pkg = importlib.import_module(package)
        except ImportError:
            return discovered
        for importer, modname, is_pkg in pkgutil.walk_packages(
            pkg.__path__, prefix=package + ".", onerror=lambda _: None
        ):
            if is_pkg:
                continue
            try:
                mod = importlib.import_module(modname)
            except Exception:
                continue
            for name, obj in inspect.getmembers(mod, inspect.isclass):
                if (
                    issubclass(obj, BaseConnector)
                    and obj is not BaseConnector
                    and not inspect.isabstract(obj)
                ):
                    try:
                        instance = obj()
                        cls.register(instance)
                        discovered.append(instance.name)
                    except Exception:
                        pass
        return discovered

    @classmethod
    def clear(cls) -> None:
        cls._connectors.clear()
