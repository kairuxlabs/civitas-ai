from src.agents.critic_agent import critic_agent
from src.agents.base import AgentState


def _state(confidence=80, flood_risk="low", evidence=None) -> AgentState:
    return AgentState(
        query="status", district_id=1, city_id="hanoi",
        weather_data={}, aqi_data={}, event_data=[], feedback_data=[],
        traffic_analysis="", environment_analysis="", event_analysis="",
        citizen_analysis="", knowledge_summary="",
        decision={"confidence": confidence, "prediction": {"flood_risk": flood_risk}},
        explanation=[], confidence=confidence,
        evidence=evidence if evidence is not None else [{"type": "sensor"}, {"type": "sensor"}],
        critic_notes=[],
    )


def test_critic_updates_decision_confidence_in_place():
    state = _state(confidence=80, flood_risk="high", evidence=[])
    result = critic_agent(state)
    assert result["decision"]["confidence"] < 80
    assert result["confidence"] == result["decision"]["confidence"]
    assert len(result["critic_notes"]) >= 1


def test_critic_no_notes_when_well_supported():
    state = _state(confidence=80, flood_risk="low")
    result = critic_agent(state)
    assert result["critic_notes"] == []
    assert result["decision"]["confidence"] == 80
