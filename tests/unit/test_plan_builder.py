from pydantic import SecretStr

from app.api.deps import build_services
from app.config import Settings
from app.rules.recommendations import select_recommendations
from app.services.gemini import AiItemText, AiPlanText, GeminiGenerator
from app.services.plan_builder import (
    DEFAULT_LOCATION_NAME,
    ai_payload,
    location_name,
    merge_ai_text,
    rules_summary,
)
from tests.factories import make_context, make_profile


def test_merge_replaces_text_but_keeps_numbers() -> None:
    recs = select_recommendations(make_context(aqi=287, commute_mode="car", commute_km=10))
    target = recs[0]
    ai = AiPlanText(
        summary="s",
        items=[AiItemText(id=target.id, title="New title", action="New action", why="New why")],
    )
    merged = merge_ai_text(recs, ai)
    assert merged[0].title == "New title"
    assert merged[0].impact == target.impact
    assert merged[0].priority == target.priority
    assert merged[1:] == recs[1:]


def test_rules_summary_with_and_without_recommendations() -> None:
    ctx = make_context(aqi=287)
    recs = select_recommendations(ctx)
    assert "Very Unhealthy" in rules_summary(ctx, recs)
    assert recs[0].title in rules_summary(ctx, recs)
    assert "No special precautions" in rules_summary(make_context(aqi=20), [])


def test_location_name_default() -> None:
    assert location_name(make_profile(location_name="")) == DEFAULT_LOCATION_NAME


def test_ai_payload_excludes_numbers_and_identity() -> None:
    ctx = make_context(aqi=287, household={"children": True})
    payload = ai_payload(ctx, select_recommendations(ctx))
    assert "latitude" not in str(payload)
    assert all(
        set(item) == {"id", "category", "default_title", "default_action", "default_why"}
        for item in payload["items"]
    )
    assert payload["household"]["children"] is True


async def test_ai_wording_is_cached_for_identical_requests() -> None:
    import httpx
    import respx
    from cachetools import TTLCache

    from app.models.plan import PlanSource
    from app.services import air_quality
    from app.services.air_quality import AirQualityClient
    from app.services.plan_builder import PlanBuilder
    from tests.factories import NOW
    from tests.payloads import FakeGenerator, air_payload

    generator = FakeGenerator()
    with respx.mock:
        respx.get(air_quality.BASE_URL).mock(return_value=httpx.Response(200, json=air_payload()))
        async with httpx.AsyncClient() as http:
            builder = PlanBuilder(
                AirQualityClient(http, TTLCache(maxsize=4, ttl=60)),
                generator,
                clock=lambda _tz: NOW,
                ai_cache=TTLCache(maxsize=4, ttl=60),
            )
            profile = make_profile(household={"children": True})
            first = await builder.build(profile)
            second = await builder.build(profile)
    assert first.source is second.source is PlanSource.AI
    assert first.summary == second.summary
    assert len(generator.plan_prompts) == 1


async def test_build_services_wires_gemini_only_with_key() -> None:
    import httpx

    async with httpx.AsyncClient() as http:
        without = build_services(Settings(gemini_api_key=None), http)
        with_key = build_services(Settings(gemini_api_key=SecretStr("abc")), http)
    assert without.chat._generator is None
    assert isinstance(with_key.chat._generator, GeminiGenerator)
