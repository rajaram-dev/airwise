"""Household risk assessment from air quality and sensitivity."""

from app.models.air import AqiCategory
from app.models.plan import Risk, RiskLevel
from app.models.profile import Household
from app.rules.aqi import CATEGORY_LABELS, severity

SENSITIVITY_REASONS: dict[str, str] = {
    "children": "Children at home breathe faster and are more affected by smog",
    "elderly": "Older adults at home are more sensitive to polluted air",
    "respiratory_condition": "Someone at home has a lung or heart condition",
    "pregnant": "Pregnancy increases sensitivity to air pollution",
}

# Score = category severity (0-5) + 1 if anyone at home is sensitive.
_LEVEL_BY_SCORE: tuple[RiskLevel, ...] = (
    RiskLevel.LOW,  # 0
    RiskLevel.LOW,  # 1
    RiskLevel.MODERATE,  # 2
    RiskLevel.HIGH,  # 3
)


def sensitivity_reasons(household: Household) -> list[str]:
    """Return a plain-language reason for each sensitive group present at home."""
    flags = household.model_dump()
    return [reason for field, reason in SENSITIVITY_REASONS.items() if flags.get(field)]


def assess_risk(category: AqiCategory, household: Household) -> Risk:
    """Combine today's air category with household sensitivity into a risk level.

    Args:
        category: Current AQI category.
        household: Who lives at home.

    Returns:
        Risk with a level and the reasons behind it.
    """
    score = severity(category) + (1 if household.is_sensitive else 0)
    level = _LEVEL_BY_SCORE[score] if score < len(_LEVEL_BY_SCORE) else RiskLevel.SEVERE
    reasons = [f"Air quality is {CATEGORY_LABELS[category]}", *sensitivity_reasons(household)]
    return Risk(level=level, reasons=reasons)
