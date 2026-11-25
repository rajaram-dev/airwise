"""US EPA AQI categories, labels and health messages."""

from app.models.air import AqiCategory

# (inclusive upper bound, category). Anything above the last bound is Hazardous.
AQI_BREAKPOINTS: tuple[tuple[int, AqiCategory], ...] = (
    (50, AqiCategory.GOOD),
    (100, AqiCategory.MODERATE),
    (150, AqiCategory.UNHEALTHY_SENSITIVE),
    (200, AqiCategory.UNHEALTHY),
    (300, AqiCategory.VERY_UNHEALTHY),
)

CATEGORY_ORDER: tuple[AqiCategory, ...] = tuple(AqiCategory)

CATEGORY_LABELS: dict[AqiCategory, str] = {
    AqiCategory.GOOD: "Good",
    AqiCategory.MODERATE: "Moderate",
    AqiCategory.UNHEALTHY_SENSITIVE: "Unhealthy for Sensitive Groups",
    AqiCategory.UNHEALTHY: "Unhealthy",
    AqiCategory.VERY_UNHEALTHY: "Very Unhealthy",
    AqiCategory.HAZARDOUS: "Hazardous",
}

HEALTH_MESSAGES: dict[AqiCategory, str] = {
    AqiCategory.GOOD: "Air is clean. Enjoy outdoor activities.",
    AqiCategory.MODERATE: (
        "Air is acceptable. Very sensitive people should limit long outdoor exertion."
    ),
    AqiCategory.UNHEALTHY_SENSITIVE: (
        "Children, older adults and people with lung or heart conditions should reduce "
        "outdoor exertion."
    ),
    AqiCategory.UNHEALTHY: "Everyone may feel effects. Sensitive groups should stay indoors.",
    AqiCategory.VERY_UNHEALTHY: "Health alert. Everyone should avoid outdoor exertion.",
    AqiCategory.HAZARDOUS: "Emergency conditions. Stay indoors with windows closed.",
}

# Highest AQI considered acceptable for outdoor exercise.
OUTDOOR_LIMIT_GENERAL = 150
OUTDOOR_LIMIT_SENSITIVE = 100


def classify_aqi(aqi: int) -> AqiCategory:
    """Return the US EPA category for an AQI value.

    Args:
        aqi: Air quality index, 0 or greater.

    Returns:
        The matching AqiCategory.

    Raises:
        ValueError: If aqi is negative.
    """
    if aqi < 0:
        raise ValueError("AQI cannot be negative")
    for upper_bound, category in AQI_BREAKPOINTS:
        if aqi <= upper_bound:
            return category
    return AqiCategory.HAZARDOUS


def severity(category: AqiCategory) -> int:
    """Return 0 (Good) to 5 (Hazardous) for comparing categories."""
    return CATEGORY_ORDER.index(category)


def is_at_least(category: AqiCategory, threshold: AqiCategory) -> bool:
    """Return True if category is as bad as or worse than threshold."""
    return severity(category) >= severity(threshold)


def outdoor_limit(sensitive: bool) -> int:
    """Return the highest AQI suitable for outdoor exercise for this household."""
    return OUTDOOR_LIMIT_SENSITIVE if sensitive else OUTDOOR_LIMIT_GENERAL
