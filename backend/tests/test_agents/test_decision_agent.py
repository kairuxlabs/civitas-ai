from unittest.mock import patch

from src.agents.decision_agent import decision_agent
from src.agents.base import AgentState


def _state(**evidence_fields) -> AgentState:
    state = AgentState(
        query="status", district_id=1, city_id="hanoi",
        weather_data={"rain": 0, "temperature": 30, "humidity": 70, "wind_speed": 5},
        aqi_data={"aqi_index": 100, "pm25": 50, "pm10": 80, "co": 1.0, "no2": 40},
        event_data=[], feedback_data=[],
        traffic_analysis="", environment_analysis="", event_analysis="",
        citizen_analysis="", knowledge_summary="", decision={}, explanation=[],
        confidence=0.0, evidence=[], critic_notes=[],
    )
    state.update(evidence_fields)
    return state


@patch("src.agents.decision_agent.call_gemini", return_value=None)
def test_gathers_evidence_from_all_five_fields(mock_gemini):
    state = _state(
        traffic_evidence=[{"id": "ev-traffic-1", "agent": "traffic"}],
        environment_evidence=[{"id": "ev-environment-1", "agent": "environment"}],
        event_evidence=[],
        citizen_evidence=[{"id": "ev-citizen-1", "agent": "citizen"}],
        knowledge_evidence=[{"id": "ev-knowledge-sop-1", "agent": "knowledge"}],
    )
    result = decision_agent(state)
    assert len(result["evidence"]) == 4
    assert [e["id"] for e in result["evidence"]] == ["ev-1", "ev-2", "ev-3", "ev-4"]
    assert [e["agent"] for e in result["evidence"]] == ["traffic", "environment", "citizen", "knowledge"]


@patch("src.agents.decision_agent.call_gemini", return_value=None)
def test_missing_evidence_fields_default_to_empty(mock_gemini):
    state = _state()  # no *_evidence keys set at all
    result = decision_agent(state)
    assert result["evidence"] == []
