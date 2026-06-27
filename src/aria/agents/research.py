from __future__ import annotations

from aria.browser import BrowserAgent, BrowserSession
from aria.config import Settings
from aria.memory import MemoryRecord, MemoryStore, create_memory
from aria.planner.react import ReActPlanner
from aria.planner.types import StepStatus
from aria.tools.router import ToolRouter
from aria.tools.types import ToolResult
from aria.vision.claude import ClaudeVisionClient

from .report import Report, ReportAgent


class ResearchAgent:
    def __init__(
        self,
        settings: Settings,
        planner: ReActPlanner | None = None,
        memory: MemoryStore | None = None,
        router: ToolRouter | None = None,
        register_default_tools: bool = True,
    ) -> None:
        self.settings = settings
        self.planner = planner or ReActPlanner()
        self.memory = memory or create_memory(settings.memory_dir, settings.memory_backend)
        self.router = router or ToolRouter()
        self.reporter = ReportAgent(settings.reports_dir)
        if register_default_tools:
            self._register_tools()

    def _register_tools(self) -> None:
        vision = ClaudeVisionClient(api_key=self.settings.anthropic_api_key, model=self.settings.vision_model)
        browser = BrowserAgent(
            BrowserSession(headless=self.settings.headless),
            screenshots_dir=self.settings.screenshots_dir,
            vision=vision,
        )
        self.router.register("browser.fetch", browser.fetch)
        self.router.register("browser.screenshot", browser.screenshot)
        self.router.register("memory.search", self._memory_search)
        self.router.register("report.write", self._report_placeholder)

    async def _memory_search(self, query: str, limit: int = 5) -> ToolResult:
        records = await self.memory.search(query, limit=limit)
        content = "\n\n".join(record.text for record in records) or "No matching memory records."
        return ToolResult(name="memory.search", ok=True, content=content)

    async def _report_placeholder(self) -> ToolResult:
        return ToolResult(name="report.write", ok=True, content="Report synthesis queued.")

    async def run(self, task: str) -> Report:
        plan = self.planner.create_plan(task)
        observations: list[str] = []
        failures = 0

        while not plan.is_complete() and len(observations) < self.settings.max_steps:
            step = plan.next_step()
            if step is None:
                break

            step.status = StepStatus.RUNNING
            result = await self.router.execute(step.tool_name, step.args)
            self.planner.observe(step, result)

            if result.ok:
                observations.append(result.content)
                await self.memory.add(
                    MemoryRecord(
                        text=result.content,
                        metadata={"tool": result.name, "task": task[:200]},
                    )
                )
            else:
                failures += 1
                observations.append(f"Failure in {step.tool_name}: {result.content}")
                if failures >= self.settings.max_failures:
                    break

        return await self.reporter.write(task, plan, observations)

    async def close(self) -> None:
        await self.memory.close()
