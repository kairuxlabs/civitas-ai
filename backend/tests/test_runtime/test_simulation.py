import asyncio

import pytest

from src.simulation.engine import SimulationEngine
from src.simulation.profiles import PROFILES


def _engine(**kwargs) -> SimulationEngine:
    """Engine with all external effects stubbed out."""
    calls = []

    async def submit_goal(goal, district_id=1, context_overrides=None):
        calls.append({"goal": goal, "district_id": district_id, "overrides": context_overrides})

    async def broadcast(data):
        pass

    eng = SimulationEngine(
        submit_goal=kwargs.get("submit_goal", submit_goal),
        broadcast=broadcast,
        persist=False,
    )
    eng._goal_calls = calls  # test helper
    return eng


def test_profiles_cover_expected_scenarios():
    assert {"normal", "heavy_rain", "air_pollution", "heatwave", "major_event"} <= set(PROFILES)


@pytest.mark.asyncio
async def test_values_drift_into_profile_range():
    eng = _engine()
    await eng.start("heavy_rain", interval_s=999, auto_goal=False)
    await eng.stop()
    for _ in range(30):
        snapshot = await eng.tick()
    profile = PROFILES["heavy_rain"]
    assert profile.rain_range[0] * 0.5 <= snapshot["rain"] <= profile.rain_range[1] * 1.2
    assert snapshot["aqi"] >= 0
    assert snapshot["tick"] == 30


@pytest.mark.asyncio
async def test_auto_goal_triggers_over_threshold_with_cooldown():
    eng = _engine()
    await eng.start("heavy_rain", interval_s=999, auto_goal=True)
    await eng.stop()
    eng.auto_goal_cooldown_s = 9999
    for _ in range(40):
        await eng.tick()
    assert len(eng._goal_calls) == 1, "cooldown must prevent repeated auto-goals"
    call = eng._goal_calls[0]
    assert "mưa" in call["goal"].lower() or "mô phỏng" in call["goal"].lower()
    assert call["overrides"]["weather_data"]["rain"] > 20


@pytest.mark.asyncio
async def test_heatwave_auto_goal_triggers_on_temperature_not_rain_or_aqi():
    eng = _engine()
    await eng.start("heatwave", interval_s=999, auto_goal=True)
    await eng.stop()
    eng.auto_goal_cooldown_s = 9999
    for _ in range(40):
        await eng.tick()
    assert len(eng._goal_calls) == 1
    call = eng._goal_calls[0]
    assert "nắng nóng" in call["goal"].lower()
    # The trigger condition checks the unrounded value (must be strictly > 38);
    # the overrides carry a value rounded to 1 decimal, which can display as
    # exactly 38.0 even when the raw reading was e.g. 38.04 — so >= here,
    # not >, to avoid a rounding-induced flake.
    assert call["overrides"]["weather_data"]["temperature"] >= 38


@pytest.mark.asyncio
async def test_major_event_auto_goal_triggers_via_event_chance_not_weather():
    eng = _engine()
    await eng.start("major_event", interval_s=999, auto_goal=True)
    await eng.stop()
    eng.auto_goal_cooldown_s = 9999
    for _ in range(60):
        await eng.tick()
    assert len(eng._goal_calls) == 1
    call = eng._goal_calls[0]
    assert "an ninh" in call["goal"].lower() or "sự kiện" in call["goal"].lower()
    # major_event's rain/AQI ranges never cross the flood/pollution thresholds,
    # proving the trigger came from event_chance, not a weather reading.
    assert call["overrides"]["weather_data"]["rain"] < 20
    assert call["overrides"]["aqi_data"]["aqi_index"] < 150


@pytest.mark.asyncio
async def test_no_auto_goal_when_disabled_or_calm():
    eng = _engine()
    await eng.start("heavy_rain", interval_s=999, auto_goal=False)
    await eng.stop()
    for _ in range(40):
        await eng.tick()
    assert eng._goal_calls == []

    eng2 = _engine()
    await eng2.start("normal", interval_s=999, auto_goal=True)
    await eng2.stop()
    for _ in range(20):
        await eng2.tick()
    assert eng2._goal_calls == []


@pytest.mark.asyncio
async def test_start_stop_idempotent_and_status_shape():
    eng = _engine()
    status = await eng.start("air_pollution", interval_s=60, auto_goal=True)
    assert status["running"] is True
    assert status["scenario"] == "air_pollution"

    # restart with another scenario replaces the loop
    status = await eng.start("heatwave", interval_s=60)
    assert status["scenario"] == "heatwave"

    status = await eng.stop()
    assert status["running"] is False
    status = await eng.stop()  # second stop is a no-op
    assert status["running"] is False
    assert {"running", "scenario", "interval_s", "auto_goal", "district_id", "tick", "values", "last_auto_goal"} <= set(eng.status())


@pytest.mark.asyncio
async def test_auto_goal_targets_the_district_selected_at_start():
    eng = _engine()
    await eng.start("heavy_rain", interval_s=999, auto_goal=True, district_id=7)
    await eng.stop()
    eng.auto_goal_cooldown_s = 9999
    for _ in range(40):
        await eng.tick()
    assert len(eng._goal_calls) == 1
    assert eng._goal_calls[0]["district_id"] == 7
    assert eng.status()["district_id"] == 7


@pytest.mark.asyncio
async def test_unknown_scenario_raises():
    eng = _engine()
    with pytest.raises(ValueError):
        await eng.start("zombie_apocalypse")


@pytest.mark.asyncio
async def test_background_loop_ticks():
    eng = _engine()
    await eng.start("normal", interval_s=0.02, auto_goal=False)
    await asyncio.sleep(0.15)
    await eng.stop()
    assert eng.status()["tick"] >= 2
