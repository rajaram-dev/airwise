"""Builders for test data. Keeps tests short and readable."""

from datetime import datetime, timedelta, timezone
from typing import Any

from app.models.air import AirReading, ForecastHour
from app.models.profile import UserProfile
from app.rules.aqi import CATEGORY_LABELS, HEALTH_MESSAGES, classify_aqi
from app.rules.context import RuleContext, build_context

IST = timezone(timedelta(hours=5, minutes=30))
NOW = datetime(2026, 11, 25, 9, 0, tzinfo=IST)


def pm_for(aqi: int) -> float:
    """Simple stand-in PM2.5 value that rises with AQI."""
    return aqi / 2


def make_forecast(
    aqi_by_hour: dict[int, int] | None = None,
    default_aqi: int = 300,
    start: datetime = NOW,
    hours: int = 24,
) -> list[ForecastHour]:
    """Hourly forecast from ``start``; hours not in ``aqi_by_hour`` use ``default_aqi``."""
    overrides = aqi_by_hour or {}
    forecast = []
    for offset in range(hours):
        moment = start + timedelta(hours=offset)
        aqi = overrides.get(moment.hour, default_aqi)
        forecast.append(ForecastHour(time=moment, aqi=aqi, pm2_5=pm_for(aqi)))
    return forecast


def make_reading(aqi: int) -> AirReading:
    """Current reading for a given AQI."""
    category = classify_aqi(aqi)
    return AirReading(
        aqi=aqi,
        category=category,
        category_label=CATEGORY_LABELS[category],
        pm2_5=pm_for(aqi),
        pm10=pm_for(aqi) * 1.5,
        dominant_pollutant="pm2_5",
        observed_at=NOW,
        health_message=HEALTH_MESSAGES[category],
    )


def make_profile(**overrides: Any) -> UserProfile:
    """Healthy adult working from home in Delhi unless overridden."""
    data: dict[str, Any] = {"latitude": 28.61, "longitude": 77.21, "location_name": "Delhi"}
    data.update(overrides)
    return UserProfile.model_validate(data)


def make_context(
    aqi: int = 287,
    forecast: list[ForecastHour] | None = None,
    **profile_overrides: Any,
) -> RuleContext:
    """Full rule context with sensible defaults."""
    return build_context(
        make_profile(**profile_overrides),
        make_reading(aqi),
        forecast if forecast is not None else make_forecast(default_aqi=aqi),
        NOW,
    )
