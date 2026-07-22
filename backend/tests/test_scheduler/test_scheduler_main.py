from unittest.mock import AsyncMock, MagicMock

import pytest

import src.scheduler.main as scheduler_main


class _FakeSessionCtx:
    """Minimal async-context-manager stand-in for AsyncSessionLocal()."""

    def __init__(self):
        self.session = MagicMock()

    async def __aenter__(self):
        return self.session

    async def __aexit__(self, *exc):
        return None


@pytest.mark.asyncio
async def test_run_all_step_failure_does_not_stop_other_steps(monkeypatch):
    calls = []

    monkeypatch.setattr(scheduler_main, "AsyncSessionLocal", lambda: _FakeSessionCtx())

    async def failing_weather(session):
        calls.append("weather")
        raise RuntimeError("open-meteo down")

    async def ok_aqi(session):
        calls.append("aqi")

    async def ok_feedback(session):
        calls.append("feedback")

    monkeypatch.setattr(scheduler_main.WeatherPipeline, "run", staticmethod(failing_weather))
    monkeypatch.setattr(scheduler_main.AQIPipeline, "run", staticmethod(ok_aqi))
    monkeypatch.setattr(scheduler_main.FeedbackPipeline, "run", staticmethod(ok_feedback))
    monkeypatch.setattr(scheduler_main.DistrictRepo, "get_all", AsyncMock(return_value=[]))

    # Must not raise even though WeatherPipeline.run() blows up.
    await scheduler_main.run_all()

    assert calls == ["weather", "aqi", "feedback"]


@pytest.mark.asyncio
async def test_run_all_per_district_score_failure_does_not_stop_others(monkeypatch):
    monkeypatch.setattr(scheduler_main, "AsyncSessionLocal", lambda: _FakeSessionCtx())
    monkeypatch.setattr(scheduler_main.WeatherPipeline, "run", AsyncMock())
    monkeypatch.setattr(scheduler_main.AQIPipeline, "run", AsyncMock())
    monkeypatch.setattr(scheduler_main.FeedbackPipeline, "run", AsyncMock())

    district_a = MagicMock(id=1)
    district_b = MagicMock(id=2)
    monkeypatch.setattr(
        scheduler_main.DistrictRepo, "get_all", AsyncMock(return_value=[district_a, district_b])
    )

    calls = []

    async def calc(session, district_id):
        calls.append(district_id)
        if district_id == 1:
            raise RuntimeError("no weather data yet")

    monkeypatch.setattr(scheduler_main.CityScoreService, "calculate_and_save", calc)

    # District 1's failure must not prevent district 2 from being scored.
    await scheduler_main.run_all()

    assert calls == [1, 2]


@pytest.mark.asyncio
async def test_main_survives_initial_run_all_failure(monkeypatch):
    """Regression test: previously `await run_all()` in main() was
    unwrapped, so a transient failure on the very first run killed the
    whole standalone scheduler process before it ever reached the idle
    wait loop."""
    monkeypatch.setattr(scheduler_main, "run_all", AsyncMock(side_effect=RuntimeError("boom")))

    fake_scheduler = MagicMock()
    monkeypatch.setattr(scheduler_main, "AsyncIOScheduler", MagicMock(return_value=fake_scheduler))
    monkeypatch.setattr(scheduler_main.knowledge_scheduler, "register", MagicMock())

    # Simulate the process receiving a shutdown signal as soon as it reaches
    # the idle wait, so the test doesn't hang.
    fake_event = MagicMock()
    fake_event.wait = AsyncMock(side_effect=SystemExit())
    monkeypatch.setattr(scheduler_main.asyncio, "Event", MagicMock(return_value=fake_event))

    # Must not raise: the initial run_all() failure is caught, and main()
    # proceeds to the idle loop and shuts down cleanly.
    await scheduler_main.main()

    fake_scheduler.shutdown.assert_called_once()
