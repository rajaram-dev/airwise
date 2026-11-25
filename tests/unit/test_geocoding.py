import httpx
import pytest
import respx
from cachetools import TTLCache

from app.core.errors import AirDataUnavailableError, LocationNotFoundError
from app.services.geocoding import BASE_URL, GeocodingClient
from tests.payloads import GEOCODE_PAYLOAD


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
