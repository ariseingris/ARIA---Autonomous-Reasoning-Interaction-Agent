from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class StepStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    DONE = "done"
    FAILED = "failed"
    SKIPPED = "skipped"


@dataclass
class PlanStep:
    id: int
    description: str
    tool_name: str
    args: dict[str, Any] = field(default_factory=dict)
    status: StepStatus = StepStatus.PENDING
    result: str | None = None


@dataclass
class Plan:
    task: str
    steps: list[PlanStep]

    def next_step(self) -> PlanStep | None:
        return next((step for step in self.steps if step.status == StepStatus.PENDING), None)

    def is_complete(self) -> bool:
        return all(step.status in {StepStatus.DONE, StepStatus.SKIPPED} for step in self.steps)
