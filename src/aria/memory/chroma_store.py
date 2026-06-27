from __future__ import annotations

from pathlib import Path

from .base import MemoryRecord


class ChromaMemory:
    def __init__(self, path: Path, collection_name: str = "aria") -> None:
        import chromadb

        path.mkdir(parents=True, exist_ok=True)
        self._client = chromadb.PersistentClient(path=str(path))
        self._collection = self._client.get_or_create_collection(collection_name)
        self._counter = self._collection.count()

    async def add(self, record: MemoryRecord) -> None:
        self._counter += 1
        self._collection.add(
            ids=[str(self._counter)],
            documents=[record.text],
            metadatas=[record.metadata or {"source": "aria"}],
        )

    async def search(self, query: str, limit: int = 5) -> list[MemoryRecord]:
        result = self._collection.query(query_texts=[query], n_results=limit)
        docs = result.get("documents") or [[]]
        metas = result.get("metadatas") or [[]]
        return [
            MemoryRecord(text=doc, metadata={str(k): str(v) for k, v in (meta or {}).items()})
            for doc, meta in zip(docs[0], metas[0], strict=False)
        ]

    async def close(self) -> None:
        return None
