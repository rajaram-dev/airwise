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


async def test_build_services_wires_gemini_only_with_key() -> None:
    import httpx

    async with httpx.AsyncClient() as http:
        without = build_services(Settings(gemini_api_key=None), http)
        with_key = build_services(Settings(gemini_api_key=SecretStr("abc")), http)
    assert without.chat._generator is None
    assert isinstance(with_key.chat._generator, GeminiGenerator)
