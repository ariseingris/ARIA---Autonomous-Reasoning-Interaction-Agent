from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

from aria.planner.types import Plan


@dataclass
class Report:
    path: Path
    content: str


class ReportAgent:
    def __init__(self, reports_dir: Path) -> None:
        self.reports_dir = reports_dir
        self.reports_dir.mkdir(parents=True, exist_ok=True)

    async def write(self, task: str, plan: Plan, observations: list[str]) -> Report:
        stamp = datetime.utcnow().strftime("%Y%m%d-%H%M%S")
        path = self.reports_dir / f"aria-report-{stamp}.md"
        content = self._render(task, plan, observations)
        path.write_text(content, encoding="utf-8")
        return Report(path=path, content=content)

    def _render(self, task: str, plan: Plan, observations: list[str]) -> str:
        step_lines = "\n".join(
            f"- [{step.status.value}] {step.id}. {step.description} (`{step.tool_name}`)" for step in plan.steps
        )
        obs_sections = "\n\n".join(f"## Observation {i + 1}\n\n{obs[:5000]}" for i, obs in enumerate(observations))
        return (
            f"# ARIA Research Report\n\n"
            f"Task: {task}\n\n"
            f"## Execution Flow\n\n{step_lines}\n\n"
            f"## Findings\n\n{obs_sections or 'No observations collected.'}\n\n"
            "## ARIA Reusable Patterns\n\n"
            "- Use a bounded ReAct loop with explicit plan state.\n"
            "- Keep tool routing separate from agent reasoning.\n"
            "- Store observations immediately, then compact or retrieve memory for later turns.\n"
            "- Treat browser state as structured observations, not raw pages.\n"
            "- Convert failures into model-readable observations instead of crashing the loop.\n"
        )
