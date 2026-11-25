"""Orchestrates a plan: air data -> rules engine -> AI wording -> merged plan."""

import logging
from collections.abc import Callable
from datetime import datetime, tzinfo
from typing import Any

from app.core.errors import AIUnavailableError
from app.models.plan import Location, Plan, PlanSource, Recommendation
from app.models.profile import UserProfile
from app.rules.context import RuleContext, build_context, format_window
from app.rules.recommendations import select_recommendations
from app.services.air_quality import AirQualityClient
from app.services.gemini import AiPlanText, TextGenerator, parse_plan_text
from app.services.prompts import PLAN_SYSTEM_PROMPT_V1, build_plan_prompt

logger = logging.getLogger(__name__)

DISCLAIMER = (
    "General guidance, not medical advice. If you or a family member have symptoms, "
    "please see a doctor."
)
DEFAULT_LOCATION_NAME = "your area"

Clock = Callable[[tzinfo | None], datetime]


def _system_clock(tz: tzinfo | None) -> datetime:
    return datetime.now(tz)


class PlanBuilder:
    """Builds a personalised plan for a user profile."""

    def __init__(
        self,
        air: AirQualityClient,
        generator: TextGenerator | None,
        clock: Clock = _system_clock,
    ) -> None:
        """Create a builder.

        Args:
            air: Air quality client.
            generator: AI text generator, or None to always use rule-based wording.
            clock: Returns the current time in a timezone (injectable for tests).
        """
        self._air = air
        self._generator = generator
        self._clock = clock

    async def build(self, profile: UserProfile) -> Plan:
        """Return the plan. AI failures fall back to rule-based wording.

        Raises:
            AirDataUnavailableError: If air data cannot be fetched.
        """
        data = await self._air.get_air_data(profile.latitude, profile.longitude)
        now = self._clock(data.current.observed_at.tzinfo)
        ctx = build_context(profile, data.current, data.forecast, now)
        recommendations = select_recommendations(ctx)
        summary = rules_summary(ctx, recommendations)
        source = PlanSource.RULES

        if self._generator is not None and recommendations:
            try:
                ai_text = await self._ai_text(self._generator, ctx, recommendations)
            except AIUnavailableError as exc:
                logger.warning("AI wording unavailable, using rules: %s", exc)
            else:
                recommendations = merge_ai_text(recommendations, ai_text)
                summary = ai_text.summary
                source = PlanSource.AI

        return Plan(
            location=Location(
                name=location_name(profile),
                latitude=round(profile.latitude, 2),
                longitude=round(profile.longitude, 2),
            ),
            air=data.current,
            risk=ctx.risk,
            best_windows=ctx.windows,
            recommendations=recommendations,
            summary=summary,
            source=source,
            disclaimer=DISCLAIMER,
            generated_at=now,
        )

    @staticmethod
    async def _ai_text(
        generator: TextGenerator, ctx: RuleContext, recs: list[Recommendation]
    ) -> AiPlanText:
        prompt = build_plan_prompt(ai_payload(ctx, recs))
        raw = await generator.generate_plan(PLAN_SYSTEM_PROMPT_V1, prompt)
        return parse_plan_text(raw, {rec.id for rec in recs})


def location_name(profile: UserProfile) -> str:
    """Return the display name for the user's location."""
    return profile.location_name or DEFAULT_LOCATION_NAME


def rules_summary(ctx: RuleContext, recs: list[Recommendation]) -> str:
    """Return a plain summary used when AI wording is unavailable."""
    first = (
        f"Air in {location_name(ctx.profile)} is {ctx.air.category_label} today "
        f"(AQI {ctx.air.aqi})."
    )
    if not recs:
        return f"{first} No special precautions are needed. Enjoy your day."
    return f"{first} Most important for you: {recs[0].title}."


def ai_payload(ctx: RuleContext, recs: list[Recommendation]) -> dict[str, Any]:
    """Build the compact input sent to Gemini.

    Impact numbers are deliberately left out so the AI cannot restate or alter them.
    """
    household = ctx.profile.household
    return {
        "location": location_name(ctx.profile),
        "air": {
            "aqi": ctx.air.aqi,
            "category": ctx.air.category_label,
            "dominant_pollutant": ctx.air.dominant_pollutant,
        },
        "risk": {"level": ctx.risk.level.value, "reasons": ctx.risk.reasons},
        "best_outdoor_windows": [format_window(w) for w in ctx.windows],
        "household": {
            "children": household.children,
            "elderly": household.elderly,
            "respiratory_condition": household.respiratory_condition,
            "pregnant": household.pregnant,
        },
        "lifestyle": {
            "commute_mode": ctx.profile.commute_mode.value,
            "cooking_fuel": ctx.profile.cooking_fuel.value,
            "heating": ctx.profile.heating.value,
            "has_air_purifier": ctx.profile.has_air_purifier,
            "outdoor_activity": ctx.profile.outdoor_activity.value,
        },
        "items": [
            {
                "id": rec.id,
                "category": rec.category.value,
                "default_title": rec.title,
                "default_action": rec.action,
                "default_why": rec.why,
            }
            for rec in recs
        ],
        "language": ctx.profile.language.value,
    }


def merge_ai_text(recs: list[Recommendation], ai_text: AiPlanText) -> list[Recommendation]:
    """Replace wording by id. Impact numbers, category and priority always stay from the rules."""
    by_id = {item.id: item for item in ai_text.items}
    merged = []
    for rec in recs:
        item = by_id.get(rec.id)
        if item is None:
            merged.append(rec)
        else:
            merged.append(
                rec.model_copy(update={"title": item.title, "action": item.action, "why": item.why})
            )
    return merged
