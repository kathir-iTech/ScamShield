from collections import Counter

import pytest
from fastapi.testclient import TestClient


def _analyze(client: TestClient, text: str) -> dict:
    resp = client.post("/analyze/text", json={"text": text})
    assert resp.status_code == 200, f"Got {resp.status_code} for: {text[:50]}"
    return resp.json()


class TestScamCategoryAccuracy:
    MIN_CORRECT = 0.6

    @pytest.mark.parametrize("category", [
        "bank_kyc", "lottery", "job", "upi", "investment",
        "courier", "government_scheme", "electricity_bill", "customs",
        "loan", "fake_customer_care", "qr_code", "crypto",
    ])
    def test_scam_category_identifies_scam(self, client, scam_samples, category):
        samples = scam_samples[category]
        correct = 0
        for text in samples:
            data = _analyze(client, text)
            if data["prediction"] == "scam":
                correct += 1
        rate = correct / len(samples)
        assert rate >= self.MIN_CORRECT, (
            f"{category}: {correct}/{len(samples)} correct ({rate:.0%}), "
            f"below {self.MIN_CORRECT:.0%} threshold"
        )

    def test_safe_texts_identified_as_safe(self, client, safe_samples):
        correct = 0
        for text in safe_samples:
            data = _analyze(client, text)
            if data["prediction"] == "safe":
                correct += 1
        rate = correct / len(safe_samples)
        assert rate >= 0.70, (
            f"safe: {correct}/{len(safe_samples)} correct ({rate:.0%}), "
            f"below 70% threshold"
        )

    def test_confidence_minimums(self, client, scam_samples):
        failures = []
        for category, samples in scam_samples.items():
            for text in samples:
                data = _analyze(client, text)
                if data["prediction"] == "scam" and data["confidence"] < 0.5:
                    failures.append(f"{category}: conf={data['confidence']:.2f}")
        assert not failures, f"Low confidence scam predictions:\n" + "\n".join(failures)


class TestFullMetrics:
    def test_precision_recall_f1(self, client, scam_samples, safe_samples):
        tp = tn = fp = fn = 0
        for text in safe_samples:
            data = _analyze(client, text)
            if data["prediction"] == "safe":
                tn += 1
            else:
                fp += 1
        for samples in scam_samples.values():
            for text in samples:
                data = _analyze(client, text)
                if data["prediction"] == "scam":
                    tp += 1
                else:
                    fn += 1
        total = tp + tn + fp + fn
        accuracy = (tp + tn) / total
        precision = tp / (tp + fp) if (tp + fp) else 0
        recall = tp / (tp + fn) if (tp + fn) else 0
        f1 = 2 * precision * recall / (precision + recall) if (precision + recall) else 0
        min_acceptable = 0.80
        report = (
            f"\n{'='*50}\n"
            f"  Accuracy : {accuracy:.2%}\n"
            f"  Precision: {precision:.2%}\n"
            f"  Recall   : {recall:.2%}\n"
            f"  F1 Score : {f1:.2%}\n"
            f"  TP={tp} TN={tn} FP={fp} FN={fn}  (total={total})\n"
            f"{'='*50}"
        )
        print(report)
        assert accuracy >= min_acceptable, f"Accuracy {accuracy:.2%} below {min_acceptable:.0%}" + report
        assert precision >= min_acceptable, f"Precision {precision:.2%} below {min_acceptable:.0%}" + report
        assert recall >= min_acceptable, f"Recall {recall:.2%} below {min_acceptable:.0%}" + report
        assert f1 >= min_acceptable, f"F1 {f1:.2%} below {min_acceptable:.0%}" + report


class TestCategoryExclusion:
    def test_all_categories_have_samples(self, scam_samples):
        from core.constants.categories import CATEGORY_KEYWORDS
        known = set(CATEGORY_KEYWORDS.keys())
        tested = set(scam_samples.keys())
        known_normalized = {k.lower().replace(" ", "_").replace("_scam", "").replace("scam_", "") for k in known}
        tested_normalized = {k.replace("_scam", "").replace("scam_", "").lower() for k in tested}
        uncovered = known_normalized - tested_normalized
        assert not uncovered, f"Categories without test samples: {uncovered}"

    def test_no_unexpected_schema_errors(self, client, scam_samples):
        for category, samples in scam_samples.items():
            for text in samples:
                data = _analyze(client, text)
                required = {"prediction", "confidence", "scam_category", "reasons", "risk_level"}
                missing = required - set(data.keys())
                assert not missing, f"{category}: missing keys {missing}"


class TestConsistency:
    def test_repeated_analysis_consistent(self, client):
        text = "URGENT: Your SBI account will be closed. Update KYC now."
        first = _analyze(client, text)
        for _ in range(3):
            subsequent = _analyze(client, text)
            assert subsequent["prediction"] == first["prediction"], "Prediction changed on re-analysis"
            assert subsequent["scam_category"] == first["scam_category"], "Category changed on re-analysis"

    def test_similar_inputs_same_category(self, client):
        variants = [
            "Your SBI bank account is deactivated. Update KYC now.",
            "SBI Alert: Account deactivated. Complete KYC verification immediately.",
            "Your SBI account has been blocked. Submit KYC documents to reactivate.",
        ]
        categories = [_analyze(client, t)["scam_category"] for t in variants]
        main = categories[0]
        mismatches = [c for c in categories if c != main]
        assert not mismatches, f"Category mismatch: {mismatches} vs expected {main}"
