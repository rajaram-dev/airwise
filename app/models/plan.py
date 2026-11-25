"""Models for the rules engine output and the personalised plan."""

from datetime import datetime
from enum import StrEnum

from pydantic import BaseModel, Field

from app.models.air import AirReading


class RiskLevel(StrEnum):
    """Overall health risk for the household today."""

    LOW = "low"
    MODERATE = "moderate"
    HIGH = "high"
    SEVERE = "severe"


class Risk(BaseModel):
    """Risk level with plain-language reasons."""

    level: RiskLevel
    reasons: list[str]


class TimeWindow(BaseModel):
    """A stretch of hours with the cleanest forecast air."""

    start: datetime
    end: datetime
    avg_aqi: int = Field(ge=0)
    avg_pm2_5: float = Field(ge=0)


class RecommendationCategory(StrEnum):
    """Which tab a recommendation belongs to."""

    ROUTINE = "routine"
    INDOOR = "indoor"
    ALTERNATIVE = "alternative"


class ImpactBasis(StrEnum):
    """How an impact figure was derived."""

    COMPUTED = "computed"
    ESTIMATED = "estimated"


class Impact(BaseModel):
    """Direct impact of following a recommendation."""

    exposure_reduction_pct: int | None = Field(default=None, ge=0, le=100)
    co2_kg_saved_per_day: float | None = Field(default=None, ge=0)
    note: str | None = None
    basis: ImpactBasis


class Recommendation(BaseModel):
    """One actionable recommendation with its reason and impact."""

    id: str
    category: RecommendationCategory
    title: str
    action: str
    why: str
    impact: Impact
    priority: int = Field(ge=0, le=100)


class PlanSource(StrEnum):
    """Who wrote the plan's wording."""

    AI = "ai"
    RULES = "rules"


class Location(BaseModel):
    """Where the plan is for."""

    name: str
    latitude: float
    longitude: float


class Trend(StrEnum):
    """Direction of air quality over the next 24 hours."""

    IMPROVING = "improving"
    STEADY = "steady"
    WORSENING = "worsening"


class Outlook(BaseModel):
    """Plain-language forecast for the next 24 hours."""

    trend: Trend
    headline: str


class Audience(StrEnum):
    """Groups of people who get their own advice card."""

    CHILDREN = "children"
    ADULTS = "adults"
    SENSITIVE = "sensitive"
    PREGNANCY = "pregnancy"


class TipKind(StrEnum):
    """Whether a tip is something to do or to avoid."""

    DO = "do"
    AVOID = "avoid"


class Tip(BaseModel):
    """One short piece of advice."""

    kind: TipKind
    text: str


class AudienceAdvice(BaseModel):
    """Advice for one group of people at home."""

    audience: Audience
    title: str
    subtitle: str
    tips: list[Tip]


class Plan(BaseModel):
    """The personalised plan returned to the user."""

    location: Location
    air: AirReading
    risk: Risk
    best_windows: list[TimeWindow]
    recommendations: list[Recommendation]
    summary: str
    outlook: Outlook
    insights: list[str]
    audiences: list[AudienceAdvice]
    source: PlanSource
    disclaimer: str
    generated_at: datetime
