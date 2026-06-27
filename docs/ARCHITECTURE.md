# ARIA Architecture

ARIA is a Python agent runtime for research, browser interaction, and coding tasks. The design borrows a small set of reusable patterns from browser-use, AutoGen, Anthropic Computer Use, and LangGraph.

## Research-Derived Patterns

### browser-use
- Agent lifecycle is a bounded step loop: capture browser state, ask model/planner, execute one or more actions, append observations, compact history, stop on done or failure limit.
- Planning is explicit state, not hidden prose. Plans can be nudged or regenerated after repeated failures or exploration stalls.
- Browser state is a lossy observation optimized for the model: URL, title, visible text, clickable elements, screenshots when useful.
- Tool execution is routed through a registry with per-action timeout guards and structured `ActionResult` records.
- Context management keeps a compacted memory block plus recent observations instead of sending the whole trajectory.

### AutoGen
- Agent runtime and tool execution are separate. An agent emits tool calls; a tool agent/router validates and executes them.
- Model context is an abstraction. Buffered, token-limited, and custom contexts can swap without changing agent logic.
- Memory updates happen before inference through a `Memory.update_context` style hook.
- Tool call iterations are bounded by `max_tool_iterations`; reflection after tool use is optional.

### Anthropic Computer Use
- The loop appends assistant `tool_use` blocks and user `tool_result` blocks until no tools remain.
- Recoverable API failures use exponential backoff; empty model responses are retried with a continuation nudge.
- Computer/browser tools produce multimodal results, but error results are kept textual and model-readable.
- Prompt caching and image pruning are first-class context management mechanisms.

### LangGraph
- Agent execution can be represented as a state graph: model node, tool node, conditional routing, checkpointing, interrupts.
- Tool nodes validate tool names, inject runtime state when needed, and convert exceptions into observations when configured.
- Retry policies and error handlers belong at node boundaries, not scattered inside business logic.

## Target Module Map

```text
src/aria/
  agents/      task agents and orchestration
  planner/     ReAct-style planner and plan state
  browser/     Playwright browser session and page extraction
  memory/      Memory abstraction, ChromaDB backend, JSON fallback
  vision/      Claude Vision wrapper
  tools/       Tool router, schemas, concrete tools
  cli/         command-line entrypoint
  config/      runtime settings
```

## Runtime Flow

```text
CLI task
  -> ResearchAgent.run()
  -> Planner.create_plan()
  -> for each PlanStep:
       ToolRouter.execute(tool, args)
       Memory.add(observation)
       Planner.observe(result)
       stop on done/failure budget
  -> ReportAgent.write_report()
```

## Core Abstractions

- `Plan` and `PlanStep`: explicit plan state. Steps have `id`, `description`, `tool_name`, `args`, and status.
- `ToolRouter`: registry mapping tool names to async callables. It validates missing tools and normalizes errors into `ToolResult`.
- `BrowserAgent`: Playwright-backed fetch/extract/screenshot helper. It returns structured page observations.
- `MemoryStore`: `add`, `search`, and `close`. `ChromaMemory` is attempted first; `JsonMemory` is always available.
- `VisionClient`: Claude wrapper for image understanding. It is optional and reports a clear error without an API key.
- `ResearchAgent`: orchestrates planner, router, memory, and report generation.

## Why This Shape

ARIA should avoid a monolithic "agent" class. The strongest frameworks separate the loop, tools, memory, and context policy. This keeps the hackathon MVP small while leaving room for LangGraph-style checkpointing later.

The first implementation is intentionally conservative:
- no global mutable registry;
- bounded retries and failure counts;
- readable JSON report artifacts;
- browser and memory backends that fail soft;
- explicit interfaces instead of framework lock-in.

## MVP Command

```bash
uv run aria "Research browser-use and produce a report"
```

The command creates a report under `reports/` and prints the path.
