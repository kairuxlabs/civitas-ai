# backend/src/runtime/event_bus.py
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Awaitable, Callable

from src.utils.logger import get_logger

logger = get_logger(__name__)


class EventTypes:
    GOAL_RECEIVED = "GOAL_RECEIVED"
    PLAN_CREATED = "PLAN_CREATED"
    TASK_STARTED = "TASK_STARTED"
    TASK_COMPLETED = "TASK_COMPLETED"
    TASK_FAILED = "TASK_FAILED"
    TASK_RETRY = "TASK_RETRY"
    REFLECTION_COMPLETED = "REFLECTION_COMPLETED"
    DECISION_READY = "DECISION_READY"
    APPROVAL_NEEDED = "APPROVAL_NEEDED"
    WORKFLOW_STEP = "WORKFLOW_STEP"
    WORKFLOW_FINISHED = "WORKFLOW_FINISHED"
    RUN_FINISHED = "RUN_FINISHED"


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


@dataclass
class Event:
    type: str
    payload: dict
    source: str = "runtime"
    run_id: str | None = None
    ts: str = field(default_factory=_now_iso)


Handler = Callable[[Event], Awaitable[None]]


class EventBus:
    """Async pub/sub bus. Subscribe with an event type or "*" for all events."""

    def __init__(self):
        self._subscribers: dict[str, list[Handler]] = {}
        self.history: list[Event] = []

    def subscribe(self, event_type: str, handler: Handler) -> None:
        self._subscribers.setdefault(event_type, []).append(handler)

    async def publish(self, event: Event) -> None:
        self.history.append(event)
        handlers = self._subscribers.get(event.type, []) + self._subscribers.get("*", [])
        for handler in handlers:
            try:
                await handler(event)
            except Exception as e:
                logger.warning(f"Event handler failed for {event.type}: {e}")
