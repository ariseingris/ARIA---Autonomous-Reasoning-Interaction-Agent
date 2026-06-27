from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from datetime import datetime
from html import unescape
from pathlib import Path
from urllib.error import URLError
from urllib.parse import parse_qs, urlencode, urlparse
from urllib.request import Request, urlopen
from xml.etree import ElementTree

from aria.brain import Brain, BrainRequest
from aria.browser import BrowserAgent
from aria.memory import MemoryRecord, MemoryStore


@dataclass(frozen=True)
class TranscriptSegment:
    start: float
    duration: float
    text: str

    @property
    def timestamp(self) -> str:
        total = int(self.start)
        hours, remainder = divmod(total, 3600)
        minutes, seconds = divmod(remainder, 60)
        if hours:
            return f"{hours:02d}:{minutes:02d}:{seconds:02d}"
        return f"{minutes:02d}:{seconds:02d}"


@dataclass(frozen=True)
class TranscriptChunk:
    index: int
    start: str
    end: str
    text: str


@dataclass(frozen=True)
class TranscriptFetch:
    segments: list[TranscriptSegment]
    source: str


@dataclass
class TranscriptPipelineResult:
    url: str
    video_id: str
    title: str
    source: str
    chunks: list[TranscriptChunk]
    chunk_summaries: list[str]
    merged_summary: str
    timeline: list[str] = field(default_factory=list)
    main_ideas: list[str] = field(default_factory=list)
    important_quotes: list[str] = field(default_factory=list)
    technical_concepts: list[str] = field(default_factory=list)
    action_items: list[str] = field(default_factory=list)
    markdown: str = ""


class TranscriptUnavailable(RuntimeError):
    pass


class TranscriptPipeline:
    def __init__(
        self,
        *,
        memory: MemoryStore,
        reports_dir: Path,
        brain: Brain | None = None,
        browser: BrowserAgent | None = None,
        max_chunk_chars: int = 5500,
    ) -> None:
        self.memory = memory
        self.reports_dir = reports_dir
        self.brain = brain
        self.browser = browser
        self.max_chunk_chars = max_chunk_chars
        self.reports_dir.mkdir(parents=True, exist_ok=True)

    async def run_youtube(self, url: str, task: str | None = None):
        video_id = youtube_video_id(url)
        if not video_id:
            raise ValueError(f"Not a YouTube URL: {url}")

        title = f"YouTube video {video_id}"
        try:
            transcript = fetch_youtube_transcript(video_id)
            segments = transcript.segments
            source = transcript.source
            chunks = chunk_transcript(segments, max_chars=self.max_chunk_chars)
            chunk_summaries = [await self._summarize_chunk(chunk) for chunk in chunks]
            merged_summary = await self._merge_summaries(chunk_summaries)
            extracted = await self._extract_sections(merged_summary, chunk_summaries)
        except TranscriptUnavailable:
            source = "browser_fallback"
            fallback = self._metadata(url)
            title = fallback.get("title") or title
            chunks = []
            chunk_summaries = []
            merged_summary = (
                "Transcript unavailable. Browser fallback retrieved metadata only, so no transcript-grounded "
                "summary, timeline, quotes, technical concepts, or action items could be extracted."
            )
            extracted = {
                "timeline": [],
                "main_ideas": [],
                "important_quotes": [],
                "technical_concepts": [],
                "action_items": [],
            }

        result = TranscriptPipelineResult(
            url=url,
            video_id=video_id,
            title=title,
            source=source,
            chunks=chunks,
            chunk_summaries=chunk_summaries,
            merged_summary=merged_summary,
            timeline=extracted["timeline"],
            main_ideas=extracted["main_ideas"],
            important_quotes=extracted["important_quotes"],
            technical_concepts=extracted["technical_concepts"],
            action_items=extracted["action_items"],
        )
        result.markdown = render_transcript_markdown(result, task=task)
        await self._store_memory(result)
        return self._write_report(result)

    def _metadata(self, url: str) -> dict[str, str]:
        try:
            html = _http_text(url, timeout=8, limit=500_000)
        except Exception:
            return {}
        title_match = re.search(r"<title[^>]*>(.*?)</title>", html, re.I | re.S)
        title = " ".join(unescape(title_match.group(1)).split()) if title_match else ""
        return {
            "url": url,
            "title": title,
            "source": "browser_metadata",
        }

    async def _summarize_chunk(self, chunk: TranscriptChunk) -> str:
        if self.brain is None or self.brain.provider == "mock":
            return deterministic_summary(chunk.text, prefix=f"{chunk.start}-{chunk.end}")
        try:
            response = await self.brain.generate(
                BrainRequest(
                    system="You summarize YouTube transcript chunks. Use only the transcript text.",
                    prompt=(
                        f"Summarize this transcript chunk from {chunk.start} to {chunk.end}. "
                        "Preserve claims, names, numbers, technical terms, quotes, and action items. "
                        "Return concise bullets.\n\n"
                        f"{chunk.text[:12000]}"
                    ),
                )
            )
            return response.text.strip()
        except Exception:
            return deterministic_summary(chunk.text, prefix=f"{chunk.start}-{chunk.end}")

    async def _merge_summaries(self, summaries: list[str]) -> str:
        joined = "\n\n".join(f"Chunk {i + 1}:\n{summary}" for i, summary in enumerate(summaries))
        if self.brain is None or self.brain.provider == "mock":
            return "\n".join(summaries)
        try:
            response = await self.brain.generate(
                BrainRequest(
                    system="You merge transcript chunk summaries. Use only supplied summaries.",
                    prompt=(
                        "Merge these chunk summaries into one coherent source-grounded summary. "
                        "Do not add facts that are not present.\n\n"
                        f"{joined[:16000]}"
                    ),
                )
            )
            return response.text.strip()
        except Exception:
            return "\n".join(summaries)

    async def _extract_sections(self, merged_summary: str, summaries: list[str]) -> dict[str, list[str]]:
        source = f"{merged_summary}\n\n" + "\n\n".join(summaries)
        if self.brain is None or self.brain.provider == "mock":
            return deterministic_extract(source)

        try:
            response = await self.brain.generate(
                BrainRequest(
                    system="Extract structured notes from transcript-derived summaries. Use only supplied text.",
                    prompt=(
                        "Return strict JSON with keys: timeline, main_ideas, important_quotes, "
                        "technical_concepts, action_items. Each value must be a list of strings. "
                        "If a section has no evidence, return an empty list.\n\n"
                        f"{source[:16000]}"
                    ),
                )
            )
            data = json.loads(_json_object(response.text))
        except Exception:
            data = deterministic_extract(source)
        return {
            "timeline": _string_list(data.get("timeline")),
            "main_ideas": _string_list(data.get("main_ideas")),
            "important_quotes": _string_list(data.get("important_quotes")),
            "technical_concepts": _string_list(data.get("technical_concepts")),
            "action_items": _string_list(data.get("action_items")),
        }

    async def _store_memory(self, result: TranscriptPipelineResult) -> None:
        await self.memory.add(
            MemoryRecord(
                text=result.markdown[:12000],
                metadata={
                    "tool": "transcript.pipeline",
                    "source": result.source,
                    "video_id": result.video_id,
                    "title": result.title[:200],
                },
            )
        )

    def _write_report(self, result: TranscriptPipelineResult):
        from aria.agents.report import Report

        stamp = datetime.utcnow().strftime("%Y%m%d-%H%M%S")
        path = self.reports_dir / f"youtube-transcript-{result.video_id}-{stamp}.md"
        path.write_text(result.markdown, encoding="utf-8")
        return Report(path=path, content=result.markdown)


def youtube_video_id(value: str) -> str | None:
    parsed = urlparse(value.strip())
    host = parsed.netloc.lower().removeprefix("www.")
    if host in {"youtube.com", "m.youtube.com", "music.youtube.com"}:
        if parsed.path == "/watch":
            return parse_qs(parsed.query).get("v", [None])[0]
        match = re.match(r"/(?:embed|shorts)/([^/?#]+)", parsed.path)
        if match:
            return match.group(1)
    if host == "youtu.be":
        return parsed.path.strip("/") or None
    return None


def is_youtube_url(value: str) -> bool:
    return youtube_video_id(value) is not None


def find_youtube_url(text: str) -> str | None:
    for match in re.finditer(r"https?://[^\s)>\]]+", text):
        candidate = match.group(0).rstrip(".,;")
        if is_youtube_url(candidate):
            return candidate
    if is_youtube_url(text.strip()):
        return text.strip()
    return None


def fetch_youtube_transcript(video_id: str) -> TranscriptFetch:
    segments = _fetch_transcript_with_library(video_id)
    if segments:
        return TranscriptFetch(segments=segments, source="youtube-transcript-api")

    try:
        tracks = _caption_tracks(video_id)
        if not tracks:
            raise TranscriptUnavailable(f"No caption tracks found for {video_id}")
        track = _pick_track(tracks)
        transcript_xml = _http_text(_timedtext_url(video_id, track))
        segments = _parse_transcript_xml(transcript_xml)
    except (URLError, OSError, ElementTree.ParseError, KeyError, ValueError) as exc:
        raise TranscriptUnavailable(f"Could not fetch transcript for {video_id}: {exc}") from exc
    if not segments:
        raise TranscriptUnavailable(f"Transcript was empty for {video_id}")
    return TranscriptFetch(segments=segments, source="timedtext_fallback")


def _fetch_transcript_with_library(video_id: str) -> list[TranscriptSegment]:
    try:
        from youtube_transcript_api import YouTubeTranscriptApi

        transcript = YouTubeTranscriptApi().fetch(video_id, languages=("en",))
        return [
            TranscriptSegment(
                start=float(snippet.start),
                duration=float(snippet.duration),
                text=" ".join(snippet.text.split()),
            )
            for snippet in transcript
            if snippet.text.strip()
        ]
    except Exception:
        return []


def chunk_transcript(segments: list[TranscriptSegment], max_chars: int = 5500) -> list[TranscriptChunk]:
    chunks: list[TranscriptChunk] = []
    current: list[str] = []
    start = "00:00"
    end = "00:00"

    for segment in segments:
        line = f"[{segment.timestamp}] {segment.text.strip()}"
        if not line.strip():
            continue
        if current and sum(len(item) + 1 for item in current) + len(line) > max_chars:
            chunks.append(TranscriptChunk(len(chunks) + 1, start, end, "\n".join(current)))
            current = []
            start = segment.timestamp
        if not current:
            start = segment.timestamp
        current.append(line)
        end = segment.timestamp

    if current:
        chunks.append(TranscriptChunk(len(chunks) + 1, start, end, "\n".join(current)))
    return chunks


def render_transcript_markdown(result: TranscriptPipelineResult, task: str | None = None) -> str:
    source_label = {
        "youtube-transcript-api": "youtube-transcript-api",
        "timedtext_fallback": "timedtext fallback",
        "browser_fallback": "browser fallback",
    }.get(result.source, result.source)
    transcript_available = result.source != "browser_fallback"
    lines = [
        f"# {result.title}",
        "",
        "## At a Glance",
        "",
        f"- Source URL: {result.url}",
        f"- Transcript source: {source_label}",
        f"- Transcript status: {'available' if transcript_available else 'unavailable; metadata only'}",
        f"- Chunks summarized: {len(result.chunks)}",
    ]
    if task:
        lines.append(f"- Task: {task}")
    lines.extend(
        [
            "",
            "## Summary",
            "",
            result.merged_summary or "No summary generated.",
            "",
            "## Timeline",
            "",
            _bullets(result.timeline),
            "",
            "## Main Ideas",
            "",
            _bullets(result.main_ideas),
            "",
            "## Important Quotes",
            "",
            _bullets(result.important_quotes),
            "",
            "## Technical Concepts",
            "",
            _bullets(result.technical_concepts),
            "",
            "## Action Items",
            "",
            _bullets(result.action_items),
            "",
            "## Chunk Summaries",
            "",
        ]
    )
    if result.chunks:
        for chunk, summary in zip(result.chunks, result.chunk_summaries, strict=False):
            lines.extend([f"### Chunk {chunk.index}: {chunk.start}-{chunk.end}", "", summary, ""])
    else:
        lines.extend(["No transcript chunks were available.", ""])
    return "\n".join(lines).strip() + "\n"


def deterministic_summary(text: str, prefix: str = "") -> str:
    sentences = re.split(r"(?<=[.!?])\s+", " ".join(text.split()))
    picked = [sentence for sentence in sentences if sentence][:5]
    if not picked:
        return "- No transcript content found."
    label = f"{prefix}: " if prefix else ""
    return "\n".join(f"- {label}{sentence[:280]}" for sentence in picked)


def deterministic_extract(source: str) -> dict[str, list[str]]:
    lines = [line.strip("- ").strip() for line in source.splitlines() if line.strip()]
    timeline = [line for line in lines if re.search(r"\b\d{1,2}:\d{2}(?::\d{2})?\b", line)][:8]
    quotes = re.findall(r'"([^"]{12,220})"', source)
    technical = [
        line
        for line in lines
        if re.search(r"\b(api|model|code|data|system|architecture|algorithm|pipeline|memory|browser|transcript)\b", line, re.I)
    ][:8]
    actions = [line for line in lines if re.search(r"\b(should|need to|must|next|action|todo|implement|build)\b", line, re.I)][:8]
    ideas = [line for line in lines if line not in timeline][:8]
    return {
        "timeline": timeline,
        "main_ideas": ideas,
        "important_quotes": quotes[:8],
        "technical_concepts": technical,
        "action_items": actions,
    }


def _caption_tracks(video_id: str) -> list[dict[str, str]]:
    root = ElementTree.fromstring(_http_text(f"https://www.youtube.com/api/timedtext?{urlencode({'type': 'list', 'v': video_id})}"))
    tracks: list[dict[str, str]] = []
    for track in root.findall("track"):
        tracks.append({key: track.attrib.get(key, "") for key in ("lang_code", "name", "kind")})
    return tracks


def _pick_track(tracks: list[dict[str, str]]) -> dict[str, str]:
    for track in tracks:
        if track.get("lang_code", "").startswith("en") and track.get("kind") != "asr":
            return track
    for track in tracks:
        if track.get("lang_code", "").startswith("en"):
            return track
    return tracks[0]


def _timedtext_url(video_id: str, track: dict[str, str]) -> str:
    params = {"v": video_id, "lang": track["lang_code"]}
    if track.get("name"):
        params["name"] = track["name"]
    if track.get("kind"):
        params["kind"] = track["kind"]
    return f"https://www.youtube.com/api/timedtext?{urlencode(params)}"


def _parse_transcript_xml(text: str) -> list[TranscriptSegment]:
    root = ElementTree.fromstring(text)
    segments: list[TranscriptSegment] = []
    for node in root.findall("text"):
        content = unescape("".join(node.itertext())).strip()
        if not content:
            continue
        segments.append(
            TranscriptSegment(
                start=float(node.attrib.get("start", "0")),
                duration=float(node.attrib.get("dur", "0")),
                text=" ".join(content.split()),
            )
        )
    return segments


def _http_text(url: str, timeout: int = 30, limit: int = 2_000_000) -> str:
    request = Request(url, headers={"User-Agent": "ARIA/0.1 transcript pipeline"})
    with urlopen(request, timeout=timeout) as response:
        raw = response.read(limit)
        charset = response.headers.get_content_charset() or "utf-8"
    return raw.decode(charset, errors="replace")


def _json_object(text: str) -> str:
    start = text.find("{")
    end = text.rfind("}")
    if start == -1 or end == -1 or end < start:
        raise ValueError("No JSON object found")
    return text[start : end + 1]


def _string_list(value: object) -> list[str]:
    if not isinstance(value, list):
        return []
    return [str(item).strip() for item in value if str(item).strip()]


def _bullets(items: list[str]) -> str:
    return "\n".join(f"- {item}" for item in items) if items else "- None found."
