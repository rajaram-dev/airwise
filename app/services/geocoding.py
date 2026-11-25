"""Geocoding: Open-Meteo for name search, OpenStreetMap Nominatim for reverse lookups."""

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


REVERSE_URL = "https://nominatim.openstreetmap.org/reverse"
REVERSE_ZOOM = 10  # city / town level
COORD_PRECISION = 2  # ~1 km: precise locations never leave the server
# Most specific populated-place field first.
PLACE_FIELDS = ("city", "town", "village", "suburb", "municipality", "county", "state_district")


def parse_reverse(payload: dict[str, Any], latitude: float, longitude: float) -> Place | None:
    """Turn a Nominatim reverse response into a Place, or None if it has no usable name."""
    address = payload.get("address")
    if not isinstance(address, dict):
        return None
    name = next((address[f] for f in PLACE_FIELDS if isinstance(address.get(f), str)), None)
    name = name or address.get("state")
    if not isinstance(name, str) or not name.strip():
        return None
    return Place(
        name=name.strip()[:100],
        admin1=str(address.get("state", ""))[:100],
        country=str(address.get("country", ""))[:100],
        latitude=latitude,
        longitude=longitude,
    )


class ReverseGeocodingClient:
    """Turns rounded coordinates into a place name using OpenStreetMap Nominatim."""

    def __init__(self, http: httpx.AsyncClient, cache: TTLCache[str, Place]) -> None:
        """Create a client with a shared HTTP client and a TTL cache."""
        self._http = http
        self._cache = cache

    async def lookup(self, latitude: float, longitude: float) -> Place:
        """Return the town or city at the coordinates.

        Raises:
            LocationNotFoundError: If no named place is found.
            AirDataUnavailableError: If the service fails.
        """
        lat, lon = round(latitude, COORD_PRECISION), round(longitude, COORD_PRECISION)
        key = f"rev:{lat:.2f}:{lon:.2f}"
        cached = self._cache.get(key)
        if cached is not None:
            return cached

        params: dict[str, str | float | int] = {
            "format": "jsonv2",
            "lat": lat,
            "lon": lon,
            "zoom": REVERSE_ZOOM,
            "accept-language": "en",
        }
        try:
            response = await self._http.get(
                REVERSE_URL, params=params, timeout=REQUEST_TIMEOUT_SECONDS
            )
            response.raise_for_status()
            payload: dict[str, Any] = response.json()
        except (httpx.HTTPError, ValueError) as exc:
            raise AirDataUnavailableError("Reverse geocoding request failed") from exc

        place = parse_reverse(payload, lat, lon)
        if place is None:
            raise LocationNotFoundError(key)
        self._cache[key] = place
        return place
