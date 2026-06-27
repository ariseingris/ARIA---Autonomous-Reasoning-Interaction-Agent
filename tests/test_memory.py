import pytest

from aria.memory.base import MemoryRecord
from aria.memory.json_store import JsonMemory


@pytest.mark.asyncio
async def test_json_memory_adds_and_searches_records(tmp_path):
    memory = JsonMemory(tmp_path / "memory.json")

    await memory.add(MemoryRecord(text="browser agents need bounded planning loops", metadata={"tool": "test"}))
    await memory.add(MemoryRecord(text="unrelated note", metadata={"tool": "test"}))

    results = await memory.search("bounded browser planning", limit=1)

    assert len(results) == 1
    assert results[0].text == "browser agents need bounded planning loops"
    assert results[0].metadata == {"tool": "test"}
