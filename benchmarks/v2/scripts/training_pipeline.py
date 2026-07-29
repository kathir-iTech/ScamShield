import json
import logging
import os
import time
from typing import Any, Callable, Dict, List, Optional, Tuple

import numpy as np
from sklearn.metrics import f1_score
from sklearn.model_selection import GridSearchCV, StratifiedKFold, cross_val_score

from .benchmark_runner import compute_overall_metrics, load_benchmark_dataset, load_training_data
from .models import ModelWrapper, available_models, create_model

logger = logging.getLogger(__name__)


def train_pipeline(
    dataset_path: str,
    output_dir: str,
    model_type: str = "tfidf_lr",
    **kwargs,
) -> ModelWrapper:
    os.makedirs(output_dir, exist_ok=True)
    texts, labels = load_training_data(dataset_path)
    logger.info("Training %s on %d samples", model_type, len(texts))
    wrapper = create_model(model_type, texts=texts, labels=labels, **kwargs)
    model_dir = os.path.join(output_dir, "models", f"{model_type}_{int(time.time())}")
    wrapper.save(model_dir)
    logger.info("Model saved to %s", model_dir)
    return wrapper


def _best_model_type(texts: List[int], labels: List[int]) -> str:
    candidates = ["tfidf_lr", "tfidf_svm"]
    results: List[Tuple[str, float]] = []
    for mtype in candidates:
        try:
            wrapper = create_model(mtype, texts=texts, labels=labels)
            from sklearn.model_selection import cross_val_score
            from sklearn.feature_extraction.text import TfidfVectorizer
            from sklearn.pipeline import Pipeline

            pipeline = Pipeline([
                ("vec", TfidfVectorizer(max_features=5000, ngram_range=(1, 2), stop_words="english")),
                ("clf", wrapper.model),
            ])
            scores = cross_val_score(pipeline, texts, labels, cv=3, scoring="f1")
            mean_f1 = scores.mean()
            results.append((mtype, mean_f1))
            logger.info("CV F1 for %s: %.4f", mtype, mean_f1)
        except Exception as e:
            logger.warning("Skipping %s for best selection: %s", mtype, e)
    if not results:
        return "tfidf_lr"
    results.sort(key=lambda x: x[1], reverse=True)
    logger.info("Best model type selected: %s (F1=%.4f)", results[0][0], results[0][1])
    return results[0][0]


def train_and_save_best(dataset_path: str, output_dir: str) -> ModelWrapper:
    os.makedirs(output_dir, exist_ok=True)
    texts, labels = load_training_data(dataset_path)
    best_type = _best_model_type(texts, labels)
    logger.info("Training best model: %s", best_type)
    wrapper = create_model(best_type, texts=texts, labels=labels)
    model_dir = os.path.join(output_dir, "models", "best")
    wrapper.save(model_dir)
    logger.info("Best model saved to %s", model_dir)
    meta_path = os.path.join(output_dir, "best_model_meta.json")
    with open(meta_path, "w", encoding="utf-8") as f:
        json.dump({"model_type": best_type, "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")}, f, indent=2)
    return wrapper


def cross_validate(
    texts: List[str],
    labels: List[int],
    model_fn: Callable,
    cv: int = 5,
) -> Dict[str, Any]:
    from sklearn.feature_extraction.text import TfidfVectorizer
    from sklearn.pipeline import Pipeline

    skf = StratifiedKFold(n_splits=cv, shuffle=True, random_state=42)
    results: Dict[str, List[float]] = {"accuracy": [], "precision": [], "recall": [], "f1": []}
    for train_idx, val_idx in skf.split(texts, labels):
        X_train = [texts[i] for i in train_idx]
        y_train = [labels[i] for i in train_idx]
        X_val = [texts[i] for i in val_idx]
        y_val = [labels[i] for i in val_idx]
        wrapper = model_fn(X_train, y_train)
        preds = []
        for t in X_val:
            result = wrapper.predict(t)
            preds.append(1 if result["prediction"] == "scam" else 0)
        from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score
        results["accuracy"].append(accuracy_score(y_val, preds))
        results["precision"].append(precision_score(y_val, preds, zero_division=0))
        results["recall"].append(recall_score(y_val, preds, zero_division=0))
        results["f1"].append(f1_score(y_val, preds, zero_division=0))
    summary: Dict[str, Any] = {}
    for metric, scores in results.items():
        summary[metric] = {
            "mean": float(np.mean(scores)),
            "std": float(np.std(scores)),
            "scores": [float(s) for s in scores],
        }
    logger.info("Cross-validation (%d-fold) results: F1=%.4f +/- %.4f", cv, summary["f1"]["mean"], summary["f1"]["std"])
    return summary


def _make_model_fn(model_type: str, **fixed_kwargs) -> Callable:
    def _fn(texts, labels):
        return create_model(model_type, texts=texts, labels=labels, **fixed_kwargs)
    return _fn


def hyperparameter_search(
    texts: List[str],
    labels: List[int],
    model_type: str,
    param_grid: Dict[str, List[Any]],
    cv: int = 3,
) -> Dict[str, Any]:
    from sklearn.feature_extraction.text import TfidfVectorizer
    from sklearn.model_selection import GridSearchCV
    from sklearn.pipeline import Pipeline

    if model_type == "tfidf_lr":
        from sklearn.linear_model import LogisticRegression
        pipeline = Pipeline([
            ("vec", TfidfVectorizer(stop_words="english")),
            ("clf", LogisticRegression(class_weight="balanced", max_iter=1000, random_state=42)),
        ])
    elif model_type == "tfidf_svm":
        from sklearn.svm import LinearSVC
        pipeline = Pipeline([
            ("vec", TfidfVectorizer(stop_words="english")),
            ("clf", LinearSVC(class_weight="balanced", max_iter=2000, random_state=42)),
        ])
    else:
        raise ValueError(f"Hyperparameter search not supported for model_type: {model_type}. Use tfidf_lr or tfidf_svm.")

    gs = GridSearchCV(
        pipeline,
        param_grid,
        cv=cv,
        scoring="f1",
        n_jobs=-1,
        verbose=1,
    )
    gs.fit(texts, labels)
    best_params = gs.best_params_
    best_score = float(gs.best_score_)
    logger.info("Hyperparameter search complete. Best F1=%.4f, params=%s", best_score, best_params)

    best_wrapper = create_model(
        model_type,
        texts=texts,
        labels=labels,
        **{k.split("__")[-1]: v for k, v in best_params.items()},
    )

    cv_results = {
        "best_params": best_params,
        "best_score": best_score,
        "cv_results_": {
            "mean_test_score": [float(s) for s in gs.cv_results_["mean_test_score"]],
            "params": gs.cv_results_["params"],
        },
    }
    return {"cv_results": cv_results, "best_wrapper": best_wrapper}
