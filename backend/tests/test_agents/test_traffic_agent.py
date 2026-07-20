from src.agents.traffic_agent import traffic_agent
from src.agents.base import AgentState


def _state(aqi: float = 100, rain: float = 0) -> AgentState:
    return AgentState(
        query="status", district_id=1, city_id="hanoi",
        weather_data={"temperature": 30, "humidity": 70, "rain": rain, "wind_speed": 5},
        aqi_data={"pm25": 50, "pm10": 80, "co": 1.0, "no2": 40, "aqi_index": aqi},
        event_data=[], feedback_data=[],
        traffic_analysis="", environment_analysis="", event_analysis="",
        citizen_analysis="", knowledge_summary="", decision={}, explanation=[],
        confidence=0.0,
    )


def test_high_aqi_produces_openaq_evidence():
    result = traffic_agent(_state(aqi=180, rain=0))
    ev = result["traffic_evidence"]
    assert len(ev) == 1
    assert ev[0]["source"] == "OpenAQ"
    assert ev[0]["type"] == "sensor"
    assert ev[0]["agent"] == "traffic"
    assert ev[0]["confidence"] == 0.9


def test_heavy_rain_produces_open_meteo_evidence():
    result = traffic_agent(_state(aqi=90, rain=15))
    ev = result["traffic_evidence"]
    assert len(ev) == 1
    assert ev[0]["source"] == "Open-Meteo"


def test_fallback_defaults_produce_lower_confidence():
    result = traffic_agent(_state())
    ev = result["traffic_evidence"]
    assert len(ev) == 1
    assert ev[0]["confidence"] == 0.5
