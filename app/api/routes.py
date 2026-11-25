"""HTTP routes for /api/v1. Contracts are documented in docs/api.md."""

from typing import Annotated

from fastapi import APIRouter, Depends, Query, Request
from pydantic import BaseModel

from app import __version__
from app.api.deps import Services, get_services
from app.config import get_settings
from app.core.security import GENERAL_RATE_LIMIT, limiter
from app.models.air import AirData
from app.models.chat import ChatRequest, ChatResponse
from app.models.plan import Plan
from app.models.profile import UserProfile
from app.services.geocoding import Place

router = APIRouter()
ServicesDep = Annotated[Services, Depends(get_services)]


class HealthResponse(BaseModel):
    """Liveness response."""

    status: str
    version: str


class GeocodeResponse(BaseModel):
    """Location search results."""

    results: list[Place]


def _plan_limit() -> str:
    return get_settings().rate_limit_plan


def _chat_limit() -> str:
    return get_settings().rate_limit_chat


@router.get("/health", tags=["system"])
async def health() -> HealthResponse:
    """Liveness check used by the host."""
    return HealthResponse(status="ok", version=__version__)


@router.get("/geocode", tags=["location"])
@limiter.limit(GENERAL_RATE_LIMIT)
async def geocode(
    request: Request,
    services: ServicesDep,
    q: Annotated[str, Query(min_length=2, max_length=100)],
) -> GeocodeResponse:
    """Search places by name."""
    return GeocodeResponse(results=await services.geocoder.search(q))


@router.get("/reverse-geocode", tags=["location"])
@limiter.limit(GENERAL_RATE_LIMIT)
async def reverse_geocode(
    request: Request,
    services: ServicesDep,
    lat: Annotated[float, Query(ge=-90, le=90)],
    lon: Annotated[float, Query(ge=-180, le=180)],
) -> Place:
    """Name of the town or city at a coordinate (rounded to about 1 km)."""
    return await services.reverse_geocoder.lookup(lat, lon)


@router.get("/air", tags=["air"])
@limiter.limit(GENERAL_RATE_LIMIT)
async def air(
    request: Request,
    services: ServicesDep,
    lat: Annotated[float, Query(ge=-90, le=90)],
    lon: Annotated[float, Query(ge=-180, le=180)],
) -> AirData:
    """Current air quality and 24-hour forecast for a coordinate."""
    return await services.air.get_air_data(lat, lon)


@router.post("/plan", tags=["plan"])
@limiter.limit(_plan_limit)
async def plan(request: Request, services: ServicesDep, profile: UserProfile) -> Plan:
    """Build a personalised plan from the user's profile."""
    return await services.plans.build(profile)


@router.post("/chat", tags=["chat"])
@limiter.limit(_chat_limit)
async def chat(request: Request, services: ServicesDep, body: ChatRequest) -> ChatResponse:
    """Answer a follow-up question about the plan."""
    return await services.chat.reply(body)
