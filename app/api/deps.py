"""Service container and the dependency that exposes it to routes."""

from dataclasses import dataclass

from cachetools import TTLCache
from fastapi import Request
from httpx import AsyncClient

from app.config import Settings
from app.services.air_quality import AirQualityClient
from app.services.chat import ChatService
from app.services.gemini import GeminiGenerator, TextGenerator
from app.services.geocoding import GeocodingClient
from app.services.plan_builder import PlanBuilder

AIR_CACHE_SIZE = 512
GEO_CACHE_SIZE = 1024
GEO_CACHE_TTL_SECONDS = 24 * 3600


@dataclass(frozen=True)
class Services:
    """Everything the routes depend on. Swapped for fakes in tests."""

    air: AirQualityClient
    geocoder: GeocodingClient
    plans: PlanBuilder
    chat: ChatService


def build_services(settings: Settings, http: AsyncClient) -> Services:
    """Wire real services from settings and a shared HTTP client."""
    generator: TextGenerator | None = None
    if settings.has_gemini_key and settings.gemini_api_key is not None:
        generator = GeminiGenerator(
            settings.gemini_api_key.get_secret_value(), settings.gemini_model
        )

    air = AirQualityClient(http, TTLCache(maxsize=AIR_CACHE_SIZE, ttl=settings.cache_ttl_seconds))
    return Services(
        air=air,
        geocoder=GeocodingClient(http, TTLCache(maxsize=GEO_CACHE_SIZE, ttl=GEO_CACHE_TTL_SECONDS)),
        plans=PlanBuilder(air, generator),
        chat=ChatService(generator),
    )


def get_services(request: Request) -> Services:
    """FastAPI dependency returning the app's services."""
    services: Services = request.app.state.services
    return services
