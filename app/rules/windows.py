"""Find the cleanest outdoor time windows in the hourly forecast."""

from collections.abc import Sequence
from datetime import datetime, timedelta
from itertools import pairwise

from app.models.air import ForecastHour
from app.models.plan import TimeWindow

DAY_START_HOUR = 6
DAY_END_HOUR = 22
LOOKAHEAD = timedelta(hours=24)
ONE_HOUR = timedelta(hours=1)


def upcoming_daytime_hours(forecast: Sequence[ForecastHour], now: datetime) -> list[ForecastHour]:
    """Return forecast hours in the next 24 h that fall between 06:00 and 22:00 local time."""
    current_hour = now.replace(minute=0, second=0, microsecond=0)
    return [
        hour
        for hour in sorted(forecast, key=lambda h: h.time)
        if current_hour <= hour.time < current_hour + LOOKAHEAD
        and DAY_START_HOUR <= hour.time.hour < DAY_END_HOUR
    ]


def _is_contiguous(hours: Sequence[ForecastHour]) -> bool:
    return all(b.time - a.time == ONE_HOUR for a, b in pairwise(hours))


def find_best_windows(
    forecast: Sequence[ForecastHour],
    *,
    now: datetime,
    limit_aqi: int,
    window_hours: int = 2,
    max_windows: int = 2,
) -> list[TimeWindow]:
    """Return the cleanest non-overlapping daytime windows, best first.

    A window qualifies only if every hour in it is at or below ``limit_aqi``.

    Args:
        forecast: Hourly forecast with timezone-aware local times.
        now: Current time in the same timezone as the forecast.
        limit_aqi: Highest acceptable AQI for any hour in the window.
        window_hours: Length of each window in hours.
        max_windows: Maximum number of windows to return.

    Returns:
        Up to ``max_windows`` windows sorted by average AQI (lowest first).
        Empty if no stretch of hours is clean enough.
    """
    hours = upcoming_daytime_hours(forecast, now)
    candidates: list[tuple[float, list[ForecastHour]]] = []
    for i in range(len(hours) - window_hours + 1):
        chunk = hours[i : i + window_hours]
        if _is_contiguous(chunk) and max(h.aqi for h in chunk) <= limit_aqi:
            candidates.append((sum(h.aqi for h in chunk) / window_hours, chunk))

    chosen: list[list[ForecastHour]] = []
    for _, chunk in sorted(candidates, key=lambda c: (c[0], c[1][0].time)):
        if len(chosen) == max_windows:
            break
        if all(
            chunk[0].time >= c[-1].time + ONE_HOUR or chunk[-1].time < c[0].time for c in chosen
        ):
            chosen.append(chunk)

    return [_to_window(chunk) for chunk in chosen]


def _to_window(chunk: Sequence[ForecastHour]) -> TimeWindow:
    return TimeWindow(
        start=chunk[0].time,
        end=chunk[-1].time + ONE_HOUR,
        avg_aqi=round(sum(h.aqi for h in chunk) / len(chunk)),
        avg_pm2_5=round(sum(h.pm2_5 for h in chunk) / len(chunk), 1),
    )


def forecast_at_hour(
    forecast: Sequence[ForecastHour], *, now: datetime, hour: int
) -> ForecastHour | None:
    """Return the next forecast entry at the given local hour (0-23), if available."""
    current_hour = now.replace(minute=0, second=0, microsecond=0)
    for entry in sorted(forecast, key=lambda h: h.time):
        if entry.time >= current_hour and entry.time.hour == hour:
            return entry
    return None


def cleanest_daytime_hour(forecast: Sequence[ForecastHour], now: datetime) -> ForecastHour | None:
    """Return the daytime hour in the next 24 h with the lowest PM2.5."""
    hours = upcoming_daytime_hours(forecast, now)
    return min(hours, key=lambda h: (h.pm2_5, h.time)) if hours else None


def dirtiest_daytime_hour(forecast: Sequence[ForecastHour], now: datetime) -> ForecastHour | None:
    """Return the daytime hour in the next 24 h with the highest PM2.5."""
    hours = upcoming_daytime_hours(forecast, now)
    return max(hours, key=lambda h: (h.pm2_5, h.time)) if hours else None
