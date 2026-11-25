"""Open-Meteo Geocoding API client with caching."""

from typing import Any

import httpx
from cachetools import TTLCache
from pydantic import BaseModel, ValidationError

from app.core.errors import AirDataUnavailableError, LocationNotFoundError

BASE_URL = "https://geocoding-api.open-meteo.com/v1/search"
REQUEST_TIMEOUT_SECONDS = 8.0
MAX_RESULTS = 5


class Place(BaseModel):
    """A location search result."""

    name: str
    country: str = ""
    admin1: str = ""
    latitude: float
    longitude: float
    timezone: str = "UTC"


class GeocodingClient:
    """Turns a place name into coordinates."""

    def __init__(self, http: httpx.AsyncClient, cache: TTLCache[str, list[Place]]) -> None:
        """Create a client with a shared HTTP client and a TTL cache."""
        self._http = http
        self._cache = cache

    async def search(self, query: str) -> list[Place]:
        """Return up to five places matching the query.

        Raises:
            LocationNotFoundError: If nothing matches.
            AirDataUnavailableError: If the geocoding service fails.
        """
        key = f"geo:{query.strip().lower()}"
        cached = self._cache.get(key)
        if cached is not None:
            return cached

        payload = await self._fetch(query.strip())
        try:
            places = [Place.model_validate(item) for item in payload.get("results", [])]
        except ValidationError as exc:
            raise AirDataUnavailableError("Geocoding response was invalid") from exc
        if not places:
            raise LocationNotFoundError(query)
        self._cache[key] = places
        return places

    async def _fetch(self, query: str) -> dict[str, Any]:
        params: dict[str, str | int] = {
            "name": query,
            "count": MAX_RESULTS,
            "language": "en",
            "format": "json",
        }
        try:
            response = await self._http.get(
                BASE_URL, params=params, timeout=REQUEST_TIMEOUT_SECONDS
            )
            response.raise_for_status()
            payload: dict[str, Any] = response.json()
        except (httpx.HTTPError, ValueError) as exc:
            raise AirDataUnavailableError("Geocoding request failed") from exc
        return payload
