"""Gemini wrapper: one place for timeouts, model fallback, error mapping and output validation."""

import asyncio
import logging
import re
from collections.abc import Callable, Sequence
from typing import Protocol

from google import genai
from google.genai import types
from pydantic import BaseModel, Field, ValidationError

from app.core.errors import AIUnavailableError

logger = logging.getLogger(__name__)

API_VERSION = "v1beta"
# Per model attempt; with one fallback the worst case stays under the 30 s browser timeout.
REQUEST_TIMEOUT_SECONDS = 10.0
PLAN_TEMPERATURE = 0.4
CHAT_TEMPERATURE = 0.6
PLAN_MAX_TOKENS = 2048
CHAT_MAX_TOKENS = 400
# Rewording needs little reasoning, and thinking tokens would eat the output budget.
# Gemini 2.x takes a token budget (0 = off); Gemini 3.x takes a level instead.
NO_THINKING_V2 = types.ThinkingConfig(thinking_budget=0)
LOW_THINKING_V3 = types.ThinkingConfig(thinking_level="low")

# Markdown that must not appear in plain-text plan fields: (pattern, replacement), applied in order.
_MARKDOWN_RULES: tuple[tuple[re.Pattern[str], str], ...] = (
    (re.compile(r"\*\*|__|`"), ""),  # bold markers and code ticks
    (re.compile(r"(?<!\w)[*_](\S(?:.*?\S)?)[*_](?!\w)"), r"\1"),  # *emphasis* / _emphasis_
    (re.compile(r"^\s*(?:#{1,6}|[*\-•])\s+"), ""),  # leading heading or bullet
)
# Impact-like figures the AI must never produce, e.g. "40%", "2 kg", "50 percent".
_IMPACT_FIGURE = re.compile(r"\d+(?:[.,]\d+)?\s*(?:%|percent|kg|kilo|µg|ug)", re.IGNORECASE)


class AiItemText(BaseModel):
    """AI wording for one recommendation."""

    id: str = Field(max_length=64)
    title: str = Field(min_length=1, max_length=80)
    action: str = Field(min_length=1, max_length=220)
    why: str = Field(min_length=1, max_length=220)


class AiPlanText(BaseModel):
    """AI wording for the whole plan."""

    summary: str = Field(min_length=1, max_length=600)
    items: list[AiItemText] = Field(max_length=20)


class TextGenerator(Protocol):
    """Anything that can generate plan JSON and chat text (real Gemini or a test fake)."""

    async def generate_plan(self, system: str, prompt: str) -> str:
        """Return raw JSON text matching AiPlanText."""
        ...

    async def generate_chat(self, system: str, prompt: str) -> str:
        """Return a plain-text chat reply."""
        ...


def thinking_config_for(model: str) -> types.ThinkingConfig:
    """Return the lightest thinking setting the model family accepts."""
    return NO_THINKING_V2 if model.startswith("gemini-2.") else LOW_THINKING_V3


ConfigFactory = Callable[[str], types.GenerateContentConfig]


class GeminiGenerator:
    """TextGenerator backed by the Gemini API, trying each model in order until one answers.

    A later model is used only when an earlier one fails (quota used up, overloaded,
    retired or timed out), so a free-tier limit on one model doesn't switch the AI off.
    """

    def __init__(self, api_key: str, models: Sequence[str]) -> None:
        """Create a generator.

        Args:
            api_key: Gemini API key.
            models: Model names in order of preference (at least one).

        Raises:
            ValueError: If no model is given.
        """
        if not models:
            raise ValueError("At least one Gemini model is required")
        # System instructions and JSON schemas need the v1beta API (v1 rejects them).
        self._client = genai.Client(
            api_key=api_key, http_options=types.HttpOptions(api_version=API_VERSION)
        )
        self._models = tuple(models)

    async def generate_plan(self, system: str, prompt: str) -> str:
        """Generate structured plan JSON."""

        def config(model: str) -> types.GenerateContentConfig:
            return types.GenerateContentConfig(
                system_instruction=system,
                temperature=PLAN_TEMPERATURE,
                max_output_tokens=PLAN_MAX_TOKENS,
                response_mime_type="application/json",
                response_schema=AiPlanText,
                thinking_config=thinking_config_for(model),
            )

        return await self._generate(prompt, config)

    async def generate_chat(self, system: str, prompt: str) -> str:
        """Generate a short chat reply."""

        def config(model: str) -> types.GenerateContentConfig:
            return types.GenerateContentConfig(
                system_instruction=system,
                temperature=CHAT_TEMPERATURE,
                max_output_tokens=CHAT_MAX_TOKENS,
                thinking_config=thinking_config_for(model),
            )

        return await self._generate(prompt, config)

    async def _generate(self, prompt: str, config_for: ConfigFactory) -> str:
        last_error: Exception | None = None
        for model in self._models:
            try:
                response = await asyncio.wait_for(
                    self._client.aio.models.generate_content(
                        model=model, contents=prompt, config=config_for(model)
                    ),
                    timeout=REQUEST_TIMEOUT_SECONDS,
                )
            except Exception as exc:  # SDK raises many error types; all mean "try the next one"
                logger.warning("Gemini model %s failed: %s", model, type(exc).__name__)
                last_error = exc
                continue
            if response.text:
                return response.text
            logger.warning("Gemini model %s returned an empty response", model)
        raise AIUnavailableError("All Gemini models failed") from last_error


def contains_impact_figure(text: str) -> bool:
    """Return True if text contains a percentage or weight the AI is not allowed to state."""
    return bool(_IMPACT_FIGURE.search(text))


def strip_markdown(text: str) -> str:
    """Remove Markdown formatting and collapse whitespace for plain-text fields."""
    for pattern, replacement in _MARKDOWN_RULES:
        text = pattern.sub(replacement, text)
    return " ".join(text.split())


def _plain_item(item: AiItemText) -> AiItemText:
    return AiItemText(
        id=item.id,
        title=strip_markdown(item.title),
        action=strip_markdown(item.action),
        why=strip_markdown(item.why),
    )


def parse_plan_text(raw: str, allowed_ids: set[str]) -> AiPlanText:
    """Validate AI plan JSON and apply guardrails.

    Unknown ids are dropped. Output containing impact figures is rejected.

    Raises:
        AIUnavailableError: If the output is invalid or breaks a guardrail.
    """
    try:
        parsed = AiPlanText.model_validate_json(raw)
    except ValidationError as exc:
        raise AIUnavailableError("Gemini output did not match the schema") from exc

    items = [_plain_item(item) for item in parsed.items if item.id in allowed_ids]
    summary = strip_markdown(parsed.summary)
    texts = [parsed.summary, *(f"{i.title} {i.action} {i.why}" for i in items)]
    if any(contains_impact_figure(text) for text in texts):
        raise AIUnavailableError("Gemini output contained impact figures")
    return AiPlanText(summary=summary, items=items)
