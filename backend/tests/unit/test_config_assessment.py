from core.config.assessment import (
    LOW_CONFIDENCE_THRESHOLD,
    MEDIUM_CONFIDENCE_THRESHOLD,
    HIGH_CONFIDENCE_THRESHOLD,
    ASSESSMENT_MAX_SCORE,
    ASSESSMENT_ML_WEIGHT,
    ASSESSMENT_DECISION_WEIGHT,
    ASSESSMENT_EVIDENCE_WEIGHT,
    ASSESSMENT_INDICATOR_WEIGHT,
    ASSESSMENT_ENTITY_WEIGHT,
    ASSESSMENT_CONFLICT_PENALTY,
)


def test_confidence_threshold_ordering():
    assert LOW_CONFIDENCE_THRESHOLD < MEDIUM_CONFIDENCE_THRESHOLD < HIGH_CONFIDENCE_THRESHOLD


def test_low_threshold_value():
    assert LOW_CONFIDENCE_THRESHOLD == 0.4


def test_medium_threshold_value():
    assert MEDIUM_CONFIDENCE_THRESHOLD == 0.7


def test_high_threshold_value():
    assert HIGH_CONFIDENCE_THRESHOLD == 0.8


def test_low_below_medium():
    assert LOW_CONFIDENCE_THRESHOLD < MEDIUM_CONFIDENCE_THRESHOLD


def test_medium_below_high():
    assert MEDIUM_CONFIDENCE_THRESHOLD < HIGH_CONFIDENCE_THRESHOLD


def test_assessment_weights_sum():
    total = (
        ASSESSMENT_ML_WEIGHT
        + ASSESSMENT_DECISION_WEIGHT
        + ASSESSMENT_EVIDENCE_WEIGHT
        + ASSESSMENT_INDICATOR_WEIGHT
        + ASSESSMENT_ENTITY_WEIGHT
        + ASSESSMENT_CONFLICT_PENALTY
    )
    assert abs(total - 1.0) < 0.01


def test_max_score_positive():
    assert ASSESSMENT_MAX_SCORE > 0


def test_no_zero_weights():
    assert ASSESSMENT_ML_WEIGHT > 0
    assert ASSESSMENT_DECISION_WEIGHT > 0
    assert ASSESSMENT_EVIDENCE_WEIGHT > 0
