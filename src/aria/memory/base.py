from __future__ import annotations

from dataclasses import dataclass, field
from typing import Protocol


@dataclass
class MemoryRecord:
    text: str
    metadata: dict[str, str] = field(default_factory=dict)


class MemoryStore(Protocol):
    async def add(self, record: MemoryRecord) -> None:
        ...

    async def search(self, query: str, limit: int = 5) -> list[MemoryRecord]:
        ...

    async def close(self) -> None:
        ...
