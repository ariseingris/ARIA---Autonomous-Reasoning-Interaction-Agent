from __future__ import annotations

import re

from aria.tools.types import ToolResult

from .types import Plan, PlanStep, StepStatus


class ReActPlanner:
    """Small deterministic ReAct planner for the MVP.

    It emits explicit tool steps and updates step state from observations. A model
    planner can replace this class later without changing the agent loop.
    """

    def create_plan(self, task: str) -> Plan:
        urls = re.findall(r"https?://[^\s)]+", task)
        steps: list[PlanStep] = []

        if urls:
            for url in urls[:3]:
                steps.append(
                    PlanStep(
                        id=len(steps) + 1,
                        description=f"Fetch and extract architecture-relevant content from {url}",
                        tool_name="browser.fetch",
                        args={"url": url},
                    )
                )
        elif "browser-use" in task.lower():
            steps.append(
                PlanStep(
                    id=1,
                    description="Fetch browser-use repository README for public architecture signals",
                    tool_name="browser.fetch",
                    args={"url": "https://github.com/browser-use/browser-use"},
                )
            )
        else:
            steps.append(
                PlanStep(
                    id=1,
                    description="Search memory for relevant prior observations",
                    tool_name="memory.search",
                    args={"query": task, "limit": 5},
                )
            )

        steps.append(
            PlanStep(
                id=len(steps) + 1,
                description="Synthesize findings into a report",
                tool_name="report.write",
                args={},
            )
        )
        return Plan(task=task, steps=steps)

    def observe(self, step: PlanStep, result: ToolResult) -> None:
        step.result = result.content
        step.status = StepStatus.DONE if result.ok else StepStatus.FAILED
