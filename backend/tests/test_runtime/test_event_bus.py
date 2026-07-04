import pytest

from src.runtime.event_bus import Event, EventBus, EventTypes


@pytest.mark.asyncio
async def test_publish_reaches_subscriber():
    bus = EventBus()
    received = []

    async def handler(event: Event):
        received.append(event)

    bus.subscribe(EventTypes.TASK_STARTED, handler)
    await bus.publish(Event(type=EventTypes.TASK_STARTED, payload={"task": "weather"}))

    assert len(received) == 1
    assert received[0].payload["task"] == "weather"


@pytest.mark.asyncio
async def test_wildcard_receives_all_events():
    bus = EventBus()
    received = []

    async def handler(event: Event):
        received.append(event.type)

    bus.subscribe("*", handler)
    await bus.publish(Event(type=EventTypes.PLAN_CREATED, payload={}))
    await bus.publish(Event(type="WEATHER_UPDATED", payload={}))

    assert received == [EventTypes.PLAN_CREATED, "WEATHER_UPDATED"]


@pytest.mark.asyncio
async def test_handler_exception_does_not_break_publish():
    bus = EventBus()
    received = []

    async def broken(event: Event):
        raise RuntimeError("boom")

    async def ok(event: Event):
        received.append(event)

    bus.subscribe(EventTypes.DECISION_READY, broken)
    bus.subscribe(EventTypes.DECISION_READY, ok)
    await bus.publish(Event(type=EventTypes.DECISION_READY, payload={}))

    assert len(received) == 1


@pytest.mark.asyncio
async def test_history_records_events():
    bus = EventBus()
    await bus.publish(Event(type=EventTypes.GOAL_RECEIVED, payload={"goal": "rain"}, run_id="r1"))
    await bus.publish(Event(type=EventTypes.RUN_FINISHED, payload={}, run_id="r1"))

    assert [e.type for e in bus.history] == [EventTypes.GOAL_RECEIVED, EventTypes.RUN_FINISHED]
    assert bus.history[0].run_id == "r1"
    assert bus.history[0].ts  # timestamp auto-filled
