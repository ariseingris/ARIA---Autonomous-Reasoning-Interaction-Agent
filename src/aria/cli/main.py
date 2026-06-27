from __future__ import annotations

import argparse
import asyncio
import getpass
import os
import platform
import signal
import shutil
import sys
import webbrowser
from pathlib import Path

from rich.console import Console
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.table import Table

from aria import __version__
from aria.config import Settings
from aria.config.settings import default_write_env_path, user_env_path, write_env_value
from aria.harness import ARIAHarness
from aria.memory import MemoryRecord

console = Console()


def _success(message: str) -> None:
    console.print(f"[bold green]PASS[/bold green] {message}")


def _warn(message: str) -> None:
    console.print(f"[bold yellow]WARN[/bold yellow] {message}")


def _fail(message: str) -> None:
    console.print(f"[bold red]FAIL[/bold red] {message}")


def _config_source(settings: Settings) -> str:
    sources: list[str] = []
    if user_env_path().exists():
        sources.append(str(user_env_path()))
    if Path("aria.toml").exists():
        sources.append("aria.toml")
    if Path(".env").exists():
        sources.append(".env")
    env_keys = {"OPENAI_API_KEY", "ANTHROPIC_API_KEY", "ARIA_MODEL", "ARIA_MEMORY_BACKEND", "ARIA_DATA_DIR"}
    if any(os.getenv(key) for key in env_keys):
        sources.append("environment")
    return ", ".join(sources) if sources else f"defaults ({settings.workspace})"


def _report_files() -> list[Path]:
    return sorted(Path("reports").glob("*.md"), key=lambda path: path.stat().st_mtime, reverse=True)


def _short(text: str, limit: int = 180) -> str:
    clean = " ".join(text.split())
    return clean if len(clean) <= limit else f"{clean[: limit - 1]}..."


async def run_task(task: str) -> int:
    settings = Settings.from_env()
    if not _brain_ready(settings):
        return 1
    console.print(Panel.fit(task, title="ARIA Run", border_style="cyan"))
    harness: ARIAHarness | None = None
    with Progress(SpinnerColumn(), TextColumn("[progress.description]{task.description}"), console=console, transient=True) as progress:
        progress.add_task("Initializing harness", total=None)
        harness = await ARIAHarness.from_settings(settings).initialize()
        progress.add_task("Running deterministic planner and tools", total=None)
        try:
            report = await harness.run_goal(task)
        finally:
            progress.add_task("Shutting down", total=None)
            await harness.shutdown()

    table = Table(title="Run Summary")
    table.add_column("Signal", style="cyan")
    table.add_column("Value")
    table.add_row("Status", "[green]success[/green]")
    table.add_row("Report", str(report.path))
    table.add_row("Size", f"{len(report.content)} characters")
    table.add_row("Brain", "OpenAI reflection" if "OpenAI Brain Summary" in report.content else "deterministic fallback")
    console.print(table)
    return 0


async def run_demo() -> int:
    settings = Settings.from_env()
    if not _brain_ready(settings):
        return 1
    task = "Research browser-use and produce a short report for ARIA"
    demo_url = "https://github.com/browser-use/browser-use"

    console.print(Panel.fit("[bold]ARIA hackathon demo[/bold]", subtitle="end-to-end CLI flow", border_style="cyan"))
    steps = [
        "Initialize ARIA",
        "Load Config",
        "Initialize Brain",
        "Initialize Browser",
        "Run Planner",
        "Browser Observation",
        "Vision Analysis",
        "Memory Update",
        "Generate Report",
        "Summary",
    ]

    harness: ARIAHarness | None = None
    with Progress(SpinnerColumn(), TextColumn("[progress.description]{task.description}"), console=console, transient=True) as progress:
        progress.add_task(steps[0], total=None)
        harness = await ARIAHarness.from_settings(settings).initialize()
        assert harness.router is not None
        assert harness.memory is not None
        assert harness.brain is not None

        progress.add_task(steps[1], total=None)
        config_table = _config_table(settings)
        console.print(config_table)

        progress.add_task(steps[2], total=None)
        brain_table = _brain_table(harness)
        console.print(brain_table)

        progress.add_task(steps[3], total=None)
        progress.add_task(steps[4], total=None)
        progress.add_task(steps[5], total=None)
        screenshot = await harness.router.execute(
            "browser.screenshot",
            {
                "url": demo_url,
                "prompt": "Summarize what is visible on this browser page for a hackathon demo.",
            },
        )

        progress.add_task(steps[6], total=None)
        browser_table = Table(title="Browser Observation + Vision")
        browser_table.add_column("Signal", style="cyan")
        browser_table.add_column("Value")
        browser_table.add_row("Tool", screenshot.name)
        browser_table.add_row("Status", "[green]ok[/green]" if screenshot.ok else f"[red]{screenshot.error}[/red]")
        browser_table.add_row("Source", str(screenshot.data.get("source", "unknown")))
        browser_table.add_row("Screenshot", str(screenshot.data.get("screenshot_path") or "not captured"))
        browser_table.add_row("Vision", _short(str(screenshot.data.get("vision") or "not available"), 240))
        console.print(browser_table)

        progress.add_task(steps[7], total=None)
        await harness.memory.add(
            MemoryRecord(
                text="Demo memory: ARIA can fetch browser pages, capture screenshots, run vision, and write reports.",
                metadata={"tool": "demo", "task": "hackathon"},
            )
        )
        memories = await harness.memory.search("ARIA browser screenshots vision reports", limit=3)
        console.print(_memory_table("Demo Memory Retrieval", memories))

        progress.add_task(steps[8], total=None)
        try:
            report = await harness.run_goal(task)
        finally:
            await harness.shutdown()

        progress.add_task(steps[9], total=None)

    summary = Table(title="Demo Summary")
    summary.add_column("Result", style="cyan")
    summary.add_column("Value")
    summary.add_row("Report", str(report.path))
    summary.add_row("Report size", f"{len(report.content)} characters")
    summary.add_row("Judge command", 'aria run "Research browser-use and produce a short report for ARIA"')
    console.print(summary)
    _success("Demo completed")
    return 0


def _config_table(settings: Settings) -> Table:
    table = Table(title="ARIA Configuration")
    table.add_column("Setting", style="cyan")
    table.add_column("Value")
    force_mock = os.getenv("ARIA_ALLOW_MOCK_BRAIN", "").lower() in {"1", "true", "yes"}
    provider = "Mock fallback" if force_mock else ("OpenAI" if settings.openai_api_key else "Mock fallback")
    table.add_row("Provider", provider)
    table.add_row("Model", settings.model)
    table.add_row("Memory backend", settings.memory_backend)
    table.add_row("Vision provider", "Anthropic" if settings.anthropic_api_key else "Mock fallback")
    table.add_row("Data directory", str(settings.data_dir))
    table.add_row("Reports directory", str(settings.reports_dir))
    table.add_row("Screenshots directory", str(settings.screenshots_dir))
    table.add_row("Environment", platform.platform())
    table.add_row("Configuration source", _config_source(settings))
    return table


async def config_check() -> int:
    console.print(_config_table(Settings.from_env()))
    _success("Configuration loaded without exposing secrets")
    return 0


def _brain_ready(settings: Settings) -> bool:
    if settings.openai_api_key:
        return True
    if os.getenv("ARIA_ALLOW_MOCK_BRAIN", "").lower() in {"1", "true", "yes"}:
        _warn("OPENAI_API_KEY is missing; continuing with MockBrain because ARIA_ALLOW_MOCK_BRAIN is enabled")
        return True

    console.print(
        Panel(
            "OPENAI_API_KEY is not configured.\n\n"
            "Run:\n"
            "  aria config set openai-api-key\n\n"
            "For offline testing only, set ARIA_ALLOW_MOCK_BRAIN=1 to use MockBrain.",
            title="ARIA setup required",
            border_style="yellow",
        )
    )
    return False


def config_set_openai_api_key() -> int:
    target = default_write_env_path()
    console.print(Panel.fit(f"Storing OpenAI API key in {target}", title="ARIA Config", border_style="cyan"))
    value = getpass.getpass("OpenAI API key: ").strip()
    if not value:
        _fail("No key entered")
        return 1
    write_env_value(target, "OPENAI_API_KEY", value)
    _success("OpenAI API key configured")
    console.print("[dim]The key was stored locally and was not printed.[/dim]")
    return 0


def config_set_openai_api_key_help() -> int:
    console.print(
        """usage: aria config set openai-api-key

Prompts securely for an OpenAI API key and stores it locally.

Storage:
  - .env in the current ARIA repo when run from the repository
  - ~/.config/aria/.env otherwise

The key is never printed."""
    )
    return 0


async def config_show() -> int:
    settings = Settings.from_env()
    table = Table(title="ARIA Config")
    table.add_column("Setting", style="cyan")
    table.add_column("Value")
    table.add_row("OpenAI key", "configured" if settings.openai_api_key else "missing")
    table.add_row("Model", settings.model)
    table.add_row("Memory backend", settings.memory_backend)
    table.add_row("Data dir", str(settings.data_dir))
    table.add_row("Vision provider", "Anthropic" if settings.anthropic_api_key else "Mock fallback")
    table.add_row("Configuration source", _config_source(settings))
    console.print(table)
    return 0


def _brain_table(harness: ARIAHarness) -> Table:
    assert harness.brain is not None
    table = Table(title="ARIA Brain")
    table.add_column("Signal", style="cyan")
    table.add_column("Value")
    table.add_row("Provider", harness.brain.provider)
    table.add_row("Model", harness.brain.model)
    table.add_row("API key", "configured" if harness.settings.openai_api_key else "not configured")
    table.add_row("Fallback", "none" if harness.brain.provider == "openai" else "MockBrain")
    return table


async def brain_check() -> int:
    harness = await ARIAHarness.from_settings(Settings.from_env()).initialize()
    try:
        console.print(_brain_table(harness))
        _success("Brain initialized")
    finally:
        await harness.shutdown()
    return 0


def _memory_table(title: str, records) -> Table:
    table = Table(title=title)
    table.add_column("#", style="cyan", justify="right")
    table.add_column("Tool")
    table.add_column("Text")
    for i, record in enumerate(records, start=1):
        table.add_row(str(i), str(record.metadata.get("tool", "-")), _short(record.text, 260))
    if not records:
        table.add_row("-", "-", "No matching memory records.")
    return table


async def memory_search(query: str) -> int:
    harness = await ARIAHarness.from_settings(Settings.from_env()).initialize()
    assert harness.memory is not None
    try:
        records = await harness.memory.search(query, limit=8)
    finally:
        await harness.shutdown()

    console.print(_memory_table(f"Memory Search: {query}", records))
    if records:
        _success(f"Found {len(records)} memory record(s)")
    else:
        _warn("No memory records matched the query")
    return 0


async def doctor() -> int:
    settings = Settings.from_env()
    rows: list[tuple[str, str, str]] = []

    def add(name: str, status: str, detail: str) -> None:
        color = {"PASS": "green", "WARN": "yellow", "FAIL": "red"}[status]
        rows.append((name, f"[{color}]{status}[/{color}]", detail))

    add("Python version", "PASS" if sys.version_info >= (3, 11) else "FAIL", platform.python_version())
    uv_path = shutil.which("uv")
    add("uv available", "PASS" if uv_path else "FAIL", uv_path or "uv not found on PATH")

    try:
        import playwright  # noqa: F401

        add("Playwright installed", "PASS", "python package import ok")
    except Exception as exc:
        add("Playwright installed", "FAIL", f"{type(exc).__name__}: {exc}")

    browser_detail = "not checked"
    browser_status = "FAIL"
    try:
        from playwright.async_api import async_playwright

        async with async_playwright() as p:
            executable = Path(p.chromium.executable_path)
            browser_detail = str(executable)
            browser_status = "PASS" if executable.exists() else "FAIL"
    except Exception as exc:
        browser_detail = f"{type(exc).__name__}: {exc}"
    add("Browser executable", browser_status, browser_detail)

    add("OPENAI_API_KEY", "PASS" if settings.openai_api_key else "WARN", "configured" if settings.openai_api_key else "missing; run aria config set openai-api-key")
    harness = await ARIAHarness.from_settings(settings).initialize()
    try:
        assert harness.brain is not None
        add("Brain provider", "PASS", f"{harness.brain.provider} / {harness.brain.model}")
    finally:
        await harness.shutdown()

    add("Memory backend", "PASS", settings.memory_backend)
    settings.reports_dir.mkdir(parents=True, exist_ok=True)
    settings.screenshots_dir.mkdir(parents=True, exist_ok=True)
    add("Reports directory", "PASS" if settings.reports_dir.exists() else "FAIL", str(settings.reports_dir))
    add("Screenshot directory", "PASS" if settings.screenshots_dir.exists() else "FAIL", str(settings.screenshots_dir))
    add("Configuration", "PASS", _config_source(settings))

    table = Table(title="ARIA Doctor")
    table.add_column("Check", style="cyan")
    table.add_column("Status")
    table.add_column("Detail")
    for row in rows:
        table.add_row(*row)
    console.print(table)

    failures = sum(1 for _, status, _ in rows if "FAIL" in status)
    warnings = sum(1 for _, status, _ in rows if "WARN" in status)
    if failures:
        _fail(f"Doctor found {failures} failure(s) and {warnings} warning(s)")
        return 1
    if warnings:
        _warn(f"Doctor found {warnings} warning(s)")
    else:
        _success("All doctor checks passed")
    return 0


def version() -> int:
    console.print(f"[bold cyan]aria[/bold cyan] {__version__}")
    return 0


def report_list() -> int:
    reports = _report_files()
    table = Table(title="ARIA Reports")
    table.add_column("#", justify="right", style="cyan")
    table.add_column("Path")
    table.add_column("Size")
    table.add_column("Modified")
    for i, path in enumerate(reports, start=1):
        modified = path.stat().st_mtime
        table.add_row(str(i), str(path), f"{path.stat().st_size} bytes", platform_time(modified))
    if not reports:
        table.add_row("-", "No reports found", "-", "-")
    console.print(table)
    return 0


def platform_time(timestamp: float) -> str:
    from datetime import datetime

    return datetime.fromtimestamp(timestamp).strftime("%Y-%m-%d %H:%M:%S")


def report_open_latest() -> int:
    reports = _report_files()
    if not reports:
        _fail("No reports found under reports/")
        return 1
    latest = reports[0].resolve()
    opened = webbrowser.open(latest.as_uri())
    if opened:
        _success(f"Opened {latest}")
    else:
        _warn(f"Could not confirm OS open; latest report is {latest}")
    return 0


class ARIAParser(argparse.ArgumentParser):
    def error(self, message: str) -> None:
        _fail(message)
        self.print_help()
        raise SystemExit(2)


def _help_parser() -> argparse.ArgumentParser:
    parser = ARIAParser(
        prog="aria",
        description="ARIA - Autonomous Reasoning & Interaction Agent",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""examples:
  aria demo
  aria run "Research browser-use and produce a short report for ARIA"
  aria youtube https://www.youtube.com/watch?v=t5F3RkDRzqA
  aria learn https://github.com/browser-use/browser-use
  aria config set openai-api-key
  aria config show
  aria config check
  aria brain check
  aria memory search "browser screenshots"
  aria doctor
  aria report list
  aria report open latest

Any unknown command is treated as a goal, so this still works:
  aria "Research browser-use and produce a short report for ARIA"
""",
    )
    subcommands = parser.add_argument_group("commands")
    subcommands.add_argument("command", nargs="?", help="goal text, demo, run, config, brain, memory, doctor, version, or report")
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
        return _run_async(run_demo())
    if command == "run":
        if not rest:
            parser.error("aria run requires a goal")
        return _run_async(run_task(" ".join(rest)))
    if command == "youtube":
        if not rest:
            parser.error("aria youtube requires a YouTube URL")
        return _run_async(run_task("youtube " + " ".join(rest)))
    if command == "learn":
        if not rest:
            parser.error("aria learn requires a URL or topic")
        return _run_async(run_task("learn " + " ".join(rest)))
    if command == "config" and rest == ["check"]:
        return _run_async(config_check())
    if command == "config" and rest == ["show"]:
        return _run_async(config_show())
    if command == "config" and rest == ["set", "openai-api-key"]:
        return config_set_openai_api_key()
    if command == "config" and rest == ["set", "openai-api-key", "--help"]:
        return config_set_openai_api_key_help()
    if command == "brain" and rest == ["check"]:
        return _run_async(brain_check())
    if command == "memory" and rest[:1] == ["search"] and len(rest) > 1:
        return _run_async(memory_search(" ".join(rest[1:])))
    if command == "doctor":
        return _run_async(doctor())
    if command == "version":
        return version()
    if command == "report" and rest == ["list"]:
        return report_list()
    if command == "report" and rest == ["open", "latest"]:
        return report_open_latest()
    if command in {"config", "brain", "memory", "report"}:
        parser.error(f"invalid {command!r} command")

    return _run_async(run_task(" ".join(argv)))


def _run_async(coro) -> int:
    loop = asyncio.new_event_loop()
    try:
        asyncio.set_event_loop(loop)
        return loop.run_until_complete(coro)
    finally:
        asyncio.set_event_loop(None)
        loop.close()


def app() -> None:
    code = main()
    sys.stdout.flush()
    sys.stderr.flush()
    _terminate_child_processes()
    os._exit(code)


def _terminate_child_processes() -> None:
    children: dict[int, list[int]] = {}
    try:
        for status in Path("/proc").glob("[0-9]*/status"):
            pid = int(status.parent.name)
            ppid = None
            for line in status.read_text(encoding="utf-8", errors="ignore").splitlines():
                if line.startswith("PPid:"):
                    ppid = int(line.split()[1])
                    break
            if ppid is not None:
                children.setdefault(ppid, []).append(pid)
    except Exception:
        return

    pending = list(children.get(os.getpid(), []))
    descendants: list[int] = []
    while pending:
        pid = pending.pop()
        descendants.append(pid)
        pending.extend(children.get(pid, []))

    for sig in (signal.SIGTERM, signal.SIGKILL):
        for pid in descendants:
            try:
                os.kill(pid, sig)
            except OSError:
                pass
