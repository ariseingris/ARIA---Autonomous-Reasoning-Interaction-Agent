from pathlib import Path

import pytest

from aria.browser.agent import BrowserAgent
from aria.browser.session import PageObservation
from aria.vision.claude import ClaudeVisionClient


class FakeSession:
    async def fetch(self, url: str, screenshot_path: str | None = None) -> PageObservation:
        if screenshot_path:
            Path(screenshot_path).write_bytes(b"fake png bytes")
        return PageObservation(
            url=url,
            title="Fake Page",
            text="Visible browser text",
            screenshot_path=screenshot_path,
            source="fake",
        )


@pytest.mark.asyncio
async def test_browser_screenshot_uses_mock_vision_fallback(tmp_path):
    agent = BrowserAgent(
        FakeSession(),
        screenshots_dir=tmp_path,
        vision=ClaudeVisionClient(api_key=None, model="test-model"),
    )

    result = await agent.screenshot("https://example.com", prompt="Describe for test")

    assert result.ok
    assert result.data["screenshot_path"]
    assert Path(result.data["screenshot_path"]).exists()
    assert "Mock vision fallback" in result.data["vision"]
    assert "Visible browser text" in result.content
