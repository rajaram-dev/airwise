"""Chat request and response models."""

from enum import StrEnum
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

from app.models.plan import RiskLevel
from app.models.profile import Language

MAX_MESSAGE_CHARS = 500
MAX_HISTORY_TURNS = 6


class ChatTurn(BaseModel):
    """One earlier message in the conversation."""

    model_config = ConfigDict(extra="forbid")

    role: Literal["user", "assistant"]
    text: str = Field(min_length=1, max_length=1000)


class ChatContext(BaseModel):
    """Compact plan context the client sends back with each question."""

    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    location_name: str = Field(default="", max_length=100)
    aqi: int = Field(ge=0, le=1000)
    risk_level: RiskLevel
    summary: str = Field(default="", max_length=600)
    item_titles: list[str] = Field(default_factory=list, max_length=15)


class ChatRequest(BaseModel):
    """A follow-up question about the plan."""

    model_config = ConfigDict(extra="forbid")

    message: str = Field(min_length=1, max_length=MAX_MESSAGE_CHARS)
    context: ChatContext
    history: list[ChatTurn] = Field(default_factory=list, max_length=MAX_HISTORY_TURNS)
    language: Language = Language.EN


class ChatSource(StrEnum):
    """Whether the reply came from the AI."""

    AI = "ai"
    UNAVAILABLE = "unavailable"


class ChatResponse(BaseModel):
    """Assistant reply."""

    reply: str
    source: ChatSource
