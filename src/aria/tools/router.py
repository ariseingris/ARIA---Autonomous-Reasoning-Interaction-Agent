from __future__ import annotations

import asyncio
from collections.abc import Awaitable, Callable
from typing import Any

from .types import ToolResult

ToolFunc = Callable[..., Awaitable[ToolResult]]


class ToolRouter:
    def __init__(self, timeout_s: float = 120.0) -> None:
        self._tools: dict[str, ToolFunc] = {}
        self.timeout_s = timeout_s

    @property
    def names(self) -> list[str]:
        return sorted(self._tools)

    def register(self, name: str, func: ToolFunc) -> None:
        if not name:
            raise ValueError("tool name cannot be empty")
        self._tools[name] = func

    async def execute(self, name: str, args: dict[str, Any] | None = None) -> ToolResult:
        if name not in self._tools:
            return ToolResult(
                name=name,
                ok=False,
                content=f"Tool {name!r} is not registered. Available tools: {', '.join(self.names)}",
                error="tool_not_found",
            )

        try:
            return await asyncio.wait_for(self._tools[name](**(args or {})), timeout=self.timeout_s)
        except TimeoutError:
            return ToolResult(name=name, ok=False, content=f"Tool {name!r} timed out", error="timeout")
        except Exception as exc:
            return ToolResult(name=name, ok=False, content=f"Tool {name!r} failed: {exc}", error=type(exc).__name__)
