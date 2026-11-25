"""Advice cards for each group of people living at home."""

from enum import Enum

from app.models.air import AqiCategory
from app.models.plan import Audience, AudienceAdvice, Tip, TipKind
from app.models.profile import Household
from app.rules.aqi import is_at_least


class Band(Enum):
    """Coarse severity bands that decide which tips apply."""

    CLEAR = "clear"  # Good, Moderate
    CAUTION = "caution"  # Unhealthy for Sensitive Groups, Unhealthy
    DANGER = "danger"  # Very Unhealthy, Hazardous


def band_for(category: AqiCategory) -> Band:
    """Map an AQI category to a severity band."""
    if is_at_least(category, AqiCategory.VERY_UNHEALTHY):
        return Band.DANGER
    if is_at_least(category, AqiCategory.UNHEALTHY_SENSITIVE):
        return Band.CAUTION
    return Band.CLEAR


DO, AVOID = TipKind.DO, TipKind.AVOID

TITLES: dict[Audience, str] = {
    Audience.CHILDREN: "For children",
    Audience.ADULTS: "For adults",
    Audience.SENSITIVE: "For sensitive people",
    Audience.PREGNANCY: "During pregnancy",
}

# (subtitle, tips) per audience and band. Wording is general wellbeing guidance.
ADVICE: dict[Audience, dict[Band, tuple[str, tuple[tuple[TipKind, str], ...]]]] = {
    Audience.CHILDREN: {
        Band.CLEAR: (
            "A good day to play outside.",
            (
                (DO, "Outdoor play and sports are fine today."),
                (DO, "Keep windows open for fresh air."),
                (DO, "Teach them to notice if the air looks hazy."),
            ),
        ),
        Band.CAUTION: (
            "Children breathe faster, so they take in more smog.",
            (
                (AVOID, "Avoid long or hard outdoor play."),
                (DO, "Keep outdoor time short and in the cleanest hours."),
                (DO, "Choose indoor games for most of the day."),
            ),
        ),
        Band.DANGER: (
            "Higher risk from today's air.",
            (
                (AVOID, "Avoid outdoor play and sports."),
                (DO, "Keep them indoors in a room with filtered air."),
                (DO, "Watch for coughing, wheezing or breathing discomfort."),
            ),
        ),
    },
    Audience.ADULTS: {
        Band.CLEAR: (
            "Enjoy your usual routine.",
            (
                (DO, "Outdoor exercise is fine today."),
                (DO, "Walk or cycle for short trips to keep the air clean."),
                (DO, "Air out your home while the air is clean."),
            ),
        ),
        Band.CAUTION: (
            "Stay active, but plan around the smog.",
            (
                (DO, "Exercise in the cleanest hours or indoors."),
                (AVOID, "Avoid busy roads when walking."),
                (DO, "Carry an N95 mask if you'll be outside for long."),
            ),
        ),
        Band.DANGER: (
            "Stay active, but stay smart.",
            (
                (DO, "Do indoor workouts like yoga or stretching."),
                (DO, "If you step out, wear a well-fitted N95 or FFP2 mask."),
                (AVOID, "Avoid smoking and second-hand smoke."),
            ),
        ),
    },
    Audience.SENSITIVE: {
        Band.CLEAR: (
            "Older adults and anyone with asthma, heart or lung conditions.",
            (
                (DO, "Normal activity is fine for most people today."),
                (DO, "Keep any prescribed inhaler or medicine with you."),
                (DO, "Pick the cleanest hours for longer walks."),
            ),
        ),
        Band.CAUTION: (
            "Older adults and anyone with asthma, heart or lung conditions.",
            (
                (AVOID, "Avoid long or hard outdoor activity."),
                (DO, "Keep any prescribed inhaler or medicine handy."),
                (DO, "Rest indoors if you feel short of breath."),
            ),
        ),
        Band.DANGER: (
            "Older adults and anyone with asthma, heart or lung conditions.",
            (
                (AVOID, "Avoid going outdoors, especially early morning and late evening."),
                (DO, "Keep any prescribed inhaler or medicine handy."),
                (DO, "Watch for breathing changes and contact a doctor if they worsen."),
            ),
        ),
    },
}


ADVICE[Audience.PREGNANCY] = {
    Band.CLEAR: (
        "Clean air today. A good day for gentle activity.",
        (
            (DO, "Gentle walks outdoors are fine today."),
            (DO, "Air out your home while the air is clean."),
            (DO, "Keep up your regular check-ups."),
        ),
    ),
    Band.CAUTION: (
        "Polluted air can affect you and your baby, so take extra care.",
        (
            (AVOID, "Avoid long walks near busy roads."),
            (DO, "Walk in the cleanest hours or indoors."),
            (DO, "Spend most of the day in your cleanest room."),
        ),
    ),
    Band.DANGER: (
        "Polluted air can affect you and your baby, so take extra care.",
        (
            (AVOID, "Avoid outdoor exertion today."),
            (DO, "Stay in a room with filtered air and windows closed."),
            (DO, "Keep taking any prescribed medicine and see a doctor if you feel breathless."),
        ),
    ),
}


def audiences_for(household: Household) -> list[Audience]:
    """Return which groups live at home. Adults are always included."""
    groups = []
    if household.children:
        groups.append(Audience.CHILDREN)
    groups.append(Audience.ADULTS)
    if household.elderly or household.respiratory_condition:
        groups.append(Audience.SENSITIVE)
    if household.pregnant:
        groups.append(Audience.PREGNANCY)
    return groups


def build_audience_advice(category: AqiCategory, household: Household) -> list[AudienceAdvice]:
    """Return one advice card per group living at home, tuned to today's air."""
    band = band_for(category)
    cards = []
    for audience in audiences_for(household):
        subtitle, tips = ADVICE[audience][band]
        cards.append(
            AudienceAdvice(
                audience=audience,
                title=TITLES[audience],
                subtitle=subtitle,
                tips=[Tip(kind=kind, text=text) for kind, text in tips],
            )
        )
    return cards
