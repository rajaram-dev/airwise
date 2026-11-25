import pytest

from app.models.air import AqiCategory
from app.rules.aqi import (
    CATEGORY_LABELS,
    HEALTH_MESSAGES,
    OUTDOOR_LIMIT_GENERAL,
    OUTDOOR_LIMIT_SENSITIVE,
    classify_aqi,
    is_at_least,
    outdoor_limit,
    severity,
)


@pytest.mark.parametrize(
    ("aqi", "expected"),
    [
        (0, AqiCategory.GOOD),
        (50, AqiCategory.GOOD),
        (51, AqiCategory.MODERATE),
        (100, AqiCategory.MODERATE),
        (101, AqiCategory.UNHEALTHY_SENSITIVE),
        (150, AqiCategory.UNHEALTHY_SENSITIVE),
        (151, AqiCategory.UNHEALTHY),
        (200, AqiCategory.UNHEALTHY),
        (201, AqiCategory.VERY_UNHEALTHY),
        (300, AqiCategory.VERY_UNHEALTHY),
        (301, AqiCategory.HAZARDOUS),
        (500, AqiCategory.HAZARDOUS),
    ],
)
def test_classify_aqi_boundaries(aqi: int, expected: AqiCategory) -> None:
    assert classify_aqi(aqi) is expected


def test_classify_aqi_rejects_negative() -> None:
    with pytest.raises(ValueError, match="negative"):
        classify_aqi(-1)


def test_severity_follows_category_order() -> None:
    assert severity(AqiCategory.GOOD) == 0
    assert severity(AqiCategory.HAZARDOUS) == 5


def test_is_at_least() -> None:
    assert is_at_least(AqiCategory.UNHEALTHY, AqiCategory.MODERATE)
    assert is_at_least(AqiCategory.MODERATE, AqiCategory.MODERATE)
    assert not is_at_least(AqiCategory.GOOD, AqiCategory.MODERATE)


def test_every_category_has_label_and_message() -> None:
    for category in AqiCategory:
        assert CATEGORY_LABELS[category]
        assert HEALTH_MESSAGES[category]


def test_outdoor_limit_is_stricter_for_sensitive_households() -> None:
    assert outdoor_limit(sensitive=True) == OUTDOOR_LIMIT_SENSITIVE
    assert outdoor_limit(sensitive=False) == OUTDOOR_LIMIT_GENERAL
    assert OUTDOOR_LIMIT_SENSITIVE < OUTDOOR_LIMIT_GENERAL
