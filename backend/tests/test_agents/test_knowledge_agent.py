from src.agents.knowledge_agent import knowledge_agent
from src.agents.base import AgentState


def _state(query: str, aqi: int = 100, rain: float = 0) -> AgentState:
    return AgentState(
        query=query,
        district_id=1,
        city_id="hanoi",
        weather_data={"temperature": 30, "humidity": 70, "rain": rain, "wind_speed": 5},
        aqi_data={"pm25": 50, "pm10": 80, "co": 1.0, "no2": 40, "aqi_index": aqi},
        event_data=[],
        feedback_data=[],
        traffic_analysis="",
        environment_analysis="",
        event_analysis="",
        citizen_analysis="",
        knowledge_summary="",
        decision={},
        explanation=[],
        confidence=0.0,
    )


def test_flood_sop_matched_on_heavy_rain():
    state = _state("What should we do?", rain=25.0)
    result = knowledge_agent(state)
    assert "knowledge_summary" in result
    assert "Flood" in result["knowledge_summary"] or "flood" in result["knowledge_summary"]


def test_aqi_sop_matched_on_hazardous_aqi():
    state = _state("What should we do?", aqi=160)
    result = knowledge_agent(state)
    assert "Air Quality" in result["knowledge_summary"] or "aqi" in result["knowledge_summary"].lower()


def test_no_match_returns_general_protocol():
    state = _state("What is the current status?", aqi=80, rain=0)
    result = knowledge_agent(state)
    assert "knowledge_summary" in result
    assert result["knowledge_summary"]  # non-empty


def test_keyword_in_query_triggers_match():
    state = _state("flood drainage needed", rain=0, aqi=90)
    result = knowledge_agent(state)
    assert "Flood" in result["knowledge_summary"]


def test_event_sop_matched_on_festival_query():
    state = _state("There is a festival today", rain=0, aqi=90)
    result = knowledge_agent(state)
    assert "Event" in result["knowledge_summary"] or "event" in result["knowledge_summary"].lower()


def test_returns_at_most_two_sops():
    # Heavy rain + high AQI → flood + aqi should both match
    state = _state("emergency situation", aqi=180, rain=30.0)
    result = knowledge_agent(state)
    # Summary should have "Relevant SOPs:" prefix with 2 entries
    summary = result["knowledge_summary"]
    if "Relevant SOPs:" in summary:
        # Count "; " separators — 2 SOPs means 1 separator
        assert summary.count("; [") <= 1
