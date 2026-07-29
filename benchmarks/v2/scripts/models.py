import logging
import warnings
from typing import Dict, List, Optional, Tuple

import numpy as np

logger = logging.getLogger(__name__)

_has_transformers = False
_has_sentence_transformers = False

try:
    from transformers import AutoModelForSequenceClassification, AutoTokenizer, pipeline as hf_pipeline
    _has_transformers = True
except ImportError:
    pass

try:
    from sentence_transformers import SentenceTransformer
    _has_sentence_transformers = True
except ImportError:
    pass


def train_tfidf_lr(
    texts: List[str], labels: List[int], max_features: int = 5000, **kwargs
) -> Tuple:
    from sklearn.feature_extraction.text import TfidfVectorizer
    from sklearn.linear_model import LogisticRegression

    vectorizer = TfidfVectorizer(
        max_features=max_features,
        ngram_range=(1, 2),
        stop_words="english",
        **{k: v for k, v in kwargs.items() if k in ("ngram_range", "stop_words", "min_df", "max_df")},
    )
    X = vectorizer.fit_transform(texts)
    model = LogisticRegression(
        class_weight="balanced",
        max_iter=1000,
        random_state=42,
        **{k: v for k, v in kwargs.items() if k in ("C", "penalty", "solver")},
    )
    model.fit(X, labels)
    logger.info("TF-IDF LR trained on %d samples (vocab size: %d)", len(texts), len(vectorizer.vocabulary_))
    return vectorizer, model


def train_tfidf_svm(
    texts: List[str], labels: List[int], max_features: int = 5000, **kwargs
) -> Tuple:
    from sklearn.feature_extraction.text import TfidfVectorizer
    from sklearn.svm import LinearSVC

    vectorizer = TfidfVectorizer(
        max_features=max_features,
        ngram_range=(1, 2),
        stop_words="english",
        **{k: v for k, v in kwargs.items() if k in ("ngram_range", "stop_words", "min_df", "max_df")},
    )
    X = vectorizer.fit_transform(texts)
    model = LinearSVC(
        class_weight="balanced",
        max_iter=2000,
        random_state=42,
        **{k: v for k, v in kwargs.items() if k in ("C", "loss", "penalty")},
    )
    model.fit(X, labels)
    logger.info("TF-IDF SVM trained on %d samples (vocab size: %d)", len(texts), len(vectorizer.vocabulary_))
    return vectorizer, model


def train_embedding_model(
    texts: List[str], labels: List[int], model_name: str = "all-MiniLM-L6-v2"
) -> Tuple:
    if not _has_sentence_transformers:
        logger.warning("sentence-transformers not installed; falling back to TF-IDF + LR")
        vec, model = train_tfidf_lr(texts, labels)
        return vec, model

    from sklearn.linear_model import LogisticRegression
    from sklearn.preprocessing import StandardScaler

    logger.info("Loading sentence transformer: %s", model_name)
    embedder = SentenceTransformer(model_name)
    logger.info("Embedding %d texts...", len(texts))
    embeddings = embedder.encode(texts, show_progress_bar=True, convert_to_numpy=True)
    scaler = StandardScaler()
    embeddings_scaled = scaler.fit_transform(embeddings)
    classifier = LogisticRegression(class_weight="balanced", max_iter=1000, random_state=42)
    classifier.fit(embeddings_scaled, labels)
    logger.info("Embedding classifier trained on %d samples (dim=%d)", len(texts), embeddings.shape[1])
    return (embedder, scaler, classifier)


def train_transformer(
    texts: List[str], labels: List[int], model_name: str = "distilbert-base-uncased"
) -> Tuple:
    if not _has_transformers:
        logger.warning("transformers not installed; falling back to TF-IDF + LR")
        vec, model = train_tfidf_lr(texts, labels)
        return vec, model

    import torch

    device = 0 if torch.cuda.is_available() else -1
    logger.info("Loading transformer: %s (device=%s)", model_name, "cuda" if device == 0 else "cpu")
    tokenizer = AutoTokenizer.from_pretrained(model_name)
    model = AutoModelForSequenceClassification.from_pretrained(model_name, num_labels=2)
    trainer_cls = _get_trainer_cls()
    train_encodings = tokenizer(texts, truncation=True, padding=True, max_length=512, return_tensors="pt")
    train_dataset = _TransformerDataset(train_encodings, labels)
    trainer = trainer_cls(
        model=model,
        args=_get_training_args(),
        train_dataset=train_dataset,
    )
    trainer.train()
    logger.info("Transformer fine-tuned on %d samples", len(texts))
    return tokenizer, model


class _TransformerDataset:
    def __init__(self, encodings, labels):
        self.encodings = encodings
        self.labels = labels

    def __getitem__(self, idx):
        item = {k: v[idx] for k, v in self.encodings.items()}
        item["labels"] = self.labels[idx]
        return item

    def __len__(self):
        return len(self.labels)


def _get_trainer_cls():
    from transformers import Trainer, TrainingArguments
    return Trainer


def _get_training_args():
    from transformers import TrainingArguments
    return TrainingArguments(
        output_dir="C:\\Users\\jeeva\\AppData\\Local\\Temp\\opencode\\transformer_cache",
        num_train_epochs=3,
        per_device_train_batch_size=16,
        logging_steps=50,
        save_strategy="no",
        report_to="none",
        disable_tqdm=True,
    )


class ModelWrapper:
    def __init__(self, model, vectorizer=None, threshold=0.5):
        self.model = model
        self.vectorizer = vectorizer
        self.threshold = threshold
        self._embedder = None
        self._scaler = None
        self._tokenizer = None
        self._is_transformer = False

    def predict(self, text: str) -> Dict:
        if self._is_transformer:
            return self._predict_transformer(text)
        if self._embedder is not None:
            return self._predict_embedding(text)
        return self._predict_sklearn(text)

    def predict_batch(self, texts: List[str]) -> List[Dict]:
        return [self.predict(t) for t in texts]

    def _predict_sklearn(self, text: str) -> Dict:
        vec = self.vectorizer.transform([text])
        proba = getattr(self.model, "predict_proba", None)
        if proba is not None:
            probs = self.model.predict_proba(vec)[0]
            pred = 1 if probs[1] >= self.threshold else 0
            confidence = float(probs[1]) if pred == 1 else float(probs[0])
        else:
            pred = int(self.model.predict(vec)[0])
            confidence = float(abs(self.model.decision_function(vec)[0])) if hasattr(self.model, "decision_function") else 0.5
        return {
            "prediction": "scam" if pred == 1 else "safe",
            "confidence": confidence,
            "probabilities": {"safe": float(1 - confidence), "scam": float(confidence)} if proba is not None else {},
        }

    def _predict_embedding(self, text: str) -> Dict:
        emb = self._embedder.encode([text], convert_to_numpy=True)
        emb_scaled = self._scaler.transform(emb)
        probs = self.model.predict_proba(emb_scaled)[0]
        pred = 1 if probs[1] >= self.threshold else 0
        return {
            "prediction": "scam" if pred == 1 else "safe",
            "confidence": float(probs[1]) if pred == 1 else float(probs[0]),
            "probabilities": {"safe": float(probs[0]), "scam": float(probs[1])},
        }

    def _predict_transformer(self, text: str) -> Dict:
        import torch

        inputs = self._tokenizer(text, truncation=True, padding=True, max_length=512, return_tensors="pt")
        with torch.no_grad():
            outputs = self.model(**inputs)
            probs = torch.nn.functional.softmax(outputs.logits, dim=-1)[0].numpy()
        pred = 1 if probs[1] >= self.threshold else 0
        return {
            "prediction": "scam" if pred == 1 else "safe",
            "confidence": float(probs[1]) if pred == 1 else float(probs[0]),
            "probabilities": {"safe": float(probs[0]), "scam": float(probs[1])},
        }

    def save(self, path: str):
        import os
        import joblib

        os.makedirs(path, exist_ok=True)
        meta = {
            "threshold": self.threshold,
            "is_transformer": self._is_transformer,
            "has_embedder": self._embedder is not None,
            "has_scaler": self._scaler is not None,
            "has_tokenizer": self._tokenizer is not None,
        }
        joblib.dump(meta, os.path.join(path, "meta.joblib"))
        if self._is_transformer:
            self.model.save_pretrained(os.path.join(path, "transformer_model"))
            self._tokenizer.save_pretrained(os.path.join(path, "transformer_model"))
        else:
            joblib.dump(self.model, os.path.join(path, "model.joblib"))
        if self.vectorizer is not None:
            joblib.dump(self.vectorizer, os.path.join(path, "vectorizer.joblib"))
        if self._embedder is not None:
            joblib.dump(self._scaler, os.path.join(path, "scaler.joblib"))
            import torch
            torch.save(self._embedder, os.path.join(path, "embedder.pt"))
        logger.info("ModelWrapper saved to %s", path)

    @classmethod
    def load(cls, path: str) -> "ModelWrapper":
        import os
        import joblib

        meta = joblib.load(os.path.join(path, "meta.joblib"))
        wrapper = cls.__new__(cls)
        wrapper.threshold = meta["threshold"]
        wrapper._is_transformer = meta["is_transformer"]
        wrapper._embedder = None
        wrapper._scaler = None
        wrapper._tokenizer = None
        if meta["is_transformer"]:
            from transformers import AutoModelForSequenceClassification, AutoTokenizer
            wrapper._tokenizer = AutoTokenizer.from_pretrained(os.path.join(path, "transformer_model"))
            wrapper.model = AutoModelForSequenceClassification.from_pretrained(os.path.join(path, "transformer_model"))
        else:
            wrapper.model = joblib.load(os.path.join(path, "model.joblib"))
        vec_path = os.path.join(path, "vectorizer.joblib")
        wrapper.vectorizer = joblib.load(vec_path) if os.path.exists(vec_path) else None
        scaler_path = os.path.join(path, "scaler.joblib")
        if meta.get("has_scaler") and os.path.exists(scaler_path):
            wrapper._scaler = joblib.load(scaler_path)
        embedder_path = os.path.join(path, "embedder.pt")
        if meta.get("has_embedder") and os.path.exists(embedder_path):
            import torch
            wrapper._embedder = torch.load(embedder_path, weights_only=False)
        logger.info("ModelWrapper loaded from %s", path)
        return wrapper


def create_model(model_type: str, **kwargs) -> "ModelWrapper":
    model_type = model_type.lower()
    texts = kwargs.pop("texts", None)
    labels = kwargs.pop("labels", None)
    if texts is None or labels is None:
        raise ValueError("'texts' and 'labels' must be provided as kwargs to create_model")

    if model_type == "tfidf_lr":
        vec, model = train_tfidf_lr(texts, labels, **kwargs)
        return ModelWrapper(model, vectorizer=vec)
    elif model_type == "tfidf_svm":
        vec, model = train_tfidf_svm(texts, labels, **kwargs)
        wrapper = ModelWrapper(model, vectorizer=vec)
        return wrapper
    elif model_type == "embedding":
        result = train_embedding_model(texts, labels, **kwargs)
        if len(result) == 3:
            embedder, scaler, classifier = result
            wrapper = ModelWrapper(classifier, vectorizer=None)
            wrapper._embedder = embedder
            wrapper._scaler = scaler
            return wrapper
        else:
            vec, model = result
            return ModelWrapper(model, vectorizer=vec)
    elif model_type == "transformer":
        result = train_transformer(texts, labels, **kwargs)
        if len(result) == 2 and not isinstance(result[0], type(None)) and hasattr(result[0], "vocab_size"):
            tokenizer, model = result
            wrapper = ModelWrapper(model, vectorizer=None)
            wrapper._tokenizer = tokenizer
            wrapper._is_transformer = True
            return wrapper
        else:
            vec, model = result
            return ModelWrapper(model, vectorizer=vec)
    else:
        raise ValueError(f"Unknown model_type: {model_type}. Choose from {available_models()}")


def available_models() -> List[str]:
    models = ["tfidf_lr", "tfidf_svm"]
    if _has_sentence_transformers:
        models.append("embedding")
    else:
        models.append("embedding (sentence-transformers not installed, falls back to TF-IDF)")
    if _has_transformers:
        models.append("transformer")
    else:
        models.append("transformer (transformers not installed, falls back to TF-IDF)")
    return models
