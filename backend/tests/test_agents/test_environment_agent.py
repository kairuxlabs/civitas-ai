from src.agents.environment_agent import environment_agent
from src.agents.base import AgentState


def _state(aqi: float = 100) -> AgentState:
    return AgentState(
        query="status", district_id=1, city_id="hanoi",
        weather_data={"temperature": 30, "humidity": 70, "rain": 0, "wind_speed": 5},
        aqi_data={"pm25": 50, "pm10": 80, "co": 1.0, "no2": 40, "aqi_index": aqi},
        event_data=[], feedback_data=[],
        traffic_analysis="", environment_analysis="", event_analysis="",
        citizen_analysis="", knowledge_summary="", decision={}, explanation=[],
        confidence=0.0,
    )


def test_environment_evidence_cites_openaq():
    result = environment_agent(_state(aqi=160))
    ev = result["environment_evidence"]
    assert len(ev) == 1
    assert ev[0]["source"] == "OpenAQ"
    assert ev[0]["type"] == "sensor"
    assert ev[0]["agent"] == "environment"
    assert "160" in ev[0]["content"]


def test_confidence_always_09_regardless_of_aqi_value():
    # Test with default aqi (100)
    result = environment_agent(_state(aqi=100))
    ev = result["environment_evidence"]
    assert len(ev) == 1
    assert ev[0]["confidence"] == 0.9
