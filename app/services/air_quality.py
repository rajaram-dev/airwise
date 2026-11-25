"""Open-Meteo Air Quality API client with caching."""

from datetime import datetime, timedelta, timezone
from typing import Any

import httpx
from cachetools import TTLCache

from app.core.errors import AirDataUnavailableError
from app.models.air import AirData, AirReading, ForecastHour
from app.rules.aqi import CATEGORY_LABELS, HEALTH_MESSAGES, classify_aqi

BASE_URL = "https://air-quality-api.open-meteo.com/v1/air-quality"
REQUEST_TIMEOUT_SECONDS = 8.0
COORD_PRECISION = 2  # ~1 km; improves cache hits and avoids handling precise locations

CURRENT_FIELDS = (
    "us_aqi",
    "pm2_5",
    "pm10",
    "nitrogen_dioxide",
    "ozone",
    "us_aqi_pm2_5",
    "us_aqi_pm10",
    "us_aqi_nitrogen_dioxide",
    "us_aqi_ozone",
)
HOURLY_FIELDS = ("us_aqi", "pm2_5")

# Sub-index field -> pollutant name shown to users.
SUB_INDICES: dict[str, str] = {
    "us_aqi_pm2_5": "pm2_5",
    "us_aqi_pm10": "pm10",
    "us_aqi_nitrogen_dioxide": "no2",
    "us_aqi_ozone": "o3",
}


def cache_key(latitude: float, longitude: float) -> str:
    """Return the cache key for rounded coordinates."""
    return f"aq:{latitude:.{COORD_PRECISION}f}:{longitude:.{COORD_PRECISION}f}"


class AirQualityClient:
    """Fetches current and forecast air quality for a coordinate."""

    def __init__(self, http: httpx.AsyncClient, cache: TTLCache[str, AirData]) -> None:
        """Create a client.

        Args:
            http: Shared async HTTP client.
            cache: TTL cache for parsed responses.
        """
        self._http = http
        self._cache = cache

    async def get_air_data(self, latitude: float, longitude: float) -> AirData:
        """Return air data for the location, using the cache when possible.

        Raises:
            AirDataUnavailableError: If the API fails or returns unusable data.
        """
        key = cache_key(latitude, longitude)
        cached = self._cache.get(key)
        if cached is not None:
            return cached

        payload = await self._fetch(
            round(latitude, COORD_PRECISION), round(longitude, COORD_PRECISION)
        )
        data = parse_air_response(payload)
        self._cache[key] = data
        return data

    async def _fetch(self, latitude: float, longitude: float) -> dict[str, Any]:
        params: dict[str, str | float | int] = {
            "latitude": latitude,
            "longitude": longitude,
            "current": ",".join(CURRENT_FIELDS),
            "hourly": ",".join(HOURLY_FIELDS),
            "forecast_days": 2,
            "timezone": "auto",
        }
        try:
            response = await self._http.get(
                BASE_URL, params=params, timeout=REQUEST_TIMEOUT_SECONDS
            )
            response.raise_for_status()
            payload: dict[str, Any] = response.json()
        except (httpx.HTTPError, ValueError) as exc:
            raise AirDataUnavailableError("Air quality service request failed") from exc
        return payload


def _local_time(value: str, tz: timezone) -> datetime:
    return datetime.fromisoformat(value).replace(tzinfo=tz)


def _dominant_pollutant(current: dict[str, Any]) -> str:
    scores = {name: current.get(field) for field, name in SUB_INDICES.items()}
    valid = {name: score for name, score in scores.items() if isinstance(score, int | float)}
    return max(valid, key=lambda name: valid[name]) if valid else "pm2_5"


def parse_air_response(payload: dict[str, Any]) -> AirData:
    """Convert an Open-Meteo response into AirData.

    Hours with missing values are skipped.

    Raises:
        AirDataUnavailableError: If required current values are missing or malformed.
    """
    try:
        tz = timezone(timedelta(seconds=int(payload.get("utc_offset_seconds", 0))))
        current = payload["current"]
        aqi = round(current["us_aqi"])
        category = classify_aqi(aqi)
        reading = AirReading(
            aqi=aqi,
            category=category,
            category_label=CATEGORY_LABELS[category],
            pm2_5=current["pm2_5"],
            pm10=current["pm10"],
            no2=current.get("nitrogen_dioxide"),
            o3=current.get("ozone"),
            dominant_pollutant=_dominant_pollutant(current),
            observed_at=_local_time(current["time"], tz),
            health_message=HEALTH_MESSAGES[category],
        )
        hourly = payload.get("hourly", {})
        forecast = [
            ForecastHour(time=_local_time(t, tz), aqi=round(a), pm2_5=p)
            for t, a, p in zip(
                hourly.get("time", []),
                hourly.get("us_aqi", []),
                hourly.get("pm2_5", []),
                strict=False,
            )
            if a is not None and p is not None
        ]
    except (KeyError, TypeError, ValueError) as exc:
        raise AirDataUnavailableError("Air quality response was incomplete") from exc

    return AirData(current=reading, forecast=forecast, timezone=str(payload.get("timezone", "UTC")))
