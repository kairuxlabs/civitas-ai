import asyncio

import pytest
from unittest.mock import AsyncMock

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
