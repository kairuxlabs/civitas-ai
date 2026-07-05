import pytest

from src.runtime.engine import RuntimeEngine
from src.runtime.event_bus import EventTypes
from src.runtime.state import RunStatus
from src.utils.config import settings


@pytest.fixture
def engine(monkeypatch):
    # Force fallback paths: no LLM, no external stores
    monkeypatch.setattr(settings, "gemini_api_key", "")
    monkeypatch.setattr(settings, "qdrant_url", "")
    monkeypatch.setattr(settings, "neo4j_uri", "")
    return RuntimeEngine(broadcast_ws=False)


@pytest.mark.asyncio
async def test_goal_reaches_awaiting_approval_with_decision(engine):
    run = await engine.submit_goal("Prepare the city for tonight's heavy rain", district_id=1)
    await engine.wait_for(run.run_id)

    assert run.status == RunStatus.AWAITING_APPROVAL
    assert run.decision is not None
    assert {"summary", "prediction", "risk", "recommendation", "confidence", "evidence"} <= set(run.decision)
    assert any(t.spec.agent == "emergency" for t in run.tasks.values())
    types = [e.type for e in engine.bus.history]
    assert EventTypes.PLAN_CREATED in types
    assert EventTypes.DECISION_READY in types
    assert EventTypes.APPROVAL_NEEDED in types


@pytest.mark.asyncio
async def test_approve_executes_workflow_steps_in_order(engine):
    run = await engine.submit_goal("heavy rain", district_id=2)
    await engine.wait_for(run.run_id)

    resolved = await engine.resolve(run.run_id, approved=True)
    assert resolved.status == RunStatus.DONE
    step_names = [s["step"] for s in resolved.workflow_steps]
    assert step_names == ["notify", "create_incident", "store_memory", "done"]
    types = [e.type for e in engine.bus.history]
    assert EventTypes.WORKFLOW_FINISHED in types
    assert EventTypes.RUN_FINISHED in types


@pytest.mark.asyncio
async def test_reject_marks_run_rejected(engine):
    run = await engine.submit_goal("heavy rain", district_id=1)
    await engine.wait_for(run.run_id)

    resolved = await engine.resolve(run.run_id, approved=False)
    assert resolved.status == RunStatus.REJECTED
    assert resolved.workflow_steps == []


@pytest.mark.asyncio
async def test_resolve_unknown_run_returns_none(engine):
    assert await engine.resolve("nope", approved=True) is None


@pytest.mark.asyncio
async def test_context_overrides_reach_workers(engine):
    run = await engine.submit_goal(
        "heavy rain",
        district_id=1,
        context_overrides={"weather_data": {"temperature": 28, "humidity": 90, "rain": 80, "wind_speed": 20}},
    )
    await engine.wait_for(run.run_id)
    assert run.context["flood_risk"] == "high"
    assert run.decision["risk"] == "high"
