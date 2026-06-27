from __future__ import annotations

import base64
import mimetypes
from pathlib import Path


class ClaudeVisionClient:
    def __init__(self, api_key: str | None, model: str) -> None:
        self.api_key = api_key
        self.model = model

    async def describe_image(self, path: Path, prompt: str = "Describe this image for an agent.") -> str:
        if not self.api_key:
            size = path.stat().st_size if path.exists() else 0
            return (
                "Mock vision fallback: ANTHROPIC_API_KEY is not set. "
                f"Observed screenshot {path.name} ({size} bytes). Prompt: {prompt}"
            )

        from anthropic import AsyncAnthropic

        media_type = mimetypes.guess_type(path.name)[0] or "image/png"
        data = base64.b64encode(path.read_bytes()).decode("ascii")
        client = AsyncAnthropic(api_key=self.api_key)
        response = await client.messages.create(
            model=self.model,
            max_tokens=800,
            messages=[
                {
                    "role": "user",
                    "content": [
                        {"type": "image", "source": {"type": "base64", "media_type": media_type, "data": data}},
                        {"type": "text", "text": prompt},
                    ],
                }
            ],
        )
        return "\n".join(block.text for block in response.content if block.type == "text")
