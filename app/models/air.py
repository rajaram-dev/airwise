"""Air quality data models."""

from datetime import datetime
from enum import StrEnum

from pydantic import BaseModel, Field


class AqiCategory(StrEnum):
    """US EPA AQI categories, ordered from cleanest to worst."""

    GOOD = "good"
    MODERATE = "moderate"
    UNHEALTHY_SENSITIVE = "unhealthy_sensitive"
    UNHEALTHY = "unhealthy"
    VERY_UNHEALTHY = "very_unhealthy"
    HAZARDOUS = "hazardous"


class AirReading(BaseModel):
    """Current air quality at a location."""

    aqi: int = Field(ge=0)
    category: AqiCategory
    category_label: str
    pm2_5: float = Field(ge=0)
    pm10: float = Field(ge=0)
    no2: float | None = None
    o3: float | None = None
    dominant_pollutant: str
    observed_at: datetime
    health_message: str


class ForecastHour(BaseModel):
    """One hour of forecast air quality."""

    time: datetime
    aqi: int = Field(ge=0)
    pm2_5: float = Field(ge=0)


class AirData(BaseModel):
    """Current reading plus the hourly forecast for the next 24 hours."""

    current: AirReading
    forecast: list[ForecastHour]
    timezone: str
