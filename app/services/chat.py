"""Scoped follow-up chat about the user's plan."""

import logging

from app.core.errors import AIUnavailableError
from app.models.chat import ChatRequest, ChatResponse, ChatSource
from app.services.gemini import TextGenerator
from app.services.prompts import CHAT_SYSTEM_PROMPT_V2, build_chat_prompt

logger = logging.getLogger(__name__)

UNAVAILABLE_REPLY = (
    "Sorry, I can't answer questions right now. Your plan above still has today's advice."
)
MAX_REPLY_CHARS = 1200


class ChatService:
    """Answers follow-up questions using Gemini, with a safe fallback."""

    def __init__(self, generator: TextGenerator | None) -> None:
        """Create the service. With no generator, every reply is the fallback message."""
        self._generator = generator

    async def reply(self, request: ChatRequest) -> ChatResponse:
        """Return the assistant's reply to the user's message."""
        if self._generator is None:
            return ChatResponse(reply=UNAVAILABLE_REPLY, source=ChatSource.UNAVAILABLE)

        context = request.context.model_dump(mode="json") | {"language": request.language.value}
        history = [turn.model_dump() for turn in request.history]
        prompt = build_chat_prompt(context, history, request.message)
        try:
            text = await self._generator.generate_chat(CHAT_SYSTEM_PROMPT_V2, prompt)
        except AIUnavailableError as exc:
            logger.warning("Chat unavailable: %s", exc)
            return ChatResponse(reply=UNAVAILABLE_REPLY, source=ChatSource.UNAVAILABLE)
        return ChatResponse(reply=text.strip()[:MAX_REPLY_CHARS], source=ChatSource.AI)
