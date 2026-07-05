import asyncio

import pytest

from src.runtime.event_bus import EventBus, EventTypes
from src.runtime.scheduler import Scheduler
from src.runtime.state import RunState, TaskSpec, TaskStatus


def _make_run(specs: list[TaskSpec]) -> RunState:
    run = RunState(goal="test")
    run.add_tasks(specs)
    return run


@pytest.mark.asyncio
async def test_dependency_order_and_completion():
    order: list[str] = []

    async def recorder(run, spec):
        order.append(spec.id)
        return {"summary": "ok", "confidence": 1.0}

    workers = {"weather": recorder, "traffic": recorder}
    run = _make_run([
        TaskSpec(id="traffic", agent="traffic", depends_on=["weather"]),
        TaskSpec(id="weather", agent="weather"),
    ])
    await Scheduler(EventBus()).execute(run, workers)

    assert order == ["weather", "traffic"]
    assert all(t.status == TaskStatus.DONE for t in run.tasks.values())


@pytest.mark.asyncio
async def test_independent_tasks_run_concurrently():
    running = 0
    max_running = 0

    async def slow(run, spec):
        nonlocal running, max_running
        running += 1
        max_running = max(max_running, running)
        await asyncio.sleep(0.05)
        running -= 1
        return {"summary": "ok", "confidence": 1.0}

    workers = {"weather": slow, "knowledge": slow}
    run = _make_run([
        TaskSpec(id="weather", agent="weather"),
        TaskSpec(id="knowledge", agent="knowledge"),
    ])
    await Scheduler(EventBus()).execute(run, workers)
    assert max_running == 2


@pytest.mark.asyncio
async def test_flaky_worker_succeeds_on_retry():
    calls = {"n": 0}

    async def flaky(run, spec):
        calls["n"] += 1
        if calls["n"] == 1:
            raise RuntimeError("transient")
        return {"summary": "recovered", "confidence": 1.0}

    bus = EventBus()
    run = _make_run([TaskSpec(id="weather", agent="weather")])
    await Scheduler(bus, max_retries=1).execute(run, {"weather": flaky})

    assert run.tasks["weather"].status == TaskStatus.DONE
    assert run.tasks["weather"].attempts == 2
    assert any(e.type == EventTypes.TASK_RETRY for e in bus.history)


@pytest.mark.asyncio
async def test_permanent_failure_marks_failed_and_skips_dependents():
    async def broken(run, spec):
        raise RuntimeError("always broken")

    async def never(run, spec):  # pragma: no cover - must not run
        raise AssertionError("dependent should not run")

    bus = EventBus()
    run = _make_run([
        TaskSpec(id="weather", agent="weather"),
        TaskSpec(id="traffic", agent="traffic", depends_on=["weather"]),
    ])
    await Scheduler(bus, max_retries=1).execute(run, {"weather": broken, "traffic": never})

    assert run.tasks["weather"].status == TaskStatus.FAILED
    assert run.tasks["traffic"].status == TaskStatus.PENDING
    assert run.all_settled()
    assert any(e.type == EventTypes.TASK_FAILED for e in bus.history)


@pytest.mark.asyncio
async def test_events_published_and_latency_recorded():
    async def ok(run, spec):
        return {"summary": "ok", "confidence": 1.0}

    bus = EventBus()
    run = _make_run([TaskSpec(id="weather", agent="weather")])
    await Scheduler(bus).execute(run, {"weather": ok})

    types = [e.type for e in bus.history]
    assert EventTypes.TASK_STARTED in types
    assert EventTypes.TASK_COMPLETED in types
    assert "WEATHER_UPDATED" in types
    assert run.tasks["weather"].latency_ms is not None
