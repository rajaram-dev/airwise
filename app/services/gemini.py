"""Gemini wrapper: one place for timeouts, error mapping and output validation."""

import asyncio
import re
from typing import Protocol

from google import genai
from google.genai import types
from pydantic import BaseModel, Field, ValidationError

from app.core.errors import AIUnavailableError

REQUEST_TIMEOUT_SECONDS = 15.0
PLAN_TEMPERATURE = 0.4
CHAT_TEMPERATURE = 0.6
PLAN_MAX_TOKENS = 1024
CHAT_MAX_TOKENS = 400

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


class GeminiGenerator:
    """TextGenerator backed by the Gemini API."""

    def __init__(self, api_key: str, model: str) -> None:
        """Create a generator for the given model."""
        self._client = genai.Client(api_key=api_key)
        self._model = model

    async def generate_plan(self, system: str, prompt: str) -> str:
        """Generate structured plan JSON."""
        config = types.GenerateContentConfig(
            system_instruction=system,
            temperature=PLAN_TEMPERATURE,
            max_output_tokens=PLAN_MAX_TOKENS,
            response_mime_type="application/json",
            response_schema=AiPlanText,
        )
        return await self._generate(prompt, config)

    async def generate_chat(self, system: str, prompt: str) -> str:
        """Generate a short chat reply."""
        config = types.GenerateContentConfig(
            system_instruction=system,
            temperature=CHAT_TEMPERATURE,
            max_output_tokens=CHAT_MAX_TOKENS,
        )
        return await self._generate(prompt, config)

    async def _generate(self, prompt: str, config: types.GenerateContentConfig) -> str:
        try:
            response = await asyncio.wait_for(
                self._client.aio.models.generate_content(
                    model=self._model, contents=prompt, config=config
                ),
                timeout=REQUEST_TIMEOUT_SECONDS,
            )
        except Exception as exc:  # SDK raises many error types; all mean "AI unavailable"
            raise AIUnavailableError("Gemini request failed") from exc
        if not response.text:
            raise AIUnavailableError("Gemini returned an empty response")
        return response.text


def contains_impact_figure(text: str) -> bool:
    """Return True if text contains a percentage or weight the AI is not allowed to state."""
    return bool(_IMPACT_FIGURE.search(text))


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

    items = [item for item in parsed.items if item.id in allowed_ids]
    texts = [parsed.summary, *(f"{i.title} {i.action} {i.why}" for i in items)]
    if any(contains_impact_figure(text) for text in texts):
        raise AIUnavailableError("Gemini output contained impact figures")
    return AiPlanText(summary=parsed.summary, items=items)
