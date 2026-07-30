import sys
from pathlib import Path

import numpy as np
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "v2" / "scripts"))


class TestC1ProbabilityInversion:
    def test_probabilities_not_inverted_for_safe_prediction(self):
        from models import ModelWrapper

        wrapper = ModelWrapper.__new__(ModelWrapper)
        wrapper.model = _MockModel(np.array([[0.95, 0.05]]))
        wrapper.vectorizer = _MockVectorizer()
        wrapper.threshold = 0.5
        wrapper._predict = wrapper._predict_sklearn

        result = wrapper.predict("safe message")

        assert result["prediction"] == "safe"
        assert result["confidence"] == pytest.approx(0.95, abs=1e-6)
        assert result["probabilities"]["safe"] == pytest.approx(0.95, abs=1e-6)
        assert result["probabilities"]["scam"] == pytest.approx(0.05, abs=1e-6)

    def test_probabilities_correct_for_scam_prediction(self):
        from models import ModelWrapper

        wrapper = ModelWrapper.__new__(ModelWrapper)
        wrapper.model = _MockModel(np.array([[0.05, 0.95]]))
        wrapper.vectorizer = _MockVectorizer()
        wrapper.threshold = 0.5
        wrapper._predict = wrapper._predict_sklearn

        result = wrapper.predict("scam message")

        assert result["prediction"] == "scam"
        assert result["confidence"] == pytest.approx(0.95, abs=1e-6)
        assert result["probabilities"]["safe"] == pytest.approx(0.05, abs=1e-6)
        assert result["probabilities"]["scam"] == pytest.approx(0.95, abs=1e-6)

    def test_probabilities_sum_to_one(self):
        from models import ModelWrapper

        wrapper = ModelWrapper.__new__(ModelWrapper)
        wrapper.model = _MockModel(np.array([[0.3, 0.7]]))
        wrapper.vectorizer = _MockVectorizer()
        wrapper.threshold = 0.5
        wrapper._predict = wrapper._predict_sklearn

        result = wrapper.predict("any message")
        assert abs(result["probabilities"]["safe"] + result["probabilities"]["scam"] - 1.0) < 1e-6


class _MockModel:
    def __init__(self, proba_output):
        self._proba = proba_output

    def predict_proba(self, vec):
        return self._proba

    def predict(self, vec):
        return np.array([1 if self._proba[0][1] >= 0.5 else 0])


class _MockVectorizer:
    def transform(self, texts):
        return np.array([[0.0]])
