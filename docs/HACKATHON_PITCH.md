# ARIA Hackathon Pitch

## Problem

People need agents that can do more than answer chat prompts. Real research and personal workflows require opening websites, reading changing pages, remembering useful context, and producing artifacts that can be shared.

## Solution

ARIA is an installable CLI autonomous agent for browser-backed research. It plans a goal, uses Playwright to inspect web pages, captures screenshots, runs vision through a provider abstraction, saves memory, and writes a Markdown report. When `OPENAI_API_KEY` is configured, ARIA also uses an OpenAI Responses brain to polish the final report for presentation.

## Architecture

```text
CLI
  -> ARIAHarness
     -> Brain: OpenAIResponsesBrain or MockBrain
     -> Planner: deterministic ReAct MVP planner
     -> ToolRouter
        -> BrowserAgent: Playwright fetch + screenshot
        -> MemoryStore: JSON default, Chroma optional
        -> ReportAgent
     -> Vision: Claude wrapper with mock fallback
```

The architecture keeps planning, tool routing, browser control, memory, vision, and reporting separate. That makes the hackathon MVP reliable while leaving room for model-backed planning later.

## Demo Flow

Run:

```bash
scripts/final_demo.sh
```

Or step through:

```bash
aria config check
aria brain check
aria demo
aria run "Research browser-use and produce a short report for ARIA"
```

Talk track:

1. Configuration check shows ARIA is installable and key-safe.
2. Brain check shows OpenAI when configured, MockBrain otherwise.
3. Demo opens a real browser page, captures a screenshot, runs vision fallback or Claude, stores memory, and writes a report.
4. Run command shows the normal user-facing workflow.

## What Works Now

- Installable CLI with `uv tool install . --reinstall`.
- `aria "goal"` and `aria run "goal"` goal execution.
- `aria demo` polished 2-minute flow.
- `aria config check` and `aria brain check`.
- Browser fetch and screenshot through Playwright.
- Vision abstraction with keyless mock fallback.
- JSON memory by default, Chroma optional.
- Markdown report generation.
- OpenAI Responses brain integration for final report polish when `OPENAI_API_KEY` is present.

## Next Steps

- Add interactive click/type/scroll browser tools.
- Promote model-backed planning from report polish into plan generation.
- Add memory compaction and pruning.
- Add richer task templates for school portals, deadline tracking, and weekly summaries.
- Package release artifacts beyond local `uv tool install`.
