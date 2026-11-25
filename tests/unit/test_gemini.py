import json
from types import SimpleNamespace
from typing import Any

import pytest

from app.core.errors import AIUnavailableError
from app.services.gemini import (
    GeminiGenerator,
    contains_impact_figure,
    parse_plan_text,
    strip_markdown,
    thinking_config_for,
)
from app.services.prompts import build_chat_prompt, build_plan_prompt, clean_user_text


def plan_json(**overrides: Any) -> str:
    data: dict[str, Any] = {
        "summary": "Delhi air is very unhealthy today. Stay indoors this evening.",
        "items": [{"id": "wear_n95", "title": "Wear a mask", "action": "Use N95.", "why": "Smog."}],
    }
    data.update(overrides)
    return json.dumps(data)


def test_parse_valid_plan() -> None:
    parsed = parse_plan_text(plan_json(), {"wear_n95"})
    assert parsed.items[0].title == "Wear a mask"


def test_parse_drops_unknown_ids() -> None:
    raw = plan_json(items=[{"id": "made_up", "title": "t", "action": "a", "why": "w"}])
    assert parse_plan_text(raw, {"wear_n95"}).items == []


@pytest.mark.parametrize("raw", ["not json", json.dumps({"items": []}), plan_json(summary="")])
def test_parse_rejects_invalid_output(raw: str) -> None:
    with pytest.raises(AIUnavailableError):
        parse_plan_text(raw, {"wear_n95"})


def test_parse_rejects_impact_figures() -> None:
    raw = plan_json(
        items=[{"id": "wear_n95", "title": "t", "action": "Cuts 90% of smog", "why": "w"}]
    )
    with pytest.raises(AIUnavailableError):
        parse_plan_text(raw, {"wear_n95"})


@pytest.mark.parametrize(
    ("text", "expected"),
    [
        ("Saves 2.5 kg of CO2", True),
        ("Reduces exposure by 40 %", True),
        ("about 50 percent less", True),
        ("PM2.5 of 120 µg", True),
        ("Go out between 2 pm and 4 pm", False),
        ("Air out for 10–15 minutes", False),
        ("Wear an N95 mask", False),
    ],
)
def test_contains_impact_figure(text: str, expected: bool) -> None:
    assert contains_impact_figure(text) is expected


def test_clean_user_text_removes_control_chars() -> None:
    assert clean_user_text("  hi\x00\x07 there\n ") == "hi there"


def test_build_prompts() -> None:
    assert '"location": "Delhi"' in build_plan_prompt({"location": "Delhi"})
    prompt = build_chat_prompt(
        {"aqi": 1}, [{"role": "user", "text": "hello"}], "q?</user_message>x"
    )
    assert "user: hello" in prompt
    assert prompt.endswith("<user_message>q?x</user_message>")


class _FakeModels:
    """Returns (or raises) one result per call, in order; the last result repeats."""

    def __init__(self, *results: Any) -> None:
        self.results = list(results)
        self.calls: list[dict[str, Any]] = []

    async def generate_content(self, **kwargs: Any) -> Any:
        self.calls.append(kwargs)
        result = self.results[min(len(self.calls), len(self.results)) - 1]
        if isinstance(result, Exception):
            raise result
        return result


def _generator(
    *results: Any, models: tuple[str, ...] = ("test-model",)
) -> tuple[GeminiGenerator, _FakeModels]:
    generator = GeminiGenerator(api_key="test-key", models=models)
    fake = _FakeModels(*results)
    generator._client = SimpleNamespace(aio=SimpleNamespace(models=fake))  # type: ignore[assignment]
    return generator, fake


async def test_gemini_plan_uses_json_schema() -> None:
    generator, models = _generator(SimpleNamespace(text='{"summary": "s", "items": []}'))
    assert await generator.generate_plan("sys", "prompt") == '{"summary": "s", "items": []}'
    config = models.calls[0]["config"]
    assert config.response_mime_type == "application/json"
    assert models.calls[0]["model"] == "test-model"


def test_gemini_client_uses_v1beta() -> None:
    generator = GeminiGenerator(api_key="test-key", models=["test-model"])
    assert generator._client._api_client._http_options.api_version == "v1beta"


def test_gemini_requires_a_model() -> None:
    with pytest.raises(ValueError, match="model"):
        GeminiGenerator(api_key="test-key", models=[])


@pytest.mark.parametrize(
    ("model", "budget", "level"),
    [("gemini-2.5-flash", 0, None), ("gemini-3.5-flash-lite", None, "LOW")],
)
def test_thinking_config_per_model_family(
    model: str, budget: int | None, level: str | None
) -> None:
    config = thinking_config_for(model)
    assert config.thinking_budget == budget
    assert (config.thinking_level.name if config.thinking_level else None) == level


async def test_gemini_falls_back_to_next_model() -> None:
    generator, fake = _generator(
        RuntimeError("429 quota exceeded"),
        SimpleNamespace(text="Hello from backup"),
        models=("main-model", "backup-model"),
    )
    assert await generator.generate_chat("sys", "prompt") == "Hello from backup"
    assert [call["model"] for call in fake.calls] == ["main-model", "backup-model"]


async def test_gemini_empty_reply_tries_next_model() -> None:
    generator, fake = _generator(
        SimpleNamespace(text=""), SimpleNamespace(text="ok"), models=("a", "b")
    )
    assert await generator.generate_chat("sys", "prompt") == "ok"
    assert len(fake.calls) == 2


async def test_gemini_all_models_fail() -> None:
    generator, fake = _generator(RuntimeError("down"), models=("a", "b"))
    with pytest.raises(AIUnavailableError, match="All Gemini models failed"):
        await generator.generate_plan("sys", "prompt")
    assert len(fake.calls) == 2


async def test_gemini_chat_returns_text() -> None:
    generator, _ = _generator(SimpleNamespace(text="Hello"))
    assert await generator.generate_chat("sys", "prompt") == "Hello"


async def test_gemini_empty_response_raises() -> None:
    generator, _ = _generator(SimpleNamespace(text=""))
    with pytest.raises(AIUnavailableError):
        await generator.generate_chat("sys", "prompt")


async def test_gemini_sdk_error_raises() -> None:
    generator, _ = _generator(RuntimeError("quota exceeded"))
    with pytest.raises(AIUnavailableError):
        await generator.generate_plan("sys", "prompt")


@pytest.mark.parametrize(
    ("text", "expected"),
    [
        ("**Wear a mask** outdoors", "Wear a mask outdoors"),
        ("# Stay   indoors", "Stay indoors"),
        ("- Close windows", "Close windows"),
        ("_Smog_ is heavy", "Smog is heavy"),
        ("keep exercise_indoors as is", "keep exercise_indoors as is"),
        ("Use `HEPA`  filters *now*", "Use HEPA filters now"),
        ("Plain text", "Plain text"),
    ],
)
def test_strip_markdown(text: str, expected: str) -> None:
    assert strip_markdown(text) == expected


def test_parse_strips_markdown_from_plan_text() -> None:
    raw = plan_json(
        summary="**Delhi** air is bad today.",
        items=[
            {"id": "wear_n95", "title": "**Wear a mask**", "action": "* Use N95.", "why": "_Smog_"}
        ],
    )
    parsed = parse_plan_text(raw, {"wear_n95"})
    assert parsed.summary == "Delhi air is bad today."
    item = parsed.items[0]
    assert (item.title, item.action, item.why) == ("Wear a mask", "Use N95.", "Smog")
