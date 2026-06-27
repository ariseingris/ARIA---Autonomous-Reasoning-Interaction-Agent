from __future__ import annotations

from datetime import datetime
from pathlib import Path

from aria.tools.types import ToolResult
from aria.vision.claude import ClaudeVisionClient

from .session import BrowserSession


class BrowserAgent:
    def __init__(
        self,
        session: BrowserSession,
        screenshots_dir: Path | None = None,
        vision: ClaudeVisionClient | None = None,
    ) -> None:
        self.session = session
        self.screenshots_dir = screenshots_dir or Path(".aria/screenshots")
        self.screenshots_dir.mkdir(parents=True, exist_ok=True)
        self.vision = vision

    async def fetch(self, url: str) -> ToolResult:
        obs = await self.session.fetch(url)
        content = f"URL: {obs.url}\nTitle: {obs.title}\nSource: {obs.source}\n\n{obs.text}"
        return ToolResult(
            name="browser.fetch",
            ok=True,
            content=content[:14000],
            data={"url": obs.url, "title": obs.title, "source": obs.source, "screenshot_path": obs.screenshot_path},
        )

    async def screenshot(self, url: str, prompt: str = "Describe the visible browser page for a demo.") -> ToolResult:
        path = self._screenshot_path(url)
        obs = await self.session.fetch(url, screenshot_path=str(path))
        vision_text = "Vision skipped: no screenshot was captured."
        if obs.screenshot_path and self.vision:
            vision_text = await self.vision.describe_image(Path(obs.screenshot_path), prompt)

        content = (
            f"URL: {obs.url}\n"
            f"Title: {obs.title}\n"
            f"Source: {obs.source}\n"
            f"Screenshot: {obs.screenshot_path or 'not captured'}\n\n"
            f"Vision:\n{vision_text}\n\n"
            f"Visible text:\n{obs.text[:4000]}"
        )
        return ToolResult(
            name="browser.screenshot",
            ok=obs.screenshot_path is not None,
            content=content,
            data={
                "url": obs.url,
                "title": obs.title,
                "source": obs.source,
                "screenshot_path": obs.screenshot_path,
                "vision": vision_text,
            },
            error=None if obs.screenshot_path else "screenshot_not_captured",
        )

    def _screenshot_path(self, url: str) -> Path:
        safe = "".join(ch if ch.isalnum() else "-" for ch in url.lower()).strip("-")[:60] or "page"
        stamp = datetime.utcnow().strftime("%Y%m%d-%H%M%S")
        return self.screenshots_dir / f"{stamp}-{safe}.png"
