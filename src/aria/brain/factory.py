from __future__ import annotations

from aria.config import Settings

from .base import Brain
from .mock import MockBrain
from .openai_responses import OpenAIResponsesBrain


def create_brain(settings: Settings) -> Brain:
    if settings.openai_api_key:
        return OpenAIResponsesBrain(api_key=settings.openai_api_key, model=settings.model)
    return MockBrain(model=settings.model)
