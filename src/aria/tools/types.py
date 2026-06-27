from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Protocol


@dataclass(frozen=True)
class ToolCall:
    name: str
    args: dict[str, Any] = field(default_factory=dict)


@dataclass
class ToolResult:
    name: str
    ok: bool
    content: str
    data: dict[str, Any] = field(default_factory=dict)
    error: str | None = None


class Tool(Protocol):
    name: str
    description: str

    async def __call__(self, **kwargs: Any) -> ToolResult:
        ...
