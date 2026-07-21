import asyncio

import pytest
from unittest.mock import AsyncMock, MagicMock

from src.runtime.event_bus import EventBus
from src.runtime.state import RunState, RunStatus
from src.runtime.workflow import WorkflowRuntime
from src.runtime import workflow as workflow_module


@pytest.mark.asyncio
async def test_resolve_rejected_calls_store_chain_off_the_event_loop_thread(monkeypatch):
    bus = EventBus()
    runtime = WorkflowRuntime(bus)
    run = RunState(goal="test goal", district_id=1, run_id="r1")
    run.status = RunStatus.AWAITING_APPROVAL
    run.decision = {"risk": "low", "confidence": 80}

    result_holder = {}

    def fake_store_chain(**kwargs):
        try:
            asyncio.get_running_loop()
            result_holder["called_on_loop_thread"] = True
        except RuntimeError:
            result_holder["called_on_loop_thread"] = False

    monkeypatch.setattr(workflow_module.decision_memory, "store_chain", fake_store_chain)
    monkeypatch.setattr(runtime, "_update_persisted", AsyncMock())

    await runtime.resolve(run, approved=False)

    assert result_holder["called_on_loop_thread"] is False


@pytest.mark.asyncio
async def test_resolve_approved_calls_store_chain_off_the_event_loop_thread(monkeypatch):
    bus = EventBus()
    runtime = WorkflowRuntime(bus)
    run = RunState(goal="test goal", district_id=1, run_id="r2")
    run.status = RunStatus.AWAITING_APPROVAL
    run.decision = {"risk": "high", "confidence": 90}

    result_holder = {}

    def fake_store_chain(**kwargs):
        try:
            asyncio.get_running_loop()
            result_holder["called_on_loop_thread"] = True
        except RuntimeError:
            result_holder["called_on_loop_thread"] = False

    monkeypatch.setattr(workflow_module.decision_memory, "store_chain", fake_store_chain)
    monkeypatch.setattr(runtime, "_update_persisted", AsyncMock())

    await runtime.resolve(run, approved=True)

    assert result_holder["called_on_loop_thread"] is False


from src.services.decision_session_service import DecisionSessionService, DECISION_OBSERVE_DELAY_MIN
from src.scheduler.registry import scheduler as shared_scheduler


@pytest.mark.asyncio
async def test_start_marks_session_awaiting_approval(monkeypatch):
    bus = EventBus()
    runtime = WorkflowRuntime(bus)
    run = RunState(goal="test goal", district_id=1, run_id="wf-1")
    run.decision = {"risk": "low", "confidence": 80, "recommendation": []}

    monkeypatch.setattr(runtime, "_persist_decision", AsyncMock())
    mark_mock = AsyncMock()
    monkeypatch.setattr(DecisionSessionService, "mark_awaiting_approval", mark_mock)

    await runtime.start(run)

    mark_mock.assert_awaited_once()
    assert mark_mock.await_args[1]["run_id"] == "wf-1"


@pytest.mark.asyncio
async def test_resolve_rejected_marks_session_rejected(monkeypatch):
    bus = EventBus()
    runtime = WorkflowRuntime(bus)
    run = RunState(goal="test goal", district_id=1, run_id="wf-2")
    run.status = RunStatus.AWAITING_APPROVAL
    run.decision = {"risk": "low", "confidence": 80}

    monkeypatch.setattr(workflow_module.decision_memory, "store_chain", lambda **kw: None)
    monkeypatch.setattr(runtime, "_update_persisted", AsyncMock())
    reject_mock = AsyncMock()
    monkeypatch.setattr(DecisionSessionService, "mark_rejected", reject_mock)

    await runtime.resolve(run, approved=False)

    reject_mock.assert_awaited_once()
    assert reject_mock.await_args[1]["run_id"] == "wf-2"


@pytest.mark.asyncio
async def test_resolve_approved_marks_session_approved_and_schedules_observe(monkeypatch):
    bus = EventBus()
    runtime = WorkflowRuntime(bus)
    run = RunState(goal="test goal", district_id=1, run_id="wf-3")
    run.status = RunStatus.AWAITING_APPROVAL
    run.decision = {"risk": "high", "confidence": 90}

    monkeypatch.setattr(workflow_module.decision_memory, "store_chain", lambda **kw: None)
    monkeypatch.setattr(runtime, "_update_persisted", AsyncMock())

    fake_session = MagicMock(id=123, run_id="wf-3")
    approve_mock = AsyncMock(return_value=fake_session)
    monkeypatch.setattr(DecisionSessionService, "mark_approved", approve_mock)
    add_job_mock = MagicMock()
    monkeypatch.setattr(shared_scheduler, "add_job", add_job_mock)

    await runtime.resolve(run, approved=True)

    approve_mock.assert_awaited_once()
    assert approve_mock.await_args[1]["run_id"] == "wf-3"
    add_job_mock.assert_called_once()
    _, kwargs = add_job_mock.call_args
    assert kwargs["id"] == "observe_session_123"
    assert kwargs["args"] == [123]
