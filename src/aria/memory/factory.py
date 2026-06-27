from __future__ import annotations

import os
from pathlib import Path

from .base import MemoryStore
from .json_store import JsonMemory


def create_memory(path: Path, backend: str | None = None) -> MemoryStore:
    selected = (backend or os.getenv("ARIA_MEMORY_BACKEND", "json")).lower()
    if selected != "chroma":
        return JsonMemory(path / "memory.json")

    try:
        from .chroma_store import ChromaMemory

        return ChromaMemory(path / "chroma")
    except Exception:
        return JsonMemory(path / "memory.json")
