import csv
import logging
from typing import List, Tuple

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score, classification_report

from config.settings import DATASET_PATH, MODEL_FOLDER, MODEL_PATH, VECTORIZER_PATH
from utils.text import clean_text

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)


def load_data(path: str) -> Tuple[List[str], List[int]]:
    with open(path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        texts: List[str] = []
        labels: List[int] = []
        for row in reader:
            texts.append(row["text"])
            labels.append(1 if row["label"] == "scam" else 0)
    return texts, labels


def main() -> None:
    import os
    os.makedirs(MODEL_FOLDER, exist_ok=True)

    logger.info("Loading dataset from %s", DATASET_PATH)
    texts, labels = load_data(DATASET_PATH)
    logger.info("Loaded %d samples (%d scam, %d safe)", len(texts), sum(labels), len(labels) - sum(labels))

    texts = [clean_text(t) for t in texts]

    X_train, X_test, y_train, y_test = train_test_split(
        texts, labels, test_size=0.2, random_state=42, stratify=labels
    )
    logger.info("Train size: %d, Test size: %d", len(X_train), len(X_test))

    vectorizer = TfidfVectorizer(max_features=5000, ngram_range=(1, 2), stop_words="english")
    X_train_vec = vectorizer.fit_transform(X_train)
    X_test_vec = vectorizer.transform(X_test)

    model = LogisticRegression(class_weight="balanced", max_iter=1000, random_state=42)
    model.fit(X_train_vec, y_train)

    y_pred = model.predict(X_test_vec)

    acc = accuracy_score(y_test, y_pred)
    prec = precision_score(y_test, y_pred)
    rec = recall_score(y_test, y_pred)
    f1 = f1_score(y_test, y_pred)

    print(f"Test set size: {len(y_test)}")
    print(f"Accuracy : {acc:.4f}")
    print(f"Precision: {prec:.4f}")
    print(f"Recall   : {rec:.4f}")
    print(f"F1-score : {f1:.4f}")
    print()
    print(classification_report(y_test, y_pred, target_names=["safe", "scam"]))

    import joblib
    joblib.dump(model, MODEL_PATH)
    joblib.dump(vectorizer, VECTORIZER_PATH)
    logger.info("Model and vectorizer saved to %s", MODEL_FOLDER)


if __name__ == "__main__":
    main()
