import pytest

from src.runtime.event_bus import EventBus, EventTypes
from src.runtime.reflection import Reflection
from src.runtime.state import RunState, TaskSpec, TaskStatus


def _run_with_results(knowledge_summary: str) -> RunState:
    run = RunState(goal="heavy rain")
    run.add_tasks([
        TaskSpec(id="weather", agent="weather"),
        TaskSpec(id="knowledge", agent="knowledge"),
    ])
    run.tasks["weather"].status = TaskStatus.DONE
    run.tasks["weather"].result = {"summary": "rain", "confidence": 0.9}
    run.tasks["knowledge"].status = TaskStatus.DONE
    run.tasks["knowledge"].result = {"summary": knowledge_summary or "No relevant SOP found", "confidence": 0.3 if not knowledge_summary else 0.9}
    run.context["knowledge_summary"] = knowledge_summary
    return run


@pytest.mark.asyncio
async def test_reflection_injects_knowledge_followup_when_summary_empty():
    run = _run_with_results(knowledge_summary="")
    bus = EventBus()
    extra = await Reflection(bus).review(run)

    assert len(extra) == 1
    assert extra[0].agent == "knowledge"
    assert extra[0].params.get("deep") is True
    assert any(e.type == EventTypes.REFLECTION_COMPLETED for e in bus.history)
    assert "reflection" in run.context


@pytest.mark.asyncio
async def test_reflection_runs_only_once():
    run = _run_with_results(knowledge_summary="")
    reflection = Reflection(EventBus())
    first = await reflection.review(run)
    second = await reflection.review(run)
    assert first and not second


@pytest.mark.asyncio
async def test_reflection_no_followup_when_all_good():
    run = _run_with_results(knowledge_summary="Flood SOP: activate pumps")
    extra = await Reflection(EventBus()).review(run)
    assert extra == []
    assert run.context["reflection"]["avg_confidence"] >= 0.8


@pytest.mark.asyncio
async def test_reflection_notes_failed_tasks():
    run = _run_with_results(knowledge_summary="SOP ok")
    run.tasks["weather"].status = TaskStatus.FAILED
    run.tasks["weather"].error = "boom"
    await Reflection(EventBus()).review(run)
    assert "weather" in run.context["reflection"]["missing"]
