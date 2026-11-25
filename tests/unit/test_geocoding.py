import httpx
import pytest
import respx
from cachetools import TTLCache

from app.core.errors import AirDataUnavailableError, LocationNotFoundError
from app.services.geocoding import (
    BASE_URL,
    REVERSE_URL,
    GeocodingClient,
    ReverseGeocodingClient,
    parse_reverse,
)
from tests.payloads import GEOCODE_PAYLOAD, REVERSE_PAYLOAD


@respx.mock
async def test_search_returns_and_caches_places() -> None:
    route = respx.get(BASE_URL).mock(return_value=httpx.Response(200, json=GEOCODE_PAYLOAD))
    async with httpx.AsyncClient() as http:
        client = GeocodingClient(http, TTLCache(maxsize=4, ttl=60))
        first = await client.search("Delhi")
        second = await client.search("  delhi ")
    assert first[0].latitude == 28.65
    assert first == second
    assert route.call_count == 1


@respx.mock
async def test_search_no_results() -> None:
    respx.get(BASE_URL).mock(return_value=httpx.Response(200, json={}))
    async with httpx.AsyncClient() as http:
        with pytest.raises(LocationNotFoundError):
            await GeocodingClient(http, TTLCache(maxsize=4, ttl=60)).search("zzz")


@respx.mock
async def test_search_invalid_payload() -> None:
    respx.get(BASE_URL).mock(return_value=httpx.Response(200, json={"results": [{"name": "x"}]}))
    async with httpx.AsyncClient() as http:
        with pytest.raises(AirDataUnavailableError):
            await GeocodingClient(http, TTLCache(maxsize=4, ttl=60)).search("x")


@respx.mock
async def test_search_upstream_error() -> None:
    respx.get(BASE_URL).mock(return_value=httpx.Response(502))
    async with httpx.AsyncClient() as http:
        with pytest.raises(AirDataUnavailableError):
            await GeocodingClient(http, TTLCache(maxsize=4, ttl=60)).search("Delhi")


# ---------- reverse geocoding ----------


@pytest.mark.parametrize(
    ("address", "expected"),
    [
        ({"city": "Lucknow", "state": "Uttar Pradesh", "country": "India"}, "Lucknow"),
        ({"town": "Sonipat", "state": "Haryana"}, "Sonipat"),
        ({"village": "Rampur"}, "Rampur"),
        ({"state": "Goa", "country": "India"}, "Goa"),
    ],
)
def test_parse_reverse_picks_most_specific_name(address: dict[str, str], expected: str) -> None:
    place = parse_reverse({"address": address}, 1.0, 2.0)
    assert place is not None
    assert place.name == expected


@pytest.mark.parametrize("payload", [{}, {"address": "x"}, {"address": {"country": "India"}}])
def test_parse_reverse_without_name(payload: dict[str, object]) -> None:
    assert parse_reverse(payload, 1.0, 2.0) is None


@respx.mock
async def test_reverse_lookup_rounds_coordinates_and_caches() -> None:
    route = respx.get(REVERSE_URL).mock(return_value=httpx.Response(200, json=REVERSE_PAYLOAD))
    async with httpx.AsyncClient() as http:
        client = ReverseGeocodingClient(http, TTLCache(maxsize=4, ttl=60))
        first = await client.lookup(26.846694, 80.946166)
        second = await client.lookup(26.8471, 80.9459)
    assert first.name == "Lucknow"
    assert first == second
    assert route.call_count == 1
    params = route.calls[0].request.url.params
    assert (params["lat"], params["lon"]) == ("26.85", "80.95")


@respx.mock
async def test_reverse_lookup_errors() -> None:
    respx.get(REVERSE_URL).mock(
        return_value=httpx.Response(200, json={"error": "Unable to geocode"})
    )
    async with httpx.AsyncClient() as http:
        client = ReverseGeocodingClient(http, TTLCache(maxsize=4, ttl=60))
        with pytest.raises(LocationNotFoundError):
            await client.lookup(0.0, 0.0)
    respx.get(REVERSE_URL).mock(return_value=httpx.Response(503))
    async with httpx.AsyncClient() as http:
        client = ReverseGeocodingClient(http, TTLCache(maxsize=4, ttl=60))
        with pytest.raises(AirDataUnavailableError):
            await client.lookup(1.0, 1.0)
