# backend/src/runtime/state.py
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


class TaskStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    DONE = "done"
    FAILED = "failed"


class RunStatus(str, Enum):
    PLANNING = "planning"
    RUNNING = "running"
    REFLECTING = "reflecting"
    DECIDING = "deciding"
    AWAITING_APPROVAL = "awaiting_approval"
    EXECUTING_WORKFLOW = "executing_workflow"
    DONE = "done"
    FAILED = "failed"
    REJECTED = "rejected"


@dataclass
class TaskSpec:
    id: str
    agent: str
    depends_on: list[str] = field(default_factory=list)
    priority: int = 1
    params: dict = field(default_factory=dict)


@dataclass
class TaskState:
    spec: TaskSpec
    status: TaskStatus = TaskStatus.PENDING
    attempts: int = 0
    result: dict | None = None
    error: str | None = None
    started_at: str | None = None
    finished_at: str | None = None
    latency_ms: float | None = None

    def to_dict(self) -> dict:
        return {
            "id": self.spec.id,
            "agent": self.spec.agent,
            "depends_on": self.spec.depends_on,
            "priority": self.spec.priority,
            "status": self.status.value,
            "attempts": self.attempts,
            "result": self.result,
            "error": self.error,
            "started_at": self.started_at,
            "finished_at": self.finished_at,
            "latency_ms": self.latency_ms,
        }


@dataclass
class RunState:
    goal: str
    district_id: int = 1
    run_id: str = field(default_factory=lambda: uuid.uuid4().hex[:12])
    status: RunStatus = RunStatus.PLANNING
    tasks: dict[str, TaskState] = field(default_factory=dict)
    context: dict = field(default_factory=dict)
    decision: dict | None = None
    workflow_steps: list[dict] = field(default_factory=list)
    timeline: list[dict] = field(default_factory=list)
    created_at: str = field(default_factory=_now_iso)
    decision_record_id: int | None = None

    def add_tasks(self, specs: list[TaskSpec]) -> None:
        for spec in specs:
            self.tasks[spec.id] = TaskState(spec=spec)

    def _deps_done(self, task: TaskState) -> bool:
        return all(
            dep in self.tasks and self.tasks[dep].status == TaskStatus.DONE
            for dep in task.spec.depends_on
        )

    def _deps_blocked(self, task: TaskState) -> bool:
        return any(
            dep not in self.tasks or self.tasks[dep].status == TaskStatus.FAILED
            or (self.tasks[dep].status == TaskStatus.PENDING and self._deps_blocked(self.tasks[dep]))
            for dep in task.spec.depends_on
        )

    def ready_tasks(self) -> list[TaskState]:
        return [
            t for t in self.tasks.values()
            if t.status == TaskStatus.PENDING and self._deps_done(t)
        ]

    def all_settled(self) -> bool:
        """True when no task can make further progress (done, failed, or blocked by a failed dep)."""
        for t in self.tasks.values():
            if t.status == TaskStatus.RUNNING:
                return False
            if t.status == TaskStatus.PENDING and not self._deps_blocked(t):
                return False
        return True

    def log(self, message: str, actor: str = "runtime") -> None:
        self.timeline.append({"ts": _now_iso(), "actor": actor, "message": message})

    def to_dict(self) -> dict:
        return {
            "run_id": self.run_id,
            "goal": self.goal,
            "district_id": self.district_id,
            "status": self.status.value,
            "tasks": [t.to_dict() for t in self.tasks.values()],
            "decision": self.decision,
            "workflow_steps": self.workflow_steps,
            "timeline": self.timeline,
            "created_at": self.created_at,
            "decision_record_id": self.decision_record_id,
            "reflection": self.context.get("reflection"),
        }

    def summary_dict(self) -> dict:
        return {
            "run_id": self.run_id,
            "goal": self.goal,
            "district_id": self.district_id,
            "status": self.status.value,
            "created_at": self.created_at,
            "task_count": len(self.tasks),
            "confidence": (self.decision or {}).get("confidence"),
        }


class RunStore:
    """Operational memory: in-process registry of runs, newest first."""

    def __init__(self):
        self._runs: dict[str, RunState] = {}

    def add(self, run: RunState) -> None:
        self._runs[run.run_id] = run

    def get(self, run_id: str) -> RunState | None:
        return self._runs.get(run_id)

    def list_recent(self, limit: int = 20) -> list[RunState]:
        return list(reversed(list(self._runs.values())))[:limit]


run_store = RunStore()
