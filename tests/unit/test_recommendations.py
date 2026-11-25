from app.models.plan import ImpactBasis, RecommendationCategory, RiskLevel
from app.rules.catalog import CATALOG
from app.rules.context import format_hour
from app.rules.recommendations import MAX_PER_CATEGORY, select_recommendations
from tests.factories import NOW, make_context, make_forecast


def _ids(**kwargs: object) -> set[str]:
    return {rec.id for rec in select_recommendations(make_context(**kwargs))}  # type: ignore[arg-type]


def test_catalog_ids_are_unique() -> None:
    ids = [item.id for item in CATALOG]
    assert len(ids) == len(set(ids))


def test_severe_delhi_family_scenario() -> None:
    """Persona: parent in Delhi, child with asthma, drives 12 km, evening walks."""
    forecast = make_forecast({14: 90, 15: 90, 18: 320}, default_aqi=287)
    ctx = make_context(
        aqi=287,
        forecast=forecast,
        household={"children": True, "respiratory_condition": True},
        commute_mode="car",
        commute_km=12,
        outdoor_activity="evening_walk",
    )
    recs = {rec.id: rec for rec in select_recommendations(ctx)}

    assert ctx.risk.level is RiskLevel.SEVERE
    assert {"shift_activity_window", "protect_sensitive", "wear_n95", "consider_purifier"} <= set(
        recs
    )
    assert {"commute_metro", "work_from_home"} <= set(recs)
    assert "exercise_indoors" not in recs

    shift = recs["shift_activity_window"]
    assert shift.impact.basis is ImpactBasis.COMPUTED
    assert shift.impact.exposure_reduction_pct == 72  # (160 - 45) / 160
    assert "2 pm–4 pm" in shift.title

    assert recs["commute_metro"].impact.co2_kg_saved_per_day == 3.4  # (0.17-0.03) x 12 x 2


def test_clean_air_healthy_cyclist_gets_no_alarm() -> None:
    assert _ids(aqi=30, commute_mode="cycle", commute_minutes=20) == set()


def test_exercise_indoors_when_no_clean_window() -> None:
    ids = _ids(aqi=250, outdoor_activity="morning_walk")
    assert "exercise_indoors" in ids
    assert "shift_activity_window" not in ids


def test_purifier_owner_gets_run_tip_not_buy_tip() -> None:
    ids = _ids(aqi=180, has_air_purifier=True)
    assert "run_purifier" in ids
    assert "consider_purifier" not in ids


def test_fuel_and_heating_swaps() -> None:
    ids = _ids(aqi=60, cooking_fuel="biomass", heating="coal")
    assert {"clean_cooking_fuel", "clean_heating"} <= ids
    assert "gas_heater_safety" in _ids(aqi=60, heating="gas")


def test_no_commute_tips_for_wfh() -> None:
    ids = _ids(aqi=350, commute_mode="wfh")
    assert "commute_metro" not in ids
    assert "work_from_home" not in ids


def test_results_sorted_and_capped_per_category() -> None:
    recs = select_recommendations(
        make_context(
            aqi=350,
            household={"children": True},
            commute_mode="two_wheeler",
            commute_minutes=40,
            cooking_fuel="kerosene",
            heating="wood",
            outdoor_activity="sports",
        )
    )
    priorities = [rec.priority for rec in recs]
    assert priorities == sorted(priorities, reverse=True)
    for category in RecommendationCategory:
        assert sum(rec.category is category for rec in recs) <= MAX_PER_CATEGORY


def test_sensitive_household_boosts_health_items() -> None:
    healthy = {r.id: r.priority for r in select_recommendations(make_context(aqi=180))}
    sensitive = {
        r.id: r.priority
        for r in select_recommendations(make_context(aqi=180, household={"elderly": True}))
    }
    assert sensitive["wear_n95"] > healthy["wear_n95"]


def test_ventilation_tip_names_cleanest_hour() -> None:
    forecast = make_forecast({13: 60}, default_aqi=200)
    recs = {r.id: r for r in select_recommendations(make_context(aqi=200, forecast=forecast))}
    vent = recs["ventilate_clean_hour"]
    assert format_hour(NOW.replace(hour=13)) in vent.action
    assert vent.impact.basis is ImpactBasis.COMPUTED


def test_ventilation_falls_back_without_forecast() -> None:
    recs = {r.id: r for r in select_recommendations(make_context(aqi=200, forecast=[]))}
    vent = recs["ventilate_clean_hour"]
    assert vent.impact.basis is ImpactBasis.ESTIMATED
    assert "cleanest" in vent.action


def test_format_hour_labels() -> None:
    assert format_hour(NOW.replace(hour=0)) == "12 am"
    assert format_hour(NOW.replace(hour=12)) == "12 pm"
    assert format_hour(NOW.replace(hour=14)) == "2 pm"
