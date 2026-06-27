from __future__ import annotations

import argparse
import asyncio
import sys
from pathlib import Path

from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from aria.config import Settings
from aria.harness import ARIAHarness
from aria.memory import MemoryRecord


async def run_task(task: str) -> int:
    console = Console()
    settings = Settings.from_env()
    harness = await ARIAHarness.from_settings(settings).initialize()
    console.print(Panel.fit(task, title="ARIA Task", border_style="cyan"))
    try:
        report = await harness.run_goal(task)
    finally:
        await harness.shutdown()

    console.print(f"[green]Report written[/green] {report.path}")
    console.print(f"[dim]Report size:[/dim] {len(report.content)} characters")
    return 0


async def run_demo() -> int:
    console = Console()
    settings = Settings.from_env()
    harness = await ARIAHarness.from_settings(settings).initialize()
    assert harness.router is not None
    assert harness.memory is not None
    task = "Research browser-use and produce a short report for ARIA"
    demo_url = "https://github.com/browser-use/browser-use"

    console.print(Panel.fit("ARIA hackathon demo", subtitle="2-minute flow", border_style="cyan"))
    console.print("[bold]1. Planning + browser use[/bold]")
    console.print(f"[dim]Task:[/dim] {task}")

    try:
        screenshot = await harness.router.execute(
            "browser.screenshot",
            {
                "url": demo_url,
                "prompt": "Summarize what is visible on this browser page for a hackathon demo.",
            },
        )

        table = Table(title="Browser + Vision")
        table.add_column("Signal", style="cyan")
        table.add_column("Value")
        table.add_row("Tool", screenshot.name)
        table.add_row("Status", "ok" if screenshot.ok else f"failed: {screenshot.error}")
        table.add_row("Source", str(screenshot.data.get("source", "unknown")))
        table.add_row("Screenshot", str(screenshot.data.get("screenshot_path") or "not captured"))
        table.add_row("Vision", str(screenshot.data.get("vision") or "not available")[:180])
        console.print(table)

        console.print("[bold]2. Memory save + retrieve[/bold]")
        await harness.memory.add(
            MemoryRecord(
                text="Demo memory: ARIA can fetch browser pages, capture screenshots, run vision, and write reports.",
                metadata={"tool": "demo", "task": "hackathon"},
            )
        )
        memories = await harness.memory.search("ARIA browser screenshots vision reports", limit=3)
        memory_table = Table(title="Memory")
        memory_table.add_column("Record", style="cyan")
        memory_table.add_column("Content")
        for i, record in enumerate(memories, start=1):
            memory_table.add_row(str(i), record.text[:180])
        console.print(memory_table)

        console.print("[bold]3. Report generation[/bold]")
        report = await harness.run_goal(task)
    finally:
        await harness.shutdown()

    console.print(f"[green]Report written[/green] {Path(report.path)}")
    console.print("[dim]Run the normal command for judges:[/dim] uv run aria \"Research browser-use and produce a short report for ARIA\"")
    return 0


async def config_check() -> int:
    console = Console()
    settings = Settings.from_env()
    table = Table(title="ARIA Configuration")
    table.add_column("Setting", style="cyan")
    table.add_column("Value")
    for key, value in settings.redacted().items():
        table.add_row(key, str(value))
    table.add_row("Brain provider", "openai" if settings.openai_api_key else "mock fallback")
    table.add_row("Vision provider", "anthropic" if settings.anthropic_api_key else "mock fallback")
    table.add_row("Data dir exists", str(settings.data_dir.exists()))
    table.add_row("Reports dir exists", str(settings.reports_dir.exists()))
    console.print(table)
    return 0


async def brain_check() -> int:
    console = Console()
    harness = await ARIAHarness.from_settings(Settings.from_env()).initialize()
    assert harness.brain is not None
    try:
        table = Table(title="ARIA Brain")
        table.add_column("Signal", style="cyan")
        table.add_column("Value")
        table.add_row("Provider", harness.brain.provider)
        table.add_row("Model", harness.brain.model)
        table.add_row("API key", "configured" if harness.settings.openai_api_key else "not configured")
        table.add_row("Fallback", "none" if harness.brain.provider == "openai" else "MockBrain")
        console.print(table)
    finally:
        await harness.shutdown()
    return 0


async def memory_search(query: str) -> int:
    console = Console()
    harness = await ARIAHarness.from_settings(Settings.from_env()).initialize()
    assert harness.memory is not None
    try:
        records = await harness.memory.search(query, limit=5)
    finally:
        await harness.shutdown()

    table = Table(title=f"Memory Search: {query}")
    table.add_column("#", style="cyan")
    table.add_column("Metadata")
    table.add_column("Text")
    for i, record in enumerate(records, start=1):
        table.add_row(str(i), str(record.metadata), record.text[:220])
    if not records:
        table.add_row("-", "-", "No matching memory records.")
    console.print(table)
    return 0


def _help_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="aria", description="Run the ARIA autonomous agent.")
    subcommands = parser.add_argument_group("commands")
    subcommands.add_argument("command", nargs="?", help="goal text, demo, run, config, brain, or memory")
    subcommands.add_argument("args", nargs="*", help="arguments for the command")
    return parser


def main(argv: list[str] | None = None) -> int:
    argv = list(sys.argv[1:] if argv is None else argv)
    parser = _help_parser()
    if not argv or argv[0] in {"-h", "--help"}:
        parser.print_help()
        return 0 if argv else 2

    command = argv[0]
    rest = argv[1:]
    if command == "demo":
        return asyncio.run(run_demo())
    if command == "run":
        if not rest:
            parser.error("aria run requires a goal")
        return asyncio.run(run_task(" ".join(rest)))
    if command == "config" and rest == ["check"]:
        return asyncio.run(config_check())
    if command == "brain" and rest == ["check"]:
        return asyncio.run(brain_check())
    if command == "memory" and rest[:1] == ["search"] and len(rest) > 1:
        return asyncio.run(memory_search(" ".join(rest[1:])))
    if command in {"config", "brain", "memory"}:
        parser.error(f"invalid {command!r} command")

    return asyncio.run(run_task(" ".join(argv)))


def app() -> None:
    raise SystemExit(main())
