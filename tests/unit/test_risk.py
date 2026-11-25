import pytest

from app.models.air import AqiCategory
from app.models.plan import RiskLevel
from app.models.profile import Household
from app.rules.risk import SENSITIVITY_REASONS, assess_risk, sensitivity_reasons

HEALTHY = Household()
SENSITIVE = Household(children=True)


@pytest.mark.parametrize(
    ("category", "household", "expected"),
    [
        (AqiCategory.GOOD, HEALTHY, RiskLevel.LOW),
        (AqiCategory.GOOD, SENSITIVE, RiskLevel.LOW),
        (AqiCategory.MODERATE, HEALTHY, RiskLevel.LOW),
        (AqiCategory.MODERATE, SENSITIVE, RiskLevel.MODERATE),
        (AqiCategory.UNHEALTHY_SENSITIVE, HEALTHY, RiskLevel.MODERATE),
        (AqiCategory.UNHEALTHY_SENSITIVE, SENSITIVE, RiskLevel.HIGH),
        (AqiCategory.UNHEALTHY, HEALTHY, RiskLevel.HIGH),
        (AqiCategory.UNHEALTHY, SENSITIVE, RiskLevel.SEVERE),
        (AqiCategory.VERY_UNHEALTHY, HEALTHY, RiskLevel.SEVERE),
        (AqiCategory.HAZARDOUS, SENSITIVE, RiskLevel.SEVERE),
    ],
)
def test_assess_risk_levels(
    category: AqiCategory, household: Household, expected: RiskLevel
) -> None:
    assert assess_risk(category, household).level is expected


def test_risk_reasons_mention_air_and_each_sensitive_group() -> None:
    household = Household(children=True, respiratory_condition=True)
    risk = assess_risk(AqiCategory.UNHEALTHY, household)
    assert risk.reasons[0] == "Air quality is Unhealthy"
    assert SENSITIVITY_REASONS["children"] in risk.reasons
    assert SENSITIVITY_REASONS["respiratory_condition"] in risk.reasons
    assert len(risk.reasons) == 3


def test_no_sensitivity_reasons_for_healthy_household() -> None:
    assert sensitivity_reasons(HEALTHY) == []


def test_household_is_sensitive_for_each_flag() -> None:
    for field in SENSITIVITY_REASONS:
        assert Household(**{field: True}).is_sensitive
    assert not HEALTHY.is_sensitive
