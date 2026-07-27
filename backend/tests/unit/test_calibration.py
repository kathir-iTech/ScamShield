from core.calibration import (
    LOW_CONFIDENCE_THRESHOLD,
    MEDIUM_CONFIDENCE_THRESHOLD,
    HIGH_CONFIDENCE_THRESHOLD,
    calibrate_confidence,
    confidence_band,
    recalibrate_final_score,
)


def test_threshold_ordering():
    assert LOW_CONFIDENCE_THRESHOLD < MEDIUM_CONFIDENCE_THRESHOLD < HIGH_CONFIDENCE_THRESHOLD


def test_confidence_band_very_low():
    assert confidence_band(0.0) == "VERY_LOW"
    assert confidence_band(0.39) == "VERY_LOW"


def test_confidence_band_low():
    assert confidence_band(0.4) == "LOW"
    assert confidence_band(0.5) == "LOW"
    assert confidence_band(0.59) == "LOW"


def test_confidence_band_medium():
    assert confidence_band(0.6) == "MEDIUM"
    assert confidence_band(0.7) == "MEDIUM"
    assert confidence_band(0.79) == "MEDIUM"


def test_confidence_band_high():
    assert confidence_band(0.8) == "HIGH"
    assert confidence_band(1.0) == "HIGH"


def test_calibrate_confidence_no_adjustment():
    result = calibrate_confidence(0.75)
    assert 0.5 <= result <= 0.85


def test_calibrate_confidence_with_fpr():
    result = calibrate_confidence(0.75, historical_fpr=0.5)
    assert result < 0.75


def test_calibrate_confidence_with_boost():
    result = calibrate_confidence(0.5, rules_contribution=0.8, entity_risk=0.6)
    assert result > 0.5


def test_calibrate_confidence_clamps():
    assert calibrate_confidence(1.5) <= 1.0
    assert calibrate_confidence(-0.5) >= 0.0


def test_recalibrate_final_score_url_no_confidence():
    result = recalibrate_final_score(50.0, ml_confidence=0.2, rule_confidence=0.2, has_url=True)
    assert result < 50.0


def test_recalibrate_final_score_urgency_no_url():
    result = recalibrate_final_score(30.0, has_urgency=True, has_url=False, has_phone=False)
    assert result < 30.0


def test_recalibrate_final_score_high_ml():
    result = recalibrate_final_score(90.0, ml_confidence=0.95)
    assert result >= 90.0


def test_recalibrate_final_score_low_all():
    result = recalibrate_final_score(50.0, ml_confidence=0.2, rule_confidence=0.1)
    assert result < 50.0


def test_recalibrate_final_score_clamps():
    assert recalibrate_final_score(-10.0) >= 0.0
    assert recalibrate_final_score(200.0) <= 100.0
