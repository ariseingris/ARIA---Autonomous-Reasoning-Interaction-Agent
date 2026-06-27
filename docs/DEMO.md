# ARIA 2-Minute Demo

## Setup Check

Run this before presenting:

```bash
uv run pytest -q
uv run aria demo
```

If Playwright is installed, the demo captures a real screenshot under `.aria/screenshots/`.
If `ANTHROPIC_API_KEY` is not set, ARIA uses the mock vision fallback so the demo still works.

## Presentation Flow

### 0:00-0:20 - One-Sentence Pitch

ARIA is a CLI autonomous agent that plans a task, uses a browser, captures what it sees, stores useful memory, and writes a research report.

Command:

```bash
uv run aria demo
```

### 0:20-0:50 - Browser Computer Use

Point to the `Browser + Vision` table.

Say:

ARIA opens the browser with Playwright, visits the target page, captures visible page state, and saves a screenshot artifact. The browser layer returns structured observations instead of raw automation logs.

### 0:50-1:15 - Vision Abstraction

Point to the `Vision` row.

Say:

The same screenshot is passed through the vision abstraction. In production this calls Claude Vision. For a hackathon floor demo without API keys, the mock fallback proves the wiring and keeps the run deterministic.

### 1:15-1:40 - Long-Term Memory

Point to the `Memory` table.

Say:

ARIA saves observations as memory records and retrieves them before or during later work. The current default is JSON for reliability, with Chroma available by setting `ARIA_MEMORY_BACKEND=chroma`.

### 1:40-2:00 - Report Artifact

Point to the final `Report written` line.

Say:

The agent finishes by writing a Markdown research report under `reports/`. The normal judge command is:

```bash
uv run aria "Research browser-use and produce a short report for ARIA"
```

## Expected Artifacts

- Report: `reports/aria-report-*.md`
- Screenshots: `.aria/screenshots/*.png`
- Memory: `.aria/memory/memory.json`

## Current MVP Boundaries

- Planning is deterministic for demo reliability.
- Interactive click/type/scroll tools are intentionally left for the next milestone.
- Model-backed planning is not enabled yet.
