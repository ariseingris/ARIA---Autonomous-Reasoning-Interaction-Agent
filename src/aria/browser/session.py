from __future__ import annotations

from dataclasses import dataclass
from html.parser import HTMLParser
from urllib.error import URLError
from urllib.request import Request, urlopen


@dataclass
class PageObservation:
    url: str
    title: str
    text: str
    screenshot_path: str | None = None
    source: str = "playwright"


class _ReadableHTMLParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.title = ""
        self._in_title = False
        self._skip_depth = 0
        self._text: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag == "title":
            self._in_title = True
        if tag in {"script", "style", "noscript", "svg"}:
            self._skip_depth += 1

    def handle_endtag(self, tag: str) -> None:
        if tag == "title":
            self._in_title = False
        if tag in {"script", "style", "noscript", "svg"} and self._skip_depth:
            self._skip_depth -= 1

    def handle_data(self, data: str) -> None:
        clean = " ".join(data.split())
        if not clean:
            return
        if self._in_title:
            self.title = f"{self.title} {clean}".strip()
        elif not self._skip_depth:
            self._text.append(clean)

    @property
    def text(self) -> str:
        return "\n".join(self._text)


class BrowserSession:
    def __init__(self, headless: bool = True) -> None:
        self.headless = headless

    async def fetch(self, url: str, screenshot_path: str | None = None) -> PageObservation:
        try:
            return await self._fetch_with_playwright(url, screenshot_path)
        except Exception as exc:
            return self._fetch_with_urllib(url, exc)

    async def _fetch_with_playwright(self, url: str, screenshot_path: str | None = None) -> PageObservation:
        from playwright.async_api import async_playwright

        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=self.headless)
            try:
                page = await browser.new_page(viewport={"width": 1400, "height": 900})
                await page.goto(url, wait_until="domcontentloaded", timeout=45_000)
                title = await page.title()
                text = await page.locator("body").inner_text(timeout=10_000)
                shot = None
                if screenshot_path:
                    await page.screenshot(path=screenshot_path, full_page=False)
                    shot = screenshot_path
            finally:
                await browser.close()

        return PageObservation(url=url, title=title, text=text[:12000], screenshot_path=shot, source="playwright")

    def _fetch_with_urllib(self, url: str, failure: Exception) -> PageObservation:
        request = Request(url, headers={"User-Agent": "ARIA/0.1 research agent"})
        try:
            with urlopen(request, timeout=30) as response:
                raw = response.read(2_000_000)
                final_url = response.geturl()
                charset = response.headers.get_content_charset() or "utf-8"
        except URLError as exc:
            raise RuntimeError(f"Playwright failed ({failure}); urllib fallback failed ({exc})") from exc

        parser = _ReadableHTMLParser()
        parser.feed(raw.decode(charset, errors="replace"))
        title = parser.title or final_url
        note = f"Fetched with urllib fallback after Playwright failed: {failure}"
        return PageObservation(url=final_url, title=title, text=f"{note}\n\n{parser.text[:12000]}", source="urllib")
