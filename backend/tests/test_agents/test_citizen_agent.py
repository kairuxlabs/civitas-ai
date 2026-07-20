from src.agents.citizen_agent import citizen_agent
from src.agents.base import AgentState


def _state(feedback: list) -> AgentState:
    return AgentState(
        query="status", district_id=1, city_id="hanoi",
        weather_data={}, aqi_data={}, event_data=[], feedback_data=feedback,
        traffic_analysis="", environment_analysis="", event_analysis="",
        citizen_analysis="", knowledge_summary="", decision={}, explanation=[],
        confidence=0.0,
    )


def test_no_feedback_produces_no_evidence():
    result = citizen_agent(_state([]))
    assert result["citizen_evidence"] == []


def test_feedback_produces_evidence():
    feedback = [
        {"category": "noise", "sentiment": "negative", "content": "too loud"},
        {"category": "traffic", "sentiment": "negative", "content": "jammed"},
    ]
    result = citizen_agent(_state(feedback))
    ev = result["citizen_evidence"]
    assert len(ev) == 1
    assert ev[0]["source"] == "CityOS Feedback DB"
    assert ev[0]["type"] == "feedback"
    assert ev[0]["agent"] == "citizen"
    assert "100" in ev[0]["content"] or "2" in ev[0]["content"]
