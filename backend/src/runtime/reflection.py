# backend/src/runtime/reflection.py
"""Reflection runtime: reviews task results after scheduling (spec_v2 §8).

Checks confidence, missing context and failures; may return follow-up
TaskSpecs (at most one reflection round per run).
"""
from src.runtime.event_bus import Event, EventBus, EventTypes
from src.runtime.state import RunState, TaskSpec, TaskStatus
from src.utils.logger import get_logger

logger = get_logger(__name__)

_LOW_CONFIDENCE = 0.5


class Reflection:
    def __init__(self, bus: EventBus):
        self.bus = bus

    async def review(self, run: RunState) -> list[TaskSpec]:
        already_reflected = run.context.get("_reflected", False)
        run.context["_reflected"] = True

        notes: list[str] = []
        missing: list[str] = []
        confidences: list[float] = []
        followups: list[TaskSpec] = []

        for task in run.tasks.values():
            if task.status == TaskStatus.FAILED:
                missing.append(task.spec.id)
                notes.append(f"Task {task.spec.id} failed: {task.error}")
                continue
            if task.status != TaskStatus.DONE or not isinstance(task.result, dict):
                continue
            conf = float(task.result.get("confidence", 0.5))
            confidences.append(conf)
            if conf < _LOW_CONFIDENCE:
                notes.append(f"Task {task.spec.id} low confidence ({conf:.2f})")

        knowledge_empty = not (run.context.get("knowledge_summary") or "").strip()
        if knowledge_empty and "knowledge" in {t.spec.agent for t in run.tasks.values()}:
            notes.append("Knowledge context missing — dispatching deep knowledge search")
            if not already_reflected:
                followups.append(TaskSpec(
                    id="knowledge_search", agent="knowledge",
                    params={"deep": True}, priority=1,
                ))

        avg_confidence = sum(confidences) / len(confidences) if confidences else 0.0
        run.context["reflection"] = {
            "avg_confidence": round(avg_confidence, 3),
            "notes": notes,
            "missing": missing,
        }
        run.log(
            f"Reflection: avg confidence {avg_confidence:.2f}, "
            f"{len(missing)} missing, {len(followups)} follow-up task(s)",
            actor="reflection",
        )
        await self.bus.publish(Event(
            type=EventTypes.REFLECTION_COMPLETED,
            payload=run.context["reflection"] | {"followups": [t.id for t in followups]},
            run_id=run.run_id,
            source="reflection",
        ))
        return [] if already_reflected else followups
