from __future__ import annotations

from dataclasses import dataclass

from aria.agents import Report, ReportAgent, ResearchAgent
from aria.brain import Brain, BrainRequest, create_brain
from aria.browser import BrowserAgent, BrowserSession
from aria.config import Settings
from aria.memory import MemoryRecord, MemoryStore, create_memory
from aria.planner.react import ReActPlanner
from aria.tools.router import ToolRouter
from aria.vision.claude import ClaudeVisionClient


@dataclass
class ARIAHarness:
    settings: Settings
    brain: Brain | None = None
    planner: ReActPlanner | None = None
    router: ToolRouter | None = None
    browser: BrowserAgent | None = None
    vision: ClaudeVisionClient | None = None
    memory: MemoryStore | None = None
    research_agent: ResearchAgent | None = None
    reporter: ReportAgent | None = None

    @classmethod
    def from_settings(cls, settings: Settings | None = None) -> "ARIAHarness":
        return cls(settings=settings or Settings.from_env())

    async def initialize(self) -> "ARIAHarness":
        self.brain = create_brain(self.settings)
        self.planner = ReActPlanner()
        self.memory = create_memory(self.settings.memory_dir, self.settings.memory_backend)
        self.vision = ClaudeVisionClient(
            api_key=self.settings.anthropic_api_key,
            model=self.settings.vision_model,
        )
        self.browser = BrowserAgent(
            BrowserSession(headless=self.settings.headless),
            screenshots_dir=self.settings.screenshots_dir,
            vision=self.vision,
        )
        self.router = ToolRouter()
        self.router.register("browser.fetch", self.browser.fetch)
        self.router.register("browser.screenshot", self.browser.screenshot)
        self.router.register("memory.search", self._memory_search)
        self.router.register("report.write", self._report_placeholder)
        self.reporter = ReportAgent(self.settings.reports_dir)
        self.research_agent = ResearchAgent(
            self.settings,
            planner=self.planner,
            brain=self.brain,
            memory=self.memory,
            router=self.router,
            browser=self.browser,
            register_default_tools=False,
        )
        return self

    async def run_goal(self, goal: str) -> Report:
        if self.research_agent is None:
            await self.initialize()
        assert self.research_agent is not None
        report = await self.research_agent.run(goal)
        return await self.improve_report(report)

    async def save_observations(self, observations: list[str], metadata: dict[str, str] | None = None) -> None:
        if self.memory is None:
            await self.initialize()
        assert self.memory is not None
        for observation in observations:
            await self.memory.add(MemoryRecord(text=observation, metadata=metadata or {"source": "harness"}))

    async def generate_report(self, goal: str) -> Report:
        return await self.run_goal(goal)

    async def improve_report(self, report: Report) -> Report:
        if self.brain is None:
            await self.initialize()
        assert self.brain is not None
        if self.brain.provider != "openai":
            return report

        prompt = (
            "Improve this ARIA research report for a 2-minute hackathon demo. "
            "Keep it concise, preserve factual claims, and return only a short executive summary "
            "with 3 bullets for what the agent did.\n\n"
            f"{report.content[:12000]}"
        )
        try:
            observation_summary = await self.summarize_observations(report.content)
            next_action = await self.suggest_next_action(report.content)
            response = await self.brain.generate(
                BrainRequest(
                    system="You are ARIA's report polishing brain.",
                    prompt=prompt,
                )
            )
            improved = (
                f"{report.content}\n\n"
                "## OpenAI Brain Summary\n\n"
                f"Provider: {response.provider}\n\n"
                f"Model: {response.model}\n\n"
                f"{response.text.strip()}\n"
            )
            if observation_summary:
                improved += f"\n## OpenAI Observation Summary\n\n{observation_summary}\n"
            if next_action:
                improved += f"\n## OpenAI Suggested Next Action\n\n{next_action}\n"
        except Exception as exc:
            improved = (
                f"{report.content}\n\n"
                "## OpenAI Brain Summary\n\n"
                f"OpenAI report polish unavailable: {type(exc).__name__}: {exc}\n"
            )

        report.path.write_text(improved, encoding="utf-8")
        return Report(path=report.path, content=improved)

    async def summarize_observations(self, report_content: str) -> str | None:
        if self.brain is None:
            await self.initialize()
        assert self.brain is not None
        if self.brain.provider != "openai":
            return None

        response = await self.brain.generate(
            BrainRequest(
                system="You summarize ARIA tool observations for a research report.",
                prompt=(
                    "Summarize the observations in this report in 3 concise bullets. "
                    "Do not invent facts.\n\n"
                    f"{report_content[:10000]}"
                ),
            )
        )
        return response.text.strip()

    async def suggest_next_action(self, report_content: str) -> str | None:
        if self.brain is None:
            await self.initialize()
        assert self.brain is not None
        if self.brain.provider != "openai":
            return None

        response = await self.brain.generate(
            BrainRequest(
                system="You suggest one practical next action for ARIA after a completed run.",
                prompt=(
                    "Suggest exactly one next action for the agent after this report. "
                    "Keep it concrete and demo-safe.\n\n"
                    f"{report_content[:8000]}"
                ),
            )
        )
        return response.text.strip()

    async def shutdown(self) -> None:
        if self.memory is not None:
            await self.memory.close()

    async def _memory_search(self, query: str, limit: int = 5):
        assert self.memory is not None
        records = await self.memory.search(query, limit=limit)
        content = "\n\n".join(record.text for record in records) or "No matching memory records."
        from aria.tools.types import ToolResult

        return ToolResult(name="memory.search", ok=True, content=content)

    async def _report_placeholder(self):
        from aria.tools.types import ToolResult

        return ToolResult(name="report.write", ok=True, content="Report synthesis queued.")
