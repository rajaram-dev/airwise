import pytest

from app.models.air import AqiCategory
from app.models.plan import Audience, TipKind
from app.models.profile import Household
from app.rules.audience import ADVICE, Band, audiences_for, band_for, build_audience_advice


@pytest.mark.parametrize(
    ("category", "band"),
    [
        (AqiCategory.GOOD, Band.CLEAR),
        (AqiCategory.MODERATE, Band.CLEAR),
        (AqiCategory.UNHEALTHY_SENSITIVE, Band.CAUTION),
        (AqiCategory.UNHEALTHY, Band.CAUTION),
        (AqiCategory.VERY_UNHEALTHY, Band.DANGER),
        (AqiCategory.HAZARDOUS, Band.DANGER),
    ],
)
def test_band_for(category: AqiCategory, band: Band) -> None:
    assert band_for(category) is band


def test_adults_always_included() -> None:
    assert audiences_for(Household()) == [Audience.ADULTS]


def test_all_groups_in_order() -> None:
    household = Household(children=True, elderly=True, pregnant=True)
    assert audiences_for(household) == [
        Audience.CHILDREN,
        Audience.ADULTS,
        Audience.SENSITIVE,
        Audience.PREGNANCY,
    ]


@pytest.mark.parametrize("flag", ["elderly", "respiratory_condition"])
def test_sensitive_group_flags(flag: str) -> None:
    assert Audience.SENSITIVE in audiences_for(Household(**{flag: True}))


def test_pregnancy_has_its_own_card() -> None:
    groups = audiences_for(Household(pregnant=True))
    assert groups == [Audience.ADULTS, Audience.PREGNANCY]


def test_pregnancy_danger_advice() -> None:
    cards = build_audience_advice(AqiCategory.VERY_UNHEALTHY, Household(pregnant=True))
    pregnancy = cards[-1]
    assert pregnancy.title == "During pregnancy"
    assert pregnancy.tips[0].kind is TipKind.AVOID
    assert "baby" in pregnancy.subtitle


def test_every_audience_and_band_has_three_tips() -> None:
    for audience in Audience:
        for band in Band:
            subtitle, tips = ADVICE[audience][band]
            assert subtitle
            assert len(tips) == 3


def test_danger_advice_for_children_says_avoid_outdoor_play() -> None:
    cards = build_audience_advice(AqiCategory.HAZARDOUS, Household(children=True))
    children = cards[0]
    assert children.title == "For children"
    assert children.tips[0].kind is TipKind.AVOID
    assert "outdoor play" in children.tips[0].text


def test_clear_air_advice_is_positive() -> None:
    cards = build_audience_advice(AqiCategory.GOOD, Household())
    assert all(tip.kind is TipKind.DO for tip in cards[0].tips)
