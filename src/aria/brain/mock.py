from __future__ import annotations

from .base import BrainRequest, BrainResponse


class MockBrain:
    provider = "mock"

    def __init__(self, model: str = "mock-brain") -> None:
        self.model = model

    async def generate(self, request: BrainRequest) -> BrainResponse:
        text = request.prompt.strip()
        if request.system:
            text = f"{request.system.strip()}\n\n{text}"
        return BrainResponse(text=f"Mock brain response: {text[:500]}", model=self.model, provider=self.provider)
