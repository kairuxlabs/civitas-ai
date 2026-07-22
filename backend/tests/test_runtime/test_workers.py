import pytest

from src.runtime.planner import AGENT_CATALOG
from src.runtime.state import RunState, TaskSpec
from src.runtime.workers import WORKERS, knowledge_worker, traffic_worker


def _make_run(rain: float = 0.0, aqi: float = 100.0) -> RunState:
    run = RunState(goal="test goal", district_id=1)
    run.context.update({
        "query": "test goal",
        "district_id": 1,
        "city_id": "hanoi",
        "weather_data": {"temperature": 30, "humidity": 70, "rain": rain, "wind_speed": 10},
        "aqi_data": {"pm25": 50, "pm10": 80, "co": 1.0, "no2": 40, "aqi_index": aqi},
        "event_data": [],
        "feedback_data": [],
    })
    return run


def test_every_catalog_agent_has_a_worker():
    assert set(WORKERS) == AGENT_CATALOG


@pytest.mark.asyncio
async def test_weather_worker_flood_risk_thresholds():
    # Thresholds come from src.reasoning.thresholds — shared with v1's
    # decision_agent so the same rain reading maps to the same flood_risk
    # regardless of which runtime handles the request (rain > 20 => high,
    # rain > 5 => medium, else low).
    for rain, expected in ((30, "high"), (10, "medium"), (2, "low")):
        run = _make_run(rain=rain)
        result = await WORKERS["weather"](run, TaskSpec(id="weather", agent="weather"))
        assert result["flood_risk"] == expected
        assert result["rain_level"] == rain
        assert 0 <= result["confidence"] <= 1


@pytest.mark.asyncio
async def test_emergency_worker_deploys_on_high_flood_risk():
    run = _make_run(rain=60)
    await WORKERS["weather"](run, TaskSpec(id="weather", agent="weather"))
    result = await WORKERS["emergency"](run, TaskSpec(id="emergency", agent="emergency"))
    assert result["readiness"] == "deploy"
    assert result["units"], "expected at least one unit recommendation"


@pytest.mark.asyncio
async def test_emergency_worker_normal_when_calm():
    run = _make_run(rain=0, aqi=50)
    await WORKERS["weather"](run, TaskSpec(id="weather", agent="weather"))
    result = await WORKERS["emergency"](run, TaskSpec(id="emergency", agent="emergency"))
    assert result["readiness"] == "normal"


@pytest.mark.asyncio
async def test_knowledge_worker_merges_summary_into_context():
    run = _make_run()
    result = await WORKERS["knowledge"](run, TaskSpec(id="knowledge", agent="knowledge"))
    assert "knowledge_summary" in run.context
    assert result["summary"]


@pytest.mark.asyncio
async def test_analytics_worker_aggregates_outputs():
    run = _make_run(rain=60, aqi=180)
    await WORKERS["weather"](run, TaskSpec(id="weather", agent="weather"))
    result = await WORKERS["analytics"](run, TaskSpec(id="analytics", agent="analytics"))
    assert result["flood_risk"] == "high"
    assert result["aqi_index"] == 180


@pytest.mark.asyncio
async def test_traffic_worker_forwards_evidence():
    run = RunState(goal="test")
    run.context["aqi_data"] = {"aqi_index": 180}
    run.context["weather_data"] = {"rain": 0}
    result = await traffic_worker(run, TaskSpec(id="t1", agent="traffic"))
    assert "evidence" in result
    assert len(result["evidence"]) == 1
    assert result["evidence"][0]["agent"] == "traffic"


@pytest.mark.asyncio
async def test_knowledge_worker_forwards_evidence(monkeypatch):
    from src.utils.config import settings
    monkeypatch.setattr(settings, "gemini_api_key", "")
    monkeypatch.setattr(settings, "openrouter_api_key", "")
    monkeypatch.setattr(settings, "qdrant_url", "")
    run = RunState(goal="flood emergency")
    run.context["query"] = "flood drainage needed"
    run.context["aqi_data"] = {}
    run.context["weather_data"] = {"rain": 25}
    result = await knowledge_worker(run, TaskSpec(id="k1", agent="knowledge"))
    assert "evidence" in result
    assert isinstance(result["evidence"], list)
