import pytest

from app.models.profile import CommuteMode
from app.rules.impact import (
    AVERAGE_URBAN_SPEED_KMH,
    EMISSION_FACTORS_KG_PER_KM,
    co2_saved_per_day,
    commute_km_one_way,
    exposure_reduction_pct,
)
from tests.factories import make_profile


def test_commute_km_uses_given_distance() -> None:
    assert commute_km_one_way(make_profile(commute_km=12, commute_minutes=60)) == 12


def test_commute_km_estimated_from_minutes() -> None:
    profile = make_profile(commute_minutes=30)
    assert commute_km_one_way(profile) == pytest.approx(AVERAGE_URBAN_SPEED_KMH / 2)


def test_co2_saved_car_to_metro_round_trip() -> None:
    # (0.17 - 0.03) kg/km x 10 km x 2 trips = 2.8 kg
    assert co2_saved_per_day(CommuteMode.CAR, CommuteMode.METRO, 10) == pytest.approx(2.8)


def test_co2_saved_never_negative() -> None:
    assert co2_saved_per_day(CommuteMode.METRO, CommuteMode.CAR, 10) == 0.0


def test_every_commute_mode_has_a_factor() -> None:
    assert set(EMISSION_FACTORS_KG_PER_KM) == set(CommuteMode)


@pytest.mark.parametrize(
    ("usual", "better", "expected"),
    [
        (200.0, 100.0, 50),
        (100.0, 100.0, 0),
        (100.0, 150.0, 0),
        (100.0, 0.0, 100),
        (0.0, 10.0, 0),
    ],
)
def test_exposure_reduction_pct(usual: float, better: float, expected: int) -> None:
    assert exposure_reduction_pct(usual, better) == expected
