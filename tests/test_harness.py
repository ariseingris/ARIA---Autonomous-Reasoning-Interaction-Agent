import pytest

from aria.agents.report import Report
from aria.brain import BrainRequest, BrainResponse
from aria.brain import MockBrain
from aria.config import Settings
from aria.harness import ARIAHarness


@pytest.mark.asyncio
async def test_harness_initializes_core_components(tmp_path):
    settings = Settings(
        workspace=tmp_path,
        reports_dir=tmp_path / "reports",
        data_dir=tmp_path / ".aria",
        memory_dir=tmp_path / ".aria" / "memory",
        screenshots_dir=tmp_path / ".aria" / "screenshots",
        openai_api_key=None,
    )
    harness = await ARIAHarness.from_settings(settings).initialize()

    try:
        assert isinstance(harness.brain, MockBrain)
        assert harness.router is not None
        assert "browser.fetch" in harness.router.names
        assert "browser.screenshot" in harness.router.names
        assert harness.research_agent is not None
    finally:
        await harness.shutdown()


class FakeOpenAIBrain:
    provider = "openai"
    model = "fake-openai"

    async def generate(self, request: BrainRequest) -> BrainResponse:
        if "Summarize the observations" in request.prompt:
            return BrainResponse(text="- observation summary", model=self.model, provider=self.provider)
        if "Suggest exactly one next action" in request.prompt:
            return BrainResponse(text="Open the next relevant source.", model=self.model, provider=self.provider)
        assert "Improve this ARIA research report" in request.prompt
        return BrainResponse(text="- polished summary", model=self.model, provider=self.provider)


@pytest.mark.asyncio
async def test_harness_improves_report_with_openai_brain(tmp_path):
    path = tmp_path / "report.md"
    path.write_text("# ARIA Research Report\n", encoding="utf-8")
    harness = ARIAHarness(settings=Settings(workspace=tmp_path), brain=FakeOpenAIBrain())

    report = await harness.improve_report(Report(path=path, content=path.read_text(encoding="utf-8")))

    assert "OpenAI Brain Summary" in report.content
    assert "OpenAI Observation Summary" in report.content
    assert "OpenAI Suggested Next Action" in report.content
    assert "fake-openai" in report.content
    assert "- polished summary" in path.read_text(encoding="utf-8")
    assert "- observation summary" in report.content
    assert "Open the next relevant source." in report.content


@pytest.mark.asyncio
async def test_harness_skips_report_improvement_with_mock_brain(tmp_path):
    path = tmp_path / "report.md"
    content = "# ARIA Research Report\n"
    path.write_text(content, encoding="utf-8")
    harness = ARIAHarness(settings=Settings(workspace=tmp_path), brain=MockBrain())

    report = await harness.improve_report(Report(path=path, content=content))

    assert report.content == content


@pytest.mark.asyncio
async def test_harness_reflection_helpers_skip_mock_brain(tmp_path):
    harness = ARIAHarness(settings=Settings(workspace=tmp_path), brain=MockBrain())

    assert await harness.summarize_observations("report") is None
    assert await harness.suggest_next_action("report") is None
