import pytest

from aria.config import Settings
from aria.memory.json_store import JsonMemory
from aria.tools.types import ToolResult
from aria.transcript import (
    TranscriptFetch,
    TranscriptPipeline,
    TranscriptSegment,
    chunk_transcript,
    find_youtube_url,
)


def test_find_youtube_url_in_task_text():
    assert find_youtube_url("Summarize https://www.youtube.com/watch?v=abc123 for me") == "https://www.youtube.com/watch?v=abc123"
    assert find_youtube_url("https://youtu.be/abc123") == "https://youtu.be/abc123"
    assert find_youtube_url("not a video") is None


def test_chunk_transcript_preserves_timestamps():
    segments = [
        TranscriptSegment(start=0, duration=1, text="intro"),
        TranscriptSegment(start=65, duration=1, text="main topic"),
        TranscriptSegment(start=130, duration=1, text="wrap up"),
    ]

    chunks = chunk_transcript(segments, max_chars=25)

    assert len(chunks) == 3
    assert chunks[0].start == "00:00"
    assert "[01:05] main topic" in chunks[1].text


@pytest.mark.asyncio
async def test_transcript_pipeline_uses_transcript_and_stores_memory(tmp_path, monkeypatch):
    def fake_fetch(video_id: str):
        assert video_id == "abc123"
        return TranscriptFetch(
            segments=[
                TranscriptSegment(start=0, duration=4, text='The speaker says "ship smaller changes".'),
                TranscriptSegment(start=10, duration=4, text="The pipeline should use transcript memory and markdown."),
            ],
            source="youtube-transcript-api",
        )

    monkeypatch.setattr("aria.transcript.fetch_youtube_transcript", fake_fetch)
    memory = JsonMemory(tmp_path / "memory.json")
    pipeline = TranscriptPipeline(memory=memory, reports_dir=tmp_path / "reports")

    report = await pipeline.run_youtube("https://www.youtube.com/watch?v=abc123", task="Summarize video")

    assert report.path.exists()
    assert "Transcript source: youtube-transcript-api" in report.content
    assert "Transcript status: available" in report.content
    assert "## Timeline" in report.content
    assert "## Main Ideas" in report.content
    assert "## Important Quotes" in report.content
    assert "## Technical Concepts" in report.content
    assert "## Action Items" in report.content
    records = await memory.search("transcript markdown", limit=3)
    assert records
    assert records[0].metadata["tool"] == "transcript.pipeline"


class FallbackBrowser:
    async def fetch(self, url: str) -> ToolResult:
        return ToolResult(
            name="browser.fetch",
            ok=True,
            content="URL: https://youtu.be/missing\nTitle: Fallback Video\n\nBrowser page text",
            data={"title": "Fallback Video", "url": url, "source": "test"},
        )


@pytest.mark.asyncio
async def test_transcript_pipeline_falls_back_to_browser(tmp_path, monkeypatch):
    from aria.transcript import TranscriptUnavailable

    def fake_fetch(video_id: str):
        raise TranscriptUnavailable("missing")

    monkeypatch.setattr("aria.transcript.fetch_youtube_transcript", fake_fetch)
    memory = JsonMemory(tmp_path / "memory.json")
    pipeline = TranscriptPipeline(memory=memory, reports_dir=tmp_path / "reports", browser=FallbackBrowser())

    report = await pipeline.run_youtube("https://youtu.be/missing")

    assert "Transcript source: browser fallback" in report.content
    assert "Transcript status: unavailable; metadata only" in report.content
    assert "Transcript unavailable. Browser fallback retrieved metadata only" in report.content
    assert "YouTube video missing" in report.content


@pytest.mark.asyncio
async def test_research_agent_routes_youtube_tasks_to_transcript_pipeline(tmp_path, monkeypatch):
    from aria.agents import ResearchAgent

    def fake_fetch(video_id: str):
        return TranscriptFetch(
            segments=[TranscriptSegment(start=0, duration=1, text="Transcript-only source.")],
            source="timedtext_fallback",
        )

    monkeypatch.setattr("aria.transcript.fetch_youtube_transcript", fake_fetch)
    settings = Settings(reports_dir=tmp_path / "reports", memory_dir=tmp_path / "memory", max_steps=2)
    agent = ResearchAgent(settings, register_default_tools=False)

    try:
        report = await agent.run("Analyze https://youtu.be/abc123")
    finally:
        await agent.close()

    assert "Transcript source: timedtext fallback" in report.content
    assert "Transcript-only source" in report.content
