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


from unittest.mock import AsyncMock
from src.services.decision_session_service import DecisionSessionService


@pytest.mark.asyncio
async def test_submit_goal_creates_decision_session(engine, monkeypatch):
    create_mock = AsyncMock()
    monkeypatch.setattr(DecisionSessionService, "create", create_mock)

    run = await engine.submit_goal("Reduce congestion", district_id=3)
    await engine.wait_for(run.run_id)

    create_mock.assert_awaited_once()
    _, call_args = create_mock.await_args
    assert call_args["run_id"] == run.run_id
    assert call_args["goal"] == "Reduce congestion"
    assert call_args["district_id"] == 3


@pytest.mark.asyncio
async def test_execute_marks_analyzing_then_recommend(engine, monkeypatch):
    analyzing_mock = AsyncMock()
    recommend_mock = AsyncMock()
    monkeypatch.setattr(DecisionSessionService, "mark_analyzing", analyzing_mock)
    monkeypatch.setattr(DecisionSessionService, "mark_recommend", recommend_mock)

    run = await engine.submit_goal("heavy rain", district_id=1)
    await engine.wait_for(run.run_id)

    analyzing_mock.assert_awaited_once()
    recommend_mock.assert_awaited_once()
    assert analyzing_mock.await_args[1]["run_id"] == run.run_id
    assert recommend_mock.await_args[1]["run_id"] == run.run_id


@pytest.mark.asyncio
async def test_decision_session_failure_does_not_break_the_run(engine, monkeypatch):
    monkeypatch.setattr(DecisionSessionService, "create", AsyncMock(side_effect=RuntimeError("db down")))

    run = await engine.submit_goal("heavy rain", district_id=1)
    await engine.wait_for(run.run_id)

    assert run.status == RunStatus.AWAITING_APPROVAL  # unaffected by the DecisionSession failure
