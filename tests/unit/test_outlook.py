from datetime import timedelta

from app.models.plan import Trend
from app.rules.outlook import build_insights, build_outlook, change_vs_yesterday
from tests.factories import NOW, make_forecast, make_reading


def test_change_vs_yesterday() -> None:
    forecast = make_forecast(start=NOW - timedelta(hours=24), hours=48, default_aqi=200)
    assert change_vs_yesterday(forecast, NOW, 260) == 30
    assert change_vs_yesterday(forecast, NOW, 150) == -25


def test_change_vs_yesterday_unknown_without_history() -> None:
    assert change_vs_yesterday(make_forecast(), NOW, 200) is None


def test_outlook_steady() -> None:
    outlook = build_outlook(make_forecast(default_aqi=190), NOW, make_reading(186))
    assert outlook.trend is Trend.STEADY
    assert outlook.headline == "Likely to remain Unhealthy over the next 24 hours."


def test_outlook_improving_names_best_time() -> None:
    later = dict.fromkeys([*range(18, 24), *range(0, 9)], 60)
    forecast = make_forecast(later, default_aqi=200)
    outlook = build_outlook(forecast, NOW, make_reading(200))
    assert outlook.trend is Trend.IMPROVING
    assert "Moderate" in outlook.headline


def test_outlook_worsening_names_peak() -> None:
    later = dict.fromkeys([*range(18, 24), *range(0, 9)], 350)
    forecast = make_forecast(later, default_aqi=200)
    outlook = build_outlook(forecast, NOW, make_reading(200))
    assert outlook.trend is Trend.WORSENING
    assert "Hazardous" in outlook.headline


def test_outlook_without_forecast() -> None:
    outlook = build_outlook([], NOW, make_reading(120))
    assert outlook.trend is Trend.STEADY
    assert "unavailable" in outlook.headline


def test_insights_include_yesterday_who_and_pollutant() -> None:
    forecast = make_forecast(start=NOW - timedelta(hours=24), hours=48, default_aqi=140)
    reading = make_reading(186)  # pm2_5 = 93 in the factory
    insights = build_insights(forecast, NOW, reading)
    assert insights[0] == "Air quality is 33% worse than this time yesterday."
    assert insights[1] == "PM2.5 is 6 times the WHO daily guideline of 15 µg/m³."
    assert insights[2].startswith("Main pollutant: PM2.5")


def test_insights_same_as_yesterday_and_clean_air() -> None:
    forecast = make_forecast(start=NOW - timedelta(hours=24), hours=48, default_aqi=20)
    insights = build_insights(forecast, NOW, make_reading(20))  # pm2_5 = 10
    assert insights[0] == "Air quality is about the same as this time yesterday."
    assert insights[1] == "PM2.5 is within the WHO daily guideline."


def test_insights_slightly_above_who() -> None:
    reading = make_reading(40).model_copy(update={"pm2_5": 20.0, "dominant_pollutant": "so2"})
    insights = build_insights([], NOW, reading)
    assert insights == ["PM2.5 is above the WHO daily guideline of 15 µg/m³."]
