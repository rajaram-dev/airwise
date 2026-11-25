"""Everything the recommendation rules need to know, computed once per request."""

from dataclasses import dataclass
from datetime import datetime

from app.models.air import AirReading, AqiCategory, ForecastHour
from app.models.plan import Risk, TimeWindow
from app.models.profile import OutdoorActivity, UserProfile
from app.rules.aqi import is_at_least, outdoor_limit
from app.rules.risk import assess_risk
from app.rules.windows import find_best_windows

# Local hour at which each outdoor habit usually happens.
USUAL_ACTIVITY_HOUR: dict[OutdoorActivity, int] = {
    OutdoorActivity.MORNING_WALK: 7,
    OutdoorActivity.EVENING_WALK: 18,
    OutdoorActivity.SPORTS: 17,
}


@dataclass(frozen=True)
class RuleContext:
    """Inputs shared by every recommendation rule."""

    profile: UserProfile
    air: AirReading
    forecast: list[ForecastHour]
    now: datetime
    risk: Risk
    windows: list[TimeWindow]
    outdoor_limit: int

    @property
    def category(self) -> AqiCategory:
        """Current AQI category."""
        return self.air.category

    def air_at_least(self, threshold: AqiCategory) -> bool:
        """Return True if current air is as bad as or worse than threshold."""
        return is_at_least(self.category, threshold)


def build_context(
    profile: UserProfile, air: AirReading, forecast: list[ForecastHour], now: datetime
) -> RuleContext:
    """Compute risk and outdoor windows once and bundle them for the rules."""
    sensitive = profile.household.is_sensitive
    limit = outdoor_limit(sensitive)
    return RuleContext(
        profile=profile,
        air=air,
        forecast=forecast,
        now=now,
        risk=assess_risk(air.category, profile.household),
        windows=find_best_windows(forecast, now=now, limit_aqi=limit),
        outdoor_limit=limit,
    )


def format_hour(moment: datetime) -> str:
    """Format a time as a short 12-hour label, e.g. '2 pm'."""
    hour = moment.hour % 12 or 12
    suffix = "am" if moment.hour < 12 else "pm"
    return f"{hour} {suffix}"


def format_window(window: TimeWindow) -> str:
    """Format a window as e.g. '2 pm–4 pm'."""
    return f"{format_hour(window.start)}–{format_hour(window.end)}"
