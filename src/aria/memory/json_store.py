from __future__ import annotations

import json
from pathlib import Path

from .base import MemoryRecord


class JsonMemory:
    def __init__(self, path: Path) -> None:
        self.path = path
        self.path.parent.mkdir(parents=True, exist_ok=True)
        if not self.path.exists():
            self.path.write_text("[]", encoding="utf-8")

    def _read(self) -> list[dict[str, object]]:
        return json.loads(self.path.read_text(encoding="utf-8"))

    async def add(self, record: MemoryRecord) -> None:
        data = self._read()
        data.append({"text": record.text, "metadata": record.metadata})
        self.path.write_text(json.dumps(data, indent=2), encoding="utf-8")

    async def search(self, query: str, limit: int = 5) -> list[MemoryRecord]:
        terms = {term.lower() for term in query.split() if len(term) > 2}
        scored: list[tuple[int, dict[str, object]]] = []
        for item in self._read():
            text = str(item.get("text", ""))
            score = sum(1 for term in terms if term in text.lower())
            scored.append((score, item))
        scored.sort(key=lambda pair: pair[0], reverse=True)
        return [
            MemoryRecord(text=str(item.get("text", "")), metadata=dict(item.get("metadata", {})))
            for score, item in scored[:limit]
            if score > 0 or not terms
        ]

    async def close(self) -> None:
        return None
