import pytest
from fastapi.testclient import TestClient


def _analyze(client: TestClient, text: str) -> dict:
    resp = client.post("/analyze/text", json={"text": text})
    assert resp.status_code == 200, f"Got {resp.status_code} for: {text[:50]}"
    return resp.json()


class TestMultilingualDetection:
    MIN_SCAM_RATE = 0.5

    def _test_scam_rate(self, client, texts: list, lang: str):
        scam_count = sum(1 for t in texts if _analyze(client, t)["prediction"] == "scam")
        rate = scam_count / len(texts)
        assert rate >= self.MIN_SCAM_RATE, (
            f"{lang}: {scam_count}/{len(texts)} scam ({rate:.0%}) "
            f"below {self.MIN_SCAM_RATE:.0%}"
        )
        return rate

    def test_hinglish_scam_detection(self, client, language_samples):
        self._test_scam_rate(client, language_samples["hi-en"], "hi-en")

    def test_tamil_scam_detection(self, client, language_samples):
        self._test_scam_rate(client, language_samples["ta"], "ta")

    def test_tanglish_scam_detection(self, client, language_samples):
        self._test_scam_rate(client, language_samples["tangling"], "tangling")

    def test_english_scam_detection(self, client, language_samples):
        self._test_scam_rate(client, language_samples["en"]["scam"], "en-scam")

    def test_english_safe_detection(self, client, language_samples):
        safe_count = 0
        texts = language_samples["en"]["safe"]
        for t in texts:
            if _analyze(client, t)["prediction"] == "safe":
                safe_count += 1
        rate = safe_count / len(texts)
        assert rate >= 0.5, f"en-safe: {safe_count}/{len(texts)} safe ({rate:.0%}) below 50%"
