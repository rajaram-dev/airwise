from collections.abc import Callable, Iterator
from datetime import datetime, tzinfo

import httpx
import pytest
import respx
from cachetools import TTLCache
from fastapi.testclient import TestClient

from app.api.deps import Services
from app.config import Settings
from app.core.security import limiter
from app.main import create_app
from app.services import air_quality, geocoding
from app.services.air_quality import AirQualityClient
from app.services.chat import ChatService
from app.services.gemini import TextGenerator
from app.services.geocoding import GeocodingClient
from app.services.plan_builder import PlanBuilder
from tests.factories import NOW
from tests.payloads import GEOCODE_PAYLOAD, air_payload

ClientFactory = Callable[..., TestClient]


def fixed_clock(_: tzinfo | None) -> datetime:
    return NOW


@pytest.fixture(autouse=True)
def reset_rate_limits() -> None:
    limiter.reset()


@pytest.fixture
def upstream() -> Iterator[respx.MockRouter]:
    """Mock Open-Meteo with healthy default responses."""
    with respx.mock(assert_all_called=False) as router:
        router.get(air_quality.BASE_URL, name="air").mock(
            return_value=httpx.Response(200, json=air_payload())
        )
        router.get(geocoding.BASE_URL, name="geo").mock(
            return_value=httpx.Response(200, json=GEOCODE_PAYLOAD)
        )
        yield router


@pytest.fixture
def make_client(upstream: respx.MockRouter) -> Iterator[ClientFactory]:
    """Build a TestClient wired to mocked upstreams and an optional fake AI."""
    clients: list[TestClient] = []
    http = httpx.AsyncClient()

    def factory(generator: TextGenerator | None = None) -> TestClient:
        air = AirQualityClient(http, TTLCache(maxsize=8, ttl=600))
        services = Services(
            air=air,
            geocoder=GeocodingClient(http, TTLCache(maxsize=8, ttl=600)),
            plans=PlanBuilder(air, generator, clock=fixed_clock),
            chat=ChatService(generator),
        )
        app = create_app(Settings(gemini_api_key=None), services=services)
        client = TestClient(app, raise_server_exceptions=False)
        client.__enter__()
        clients.append(client)
        return client

    yield factory
    for client in clients:
        client.__exit__(None, None, None)
