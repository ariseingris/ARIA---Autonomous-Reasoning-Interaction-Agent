import pytest

from aria.agents import ResearchAgent
from aria.config import Settings


@pytest.mark.asyncio
async def test_research_agent_writes_report_for_memory_task(tmp_path):
    settings = Settings(reports_dir=tmp_path / "reports", memory_dir=tmp_path / "memory", max_steps=4)
    agent = ResearchAgent(settings)

    try:
        report = await agent.run("Summarize what ARIA already knows")
    finally:
        await agent.close()

    assert report.path.exists()
    assert "ARIA Research Report" in report.content
    assert "memory.search" in report.content
    assert "report.write" in report.content
