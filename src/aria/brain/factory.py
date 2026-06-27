from __future__ import annotations

import os

from aria.config import Settings

from .base import Brain
from .mock import MockBrain
from .openai_responses import OpenAIResponsesBrain


def create_brain(settings: Settings) -> Brain:
    if os.getenv("ARIA_ALLOW_MOCK_BRAIN", "").lower() in {"1", "true", "yes"}:
        return MockBrain(model=settings.model)
    if settings.openai_api_key:
        return OpenAIResponsesBrain(api_key=settings.openai_api_key, model=settings.model)
    return MockBrain(model=settings.model)
