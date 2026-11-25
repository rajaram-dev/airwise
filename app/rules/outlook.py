"""24-hour outlook and quick insights derived from the forecast."""

from collections.abc import Sequence
from datetime import datetime, timedelta

from app.models.air import AirReading, ForecastHour
from app.models.plan import Outlook, Trend
from app.rules.aqi import CATEGORY_LABELS, classify_aqi
from app.rules.context import format_hour

# WHO 2021 Air Quality Guidelines: PM2.5 24-hour mean of 15 µg/m³.
WHO_PM25_DAILY = 15.0
# Changes smaller than this (in %) are reported as "about the same".
SAME_CHANGE_PCT = 5
# Average AQI shift in the second half of the next 24 h that counts as a trend.
TREND_DELTA_AQI = 25
LOOKAHEAD = timedelta(hours=24)

POLLUTANT_SOURCES: dict[str, str] = {
    "pm2_5": "PM2.5, fine particles from traffic, burning and dust",
    "pm10": "PM10, coarse dust from roads and construction",
    "no2": "nitrogen dioxide, mostly from vehicle exhaust",
    "o3": "ozone, formed when sunlight reacts with traffic fumes",
}


def _hour(moment: datetime) -> datetime:
    return moment.replace(minute=0, second=0, microsecond=0)


def _upcoming(forecast: Sequence[ForecastHour], now: datetime) -> list[ForecastHour]:
    start = _hour(now)
    return sorted(
        (h for h in forecast if start < h.time <= start + LOOKAHEAD), key=lambda h: h.time
    )


def change_vs_yesterday(
    forecast: Sequence[ForecastHour], now: datetime, current_aqi: int
) -> int | None:
    """Return the % change from the same hour yesterday, or None if unknown."""
    target = _hour(now) - LOOKAHEAD
    yesterday = next((h for h in forecast if h.time == target), None)
    if yesterday is None or yesterday.aqi <= 0:
        return None
    return round((current_aqi - yesterday.aqi) / yesterday.aqi * 100)


def build_outlook(forecast: Sequence[ForecastHour], now: datetime, current: AirReading) -> Outlook:
    """Summarise where air quality is heading over the next 24 hours."""
    upcoming = _upcoming(forecast, now)
    if not upcoming:
        return Outlook(
            trend=Trend.STEADY,
            headline=f"Forecast unavailable. Air is {current.category_label} right now.",
        )

    later = upcoming[len(upcoming) // 2 :]
    later_avg = sum(h.aqi for h in later) / len(later)
    if later_avg <= current.aqi - TREND_DELTA_AQI:
        best = min(upcoming, key=lambda h: (h.aqi, h.time))
        label = CATEGORY_LABELS[classify_aqi(best.aqi)]
        return Outlook(
            trend=Trend.IMPROVING,
            headline=f"Improving: expected to reach {label} around {format_hour(best.time)}.",
        )
    if later_avg >= current.aqi + TREND_DELTA_AQI:
        worst = max(upcoming, key=lambda h: (h.aqi, h.time))
        label = CATEGORY_LABELS[classify_aqi(worst.aqi)]
        return Outlook(
            trend=Trend.WORSENING,
            headline=f"Worsening: expected to peak at {label} around {format_hour(worst.time)}.",
        )
    return Outlook(
        trend=Trend.STEADY,
        headline=f"Likely to remain {current.category_label} over the next 24 hours.",
    )


def build_insights(
    forecast: Sequence[ForecastHour], now: datetime, current: AirReading
) -> list[str]:
    """Return up to three short, factual insights about today's air."""
    insights: list[str] = []

    change = change_vs_yesterday(forecast, now, current.aqi)
    if change is not None:
        if abs(change) < SAME_CHANGE_PCT:
            insights.append("Air quality is about the same as this time yesterday.")
        else:
            direction = "worse" if change > 0 else "better"
            insights.append(f"Air quality is {abs(change)}% {direction} than this time yesterday.")

    ratio = current.pm2_5 / WHO_PM25_DAILY
    if ratio >= 2:
        insights.append(
            f"PM2.5 is {ratio:.0f} times the WHO daily guideline of {WHO_PM25_DAILY:.0f} µg/m³."
        )
    elif ratio > 1:
        insights.append(f"PM2.5 is above the WHO daily guideline of {WHO_PM25_DAILY:.0f} µg/m³.")
    else:
        insights.append("PM2.5 is within the WHO daily guideline.")

    source = POLLUTANT_SOURCES.get(current.dominant_pollutant)
    if source:
        insights.append(f"Main pollutant: {source}.")
    return insights
