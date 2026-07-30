from __future__ import annotations

import json
import os
import threading
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from typing import Dict, List, Optional

from config.settings import MODEL_FOLDER, MODEL_PATH, VECTORIZER_PATH
from core.logger import logger

REGISTRY_PATH: str = os.path.join(MODEL_FOLDER, "registry.json")
TRAINING_LOG_PATH: str = os.path.join(MODEL_FOLDER, "training_log.json")


@dataclass
class ModelMetadata:
    version: str
    model_type: str = "LogisticRegression"
    trained_at: str = ""
    dataset_path: str = ""
    dataset_samples: int = 0
    dataset_categories: int = 0
    params: Dict = field(default_factory=dict)
    cv_metrics: Dict = field(default_factory=dict)
    test_metrics: Dict = field(default_factory=dict)
    top_features: Dict = field(default_factory=dict)
    file_path: str = ""
    vectorizer_path: str = ""
    status: str = "staging"


class ModelRegistry:
    def __init__(self, registry_path: str = REGISTRY_PATH) -> None:
        self._path = registry_path
        self._lock = threading.Lock()
        self._models: Dict[str, ModelMetadata] = {}
        self._active_version: Optional[str] = None
        self._loaded = False

    def _load(self) -> None:
        if self._loaded:
            return
        if os.path.isfile(self._path):
            try:
                with open(self._path, "r") as f:
                    data = json.load(f)
                models_data = data.get("models", {})
                self._models = {}
                for ver, mdata in models_data.items():
                    self._models[ver] = ModelMetadata(**mdata)
                self._active_version = data.get("active_version")
                self._loaded = True
                logger.info("Model registry loaded from %s", self._path)
                return
            except Exception as exc:
                logger.warning("Failed to load registry: %s — creating fresh", exc)
        self._models = {}
        self._active_version = None
        self._loaded = True
        self._auto_register_current()

    def _save(self) -> None:
        os.makedirs(os.path.dirname(self._path), exist_ok=True)
        data = {
            "models": {ver: asdict(m) for ver, m in self._models.items()},
            "active_version": self._active_version,
        }
        with open(self._path, "w") as f:
            json.dump(data, f, indent=2, default=str)

    def _auto_register_current(self) -> None:
        if not os.path.isfile(TRAINING_LOG_PATH):
            return
        try:
            with open(TRAINING_LOG_PATH, "r") as f:
                log = json.load(f)
        except Exception:
            return

        if self._models:
            return

        timestamp = log.get("timestamp", datetime.now(timezone.utc).isoformat())
        version = "v" + datetime.fromisoformat(timestamp.replace("Z", "+00:00")).strftime("%Y%m%d_%H%M%S")
        ds = log.get("dataset", {})
        cv = log.get("cross_validation", {})
        test = log.get("test_set", {})
        top = log.get("top_features", {})
        params = {
            "vectorizer": log.get("vectorizer_params", {}),
            "model": log.get("model_params", {}),
        }

        meta = ModelMetadata(
            version=version,
            model_type="LogisticRegression",
            trained_at=timestamp,
            dataset_path=ds.get("path", ""),
            dataset_samples=ds.get("n_samples", 0),
            dataset_categories=ds.get("n_categories", 0),
            params=params,
            cv_metrics=cv.get("average", {}),
            test_metrics={
                "accuracy": test.get("accuracy"),
                "f1": test.get("f1"),
                "roc_auc": test.get("roc_auc"),
                "precision": test.get("precision"),
                "recall": test.get("recall"),
                "fpr": test.get("fpr"),
                "fnr": test.get("fnr"),
            },
            top_features=top,
            file_path=MODEL_PATH,
            vectorizer_path=VECTORIZER_PATH,
            status="active",
        )
        self._models[version] = meta
        self._active_version = version
        self._save()
        logger.info("Auto-registered current model as version %s", version)

    def register_model(self, metadata: ModelMetadata) -> str:
        with self._lock:
            self._load()
            version = metadata.version
            self._models[version] = metadata
            self._save()
            logger.info("Model %s registered", version)
            return version

    def get_active_model(self) -> Optional[ModelMetadata]:
        with self._lock:
            self._load()
            if self._active_version and self._active_version in self._models:
                return self._models[self._active_version]
            return None

    def set_active_model(self, version: str) -> None:
        with self._lock:
            self._load()
            if version not in self._models:
                raise KeyError(f"Model version {version} not found in registry")
            self._models[version].status = "active"
            if self._active_version and self._active_version in self._models:
                self._models[self._active_version].status = "archived"
            self._active_version = version
            self._save()
            logger.info("Active model set to %s", version)

    def list_models(self) -> List[ModelMetadata]:
        with self._lock:
            self._load()
            return list(self._models.values())

    def get_model(self, version: str) -> Optional[ModelMetadata]:
        with self._lock:
            self._load()
            return self._models.get(version)

    def archive_model(self, version: str) -> None:
        with self._lock:
            self._load()
            if version not in self._models:
                raise KeyError(f"Model version {version} not found in registry")
            self._models[version].status = "archived"
            if self._active_version == version:
                self._active_version = None
            self._save()
            logger.info("Model %s archived", version)

    def rollback(self, version: Optional[str] = None) -> str:
        with self._lock:
            self._load()
            if version is None:
                versions = sorted(self._models.keys(), reverse=True)
                if not versions:
                    raise RuntimeError("No models in registry to roll back to")
                if self._active_version and self._active_version in versions:
                    idx = versions.index(self._active_version)
                    if idx + 1 >= len(versions):
                        raise RuntimeError("No previous version to roll back to")
                    version = versions[idx + 1]
                else:
                    version = versions[0]
            if version not in self._models:
                raise KeyError(f"Model version {version} not found in registry")
            self._models[version].status = "active"
            if self._active_version and self._active_version in self._models:
                self._models[self._active_version].status = "archived"
            self._active_version = version
            self._save()
            logger.info("Rolled back to model %s", version)
            return version

    def model_count(self) -> int:
        with self._lock:
            self._load()
            return len(self._models)


_registry_instance: Optional[ModelRegistry] = None
_registry_lock = threading.Lock()


def get_registry() -> ModelRegistry:
    global _registry_instance
    if _registry_instance is None:
        with _registry_lock:
            if _registry_instance is None:
                _registry_instance = ModelRegistry()
                _registry_instance._load()
    return _registry_instance
