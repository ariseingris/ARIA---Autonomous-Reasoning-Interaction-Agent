from __future__ import annotations

from .base import BrainRequest, BrainResponse


class OpenAIResponsesBrain:
    provider = "openai"

    def __init__(self, api_key: str, model: str) -> None:
        self.api_key = api_key
        self.model = model

    async def generate(self, request: BrainRequest) -> BrainResponse:
        from openai import AsyncOpenAI

        client = AsyncOpenAI(api_key=self.api_key)
        input_text = request.prompt if not request.system else f"{request.system}\n\n{request.prompt}"
        response = await client.responses.create(model=self.model, input=input_text)
        return BrainResponse(text=response.output_text, model=self.model, provider=self.provider)
