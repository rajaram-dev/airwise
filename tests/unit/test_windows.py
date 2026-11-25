from datetime import timedelta

from app.rules.windows import (
    cleanest_daytime_hour,
    dirtiest_daytime_hour,
    find_best_windows,
    forecast_at_hour,
    upcoming_daytime_hours,
)
from tests.factories import NOW, make_forecast


def test_picks_cleanest_daytime_window() -> None:
    forecast = make_forecast({14: 80, 15: 90, 11: 140, 12: 140})
    windows = find_best_windows(forecast, now=NOW, limit_aqi=150)
    best = windows[0]
    assert best.start.hour == 14
    assert best.end.hour == 16
    assert best.avg_aqi == 85
    assert best.avg_pm2_5 == 42.5


def test_ignores_night_hours_even_if_cleaner() -> None:
    forecast = make_forecast({2: 20, 3: 20, 4: 20, 16: 120, 17: 120})
    windows = find_best_windows(forecast, now=NOW, limit_aqi=150)
    assert windows[0].start.hour == 16


def test_returns_empty_when_no_hour_is_clean_enough() -> None:
    forecast = make_forecast(default_aqi=250)
    assert find_best_windows(forecast, now=NOW, limit_aqi=150) == []


def test_window_requires_every_hour_under_limit() -> None:
    forecast = make_forecast({14: 50, 15: 160})
    assert find_best_windows(forecast, now=NOW, limit_aqi=150) == []


def test_windows_do_not_overlap_and_respect_max() -> None:
    forecast = make_forecast({10: 60, 11: 60, 12: 70, 13: 70, 15: 80, 16: 80})
    windows = find_best_windows(forecast, now=NOW, limit_aqi=150, max_windows=2)
    assert len(windows) == 2
    first, second = windows
    assert first.end <= second.start or second.end <= first.start


def test_skips_gaps_in_forecast() -> None:
    forecast = [h for h in make_forecast({14: 50, 15: 50, 16: 50}) if h.time.hour != 15]
    windows = find_best_windows(forecast, now=NOW, limit_aqi=150)
    assert windows == []


def test_upcoming_hours_limited_to_next_24h() -> None:
    forecast = make_forecast(hours=48, default_aqi=100)
    hours = upcoming_daytime_hours(forecast, NOW)
    assert all(NOW <= h.time < NOW + timedelta(hours=24) for h in hours)
    assert all(6 <= h.time.hour < 22 for h in hours)


def test_forecast_at_hour_finds_next_occurrence() -> None:
    forecast = make_forecast({18: 222})
    entry = forecast_at_hour(forecast, now=NOW, hour=18)
    assert entry is not None
    assert entry.aqi == 222


def test_forecast_at_hour_returns_none_when_missing() -> None:
    forecast = make_forecast(hours=3)
    assert forecast_at_hour(forecast, now=NOW, hour=18) is None


def test_cleanest_and_dirtiest_hours() -> None:
    forecast = make_forecast({13: 40, 20: 400}, default_aqi=200)
    clean = cleanest_daytime_hour(forecast, NOW)
    dirty = dirtiest_daytime_hour(forecast, NOW)
    assert clean is not None
    assert clean.time.hour == 13
    assert dirty is not None
    assert dirty.time.hour == 20


def test_cleanest_and_dirtiest_none_without_daytime_data() -> None:
    assert cleanest_daytime_hour([], NOW) is None
    assert dirtiest_daytime_hour([], NOW) is None
