# backend/src/runtime/scheduler.py
"""Scheduler: executes the task DAG in dependency waves (spec_v2 §5).

Ready tasks of each wave run concurrently; failures retry up to
max_retries, then the task is marked failed and its dependents stay
blocked. The scheduler only touches runtime state — business logic
lives in workers.
"""
import asyncio
import time

from src.runtime.event_bus import Event, EventBus, EventTypes
from src.runtime.state import RunState, TaskState, TaskStatus
from src.utils.logger import get_logger

logger = get_logger(__name__)


class Scheduler:
    def __init__(self, bus: EventBus, max_retries: int = 1, task_timeout_s: float = 45.0):
        self.bus = bus
        self.max_retries = max_retries
        self.task_timeout_s = task_timeout_s

    async def execute(self, run: RunState, workers: dict) -> None:
        while True:
            ready = run.ready_tasks()
            if not ready:
                if run.all_settled():
                    return
                # Nothing ready but not settled — should not happen with a valid DAG
                logger.warning(f"Scheduler stalled for run {run.run_id}")
                return
            ready.sort(key=lambda t: t.spec.priority)
            await asyncio.gather(*(self._run_task(run, task, workers) for task in ready))

    async def _run_task(self, run: RunState, task: TaskState, workers: dict) -> None:
        spec = task.spec
        worker = workers.get(spec.agent)
        task.status = TaskStatus.RUNNING
        task.started_at = _iso_now()
        await self._publish(run, EventTypes.TASK_STARTED, {"task": spec.id, "agent": spec.agent})
        run.log(f"Task {spec.id} started", actor="scheduler")

        while True:
            task.attempts += 1
            start = time.monotonic()
            try:
                if worker is None:
                    raise RuntimeError(f"No worker registered for agent '{spec.agent}'")
                result = await asyncio.wait_for(worker(run, spec), timeout=self.task_timeout_s)
                task.latency_ms = (time.monotonic() - start) * 1000
                task.result = result
                task.status = TaskStatus.DONE
                task.finished_at = _iso_now()
                run.log(f"Task {spec.id} done ({task.latency_ms:.0f}ms)", actor="scheduler")
                await self._publish(run, EventTypes.TASK_COMPLETED, {
                    "task": spec.id, "agent": spec.agent,
                    "latency_ms": task.latency_ms,
                    "summary": result.get("summary", "") if isinstance(result, dict) else "",
                })
                await self._publish(run, f"{spec.agent.upper()}_UPDATED", result if isinstance(result, dict) else {})
                return
            except Exception as e:
                task.latency_ms = (time.monotonic() - start) * 1000
                task.error = str(e)
                if task.attempts <= self.max_retries:
                    run.log(f"Task {spec.id} retrying: {e}", actor="scheduler")
                    await self._publish(run, EventTypes.TASK_RETRY, {
                        "task": spec.id, "agent": spec.agent, "error": str(e), "attempt": task.attempts,
                    })
                    continue
                task.status = TaskStatus.FAILED
                task.finished_at = _iso_now()
                run.log(f"Task {spec.id} failed: {e}", actor="scheduler")
                await self._publish(run, EventTypes.TASK_FAILED, {
                    "task": spec.id, "agent": spec.agent, "error": str(e),
                })
                return

    async def _publish(self, run: RunState, event_type: str, payload: dict) -> None:
        await self.bus.publish(Event(type=event_type, payload=payload, run_id=run.run_id, source="scheduler"))


def _iso_now() -> str:
    from datetime import datetime, timezone
    return datetime.now(timezone.utc).isoformat()
