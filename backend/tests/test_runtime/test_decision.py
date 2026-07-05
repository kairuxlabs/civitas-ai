import pytest

import src.runtime.decision as decision_mod
from src.runtime.decision import make_decision
from src.runtime.event_bus import EventBus, EventTypes
from src.runtime.state import RunState, TaskSpec, TaskStatus

SPEC_KEYS = {"summary", "prediction", "risk", "recommendation", "confidence", "evidence"}


def _run() -> RunState:
    run = RunState(goal="Prepare for heavy rain")
    run.add_tasks([
        TaskSpec(id="weather", agent="weather"),
        TaskSpec(id="emergency", agent="emergency"),
    ])
    run.tasks["weather"].status = TaskStatus.DONE
    run.tasks["weather"].result = {"summary": "Rain 60mm/h — flood risk high", "flood_risk": "high", "confidence": 0.9}
    run.tasks["emergency"].status = TaskStatus.DONE
    run.tasks["emergency"].result = {"summary": "deploy 3 units", "readiness": "deploy", "confidence": 0.85}
    run.context.update({
        "flood_risk": "high",
        "weather_data": {"rain": 60},
        "aqi_data": {"aqi_index": 120},
        "knowledge_summary": "Flood SOP: activate pumps",
        "emergency": {"readiness": "deploy", "units": ["Đội bơm thoát nước"]},
        "reflection": {"avg_confidence": 0.85, "notes": [], "missing": []},
    })
    return run


@pytest.mark.asyncio
async def test_fallback_decision_has_spec_shape(monkeypatch):
    monkeypatch.setattr(decision_mod, "call_gemini", lambda *a, **k: None)
    bus = EventBus()
    run = _run()
    decision = await make_decision(run, bus)

    assert SPEC_KEYS <= set(decision)
    assert isinstance(decision["confidence"], (int, float))
    assert 0 <= decision["confidence"] <= 100
    assert isinstance(decision["evidence"], list) and len(decision["evidence"]) == 2
    assert decision["risk"] == "high"
    assert any(e.type == EventTypes.DECISION_READY for e in bus.history)


@pytest.mark.asyncio
async def test_gemini_decision_used_when_valid(monkeypatch):
    payload = (
        '{"summary": "s", "prediction": "p", "risk": "low",'
        ' "recommendation": ["r1"], "confidence": 88, "evidence": []}'
    )
    monkeypatch.setattr(decision_mod, "call_gemini", lambda *a, **k: payload)
    decision = await make_decision(_run(), EventBus())
    assert decision["summary"] == "s"
    assert decision["confidence"] == 88
    # evidence is always rebuilt from actual task results
    assert len(decision["evidence"]) == 2


@pytest.mark.asyncio
async def test_invalid_gemini_falls_back(monkeypatch):
    monkeypatch.setattr(decision_mod, "call_gemini", lambda *a, **k: '{"summary": "missing keys"}')
    decision = await make_decision(_run(), EventBus())
    assert SPEC_KEYS <= set(decision)
    assert decision["risk"] == "high"
