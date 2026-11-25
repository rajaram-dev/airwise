from typing import Any

import httpx
import pytest
import respx
from cachetools import TTLCache

from app.core.errors import AirDataUnavailableError
from app.models.air import AirData, AqiCategory
from app.services.air_quality import BASE_URL, AirQualityClient, cache_key, parse_air_response


def sample_payload() -> dict[str, Any]:
    return {
        "timezone": "Asia/Kolkata",
        "utc_offset_seconds": 19800,
        "current": {
            "time": "2026-11-25T09:00",
            "us_aqi": 287,
            "pm2_5": 212.4,
            "pm10": 340.1,
            "nitrogen_dioxide": 60.2,
            "ozone": 20.0,
            "us_aqi_pm2_5": 287,
            "us_aqi_pm10": 190,
            "us_aqi_nitrogen_dioxide": 40,
            "us_aqi_ozone": 15,
        },
        "hourly": {
            "time": ["2026-11-25T09:00", "2026-11-25T10:00", "2026-11-25T11:00"],
            "us_aqi": [287, None, 250],
            "pm2_5": [212.4, 200.0, 180.0],
        },
    }


def make_client() -> tuple[AirQualityClient, httpx.AsyncClient]:
    http = httpx.AsyncClient()
    return AirQualityClient(http, TTLCache(maxsize=16, ttl=600)), http


def test_parse_air_response() -> None:
    data = parse_air_response(sample_payload())
    assert data.current.aqi == 287
    assert data.current.category is AqiCategory.VERY_UNHEALTHY
    assert data.current.category_label == "Very Unhealthy"
    assert data.current.dominant_pollutant == "pm2_5"
    assert data.current.observed_at.utcoffset() is not None
    assert data.timezone == "Asia/Kolkata"
    assert len(data.forecast) == 2  # hour with missing AQI skipped


def test_dominant_pollutant_defaults_when_sub_indices_missing() -> None:
    payload = sample_payload()
    for key in ("us_aqi_pm2_5", "us_aqi_pm10", "us_aqi_nitrogen_dioxide", "us_aqi_ozone"):
        payload["current"].pop(key)
    assert parse_air_response(payload).current.dominant_pollutant == "pm2_5"


@pytest.mark.parametrize("broken", [{"current": {}}, {"current": {"us_aqi": "bad"}}, {}])
def test_parse_rejects_incomplete_payload(broken: dict[str, Any]) -> None:
    with pytest.raises(AirDataUnavailableError):
        parse_air_response(broken)


def test_cache_key_rounds_coordinates() -> None:
    assert cache_key(28.61394, 77.20902) == "aq:28.61:77.21"


@respx.mock
async def test_get_air_data_fetches_and_caches() -> None:
    route = respx.get(BASE_URL).mock(return_value=httpx.Response(200, json=sample_payload()))
    client, http = make_client()
    async with http:
        first = await client.get_air_data(28.61394, 77.20902)
        second = await client.get_air_data(28.6141, 77.2091)

    assert isinstance(first, AirData)
    assert first == second
    assert route.call_count == 1
    sent = route.calls[0].request.url.params
    assert sent["latitude"] == "28.61"
    assert sent["timezone"] == "auto"


@respx.mock
async def test_get_air_data_raises_on_server_error() -> None:
    respx.get(BASE_URL).mock(return_value=httpx.Response(500))
    client, http = make_client()
    async with http:
        with pytest.raises(AirDataUnavailableError):
            await client.get_air_data(28.61, 77.21)


@respx.mock
async def test_get_air_data_raises_on_timeout() -> None:
    respx.get(BASE_URL).mock(side_effect=httpx.ConnectTimeout("timeout"))
    client, http = make_client()
    async with http:
        with pytest.raises(AirDataUnavailableError):
            await client.get_air_data(28.61, 77.21)
