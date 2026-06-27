from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol


@dataclass(frozen=True)
class BrainRequest:
    prompt: str
    system: str | None = None


@dataclass(frozen=True)
class BrainResponse:
    text: str
    model: str
    provider: str


class Brain(Protocol):
    provider: str
    model: str

    async def generate(self, request: BrainRequest) -> BrainResponse:
        ...
