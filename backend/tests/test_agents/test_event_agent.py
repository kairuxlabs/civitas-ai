from src.agents.event_agent import event_agent
from src.agents.base import AgentState


def _state(events: list) -> AgentState:
    return AgentState(
        query="status", district_id=1, city_id="hanoi",
        weather_data={}, aqi_data={}, event_data=events, feedback_data=[],
        traffic_analysis="", environment_analysis="", event_analysis="",
        citizen_analysis="", knowledge_summary="", decision={}, explanation=[],
        confidence=0.0,
    )


def test_no_events_produces_no_evidence():
    result = event_agent(_state([]))
    assert result["event_evidence"] == []


def test_high_impact_events_produce_evidence():
    events = [
        {"title": "Marathon", "category": "sport", "impact_level": "high"},
        {"title": "Concert", "category": "music", "impact_level": "high"},
    ]
    result = event_agent(_state(events))
    ev = result["event_evidence"]
    assert len(ev) == 2
    assert all(e["source"] == "CityOS Events DB" for e in ev)
    assert all(e["type"] == "event" for e in ev)
    assert all(e["agent"] == "event" for e in ev)


def test_max_three_event_evidence_items():
    events = [{"title": f"E{i}", "category": "x", "impact_level": "high"} for i in range(5)]
    result = event_agent(_state(events))
    assert len(result["event_evidence"]) == 3
