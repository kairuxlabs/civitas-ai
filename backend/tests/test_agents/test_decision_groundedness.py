"""Regression tests verifying the v1 decision pipeline (knowledge_agent +
decision_agent) stays grounded in the static SOP knowledge base.

Three groups, in three tasks of the same implementation plan:
1. Retrieval correctness — knowledge_agent picks the right SOP per scenario.
2. Grounding-input check — decision_agent's LLM prompt includes the retrieved
   SOP summary (added in Task 2).
3. Fallback-alignment — the rule-based safety-net decision recommends
   actions matching the SOP's intent (added in Task 3).

All tests are fully offline: no real Gemini/OpenRouter calls are made.
"""
from src.agents.base import AgentState
from src.agents.knowledge_agent import knowledge_agent


def _state(
    query: str,
    aqi: float = 100,
    rain: float = 0,
    temperature: float = 30,
    event_analysis: str = "",
    citizen_analysis: str = "",
) -> AgentState:
    return AgentState(
        query=query,
        district_id=1,
        city_id="hanoi",
        weather_data={"temperature": temperature, "humidity": 70, "rain": rain, "wind_speed": 5},
        aqi_data={"pm25": 50, "pm10": 80, "co": 1.0, "no2": 40, "aqi_index": aqi},
        event_data=[],
        feedback_data=[],
        traffic_analysis="",
        environment_analysis="",
        event_analysis=event_analysis,
        citizen_analysis=citizen_analysis,
        knowledge_summary="",
        decision={},
        explanation=[],
        confidence=0.0,
    )


# Each scenario is designed to trigger exactly one SOP match (or none, for
# "baseline"), verified against the live thresholds/keywords in
# src/agents/knowledge_agent.py (see Step 1). "sop_title" is the exact
# substring expected in knowledge_agent's returned knowledge_summary.
# "fallback_keyword" is the concept-level keyword(s) Task 3 will look for in
# _rule_based_decision's output (None where no scenario-specific recommendation
# exists in the rule-based fallback — see Task 3, Step 1 for why).
SCENARIOS = {
    "flood": {
        "state": _state("Tình hình hiện tại thế nào?", rain=25),
        "sop_title": "Flood Emergency SOP",
        "fallback_keyword": "thoát nước",
    },
    "aqi": {
        "state": _state("Tình hình hiện tại thế nào?", aqi=180),
        "sop_title": "Air Quality Emergency SOP",
        "fallback_keyword": "khuyến cáo sức khỏe",
    },
    "heatwave": {
        "state": _state("Tình hình hiện tại thế nào?", temperature=39),
        "sop_title": "Heatwave Response SOP",
        "fallback_keyword": "điểm mát",
    },
    "traffic": {
        "state": _state("Tắc đường nghiêm trọng ở khu vực trung tâm, cần làm gì?"),
        "sop_title": "Traffic Congestion Management SOP",
        "fallback_keyword": None,  # no traffic-specific branch in _rule_based_decision — see Task 3
    },
    "event": {
        "state": _state(
            "Có sự kiện đông người sắp diễn ra, cần chuẩn bị gì?",
            event_analysis="1 HIGH-impact event(s) may cause disruptions: Concert",
        ),
        "sop_title": "Mass Event Management SOP",
        "fallback_keyword": "an ninh",
    },
    "baseline": {
        "state": _state("Tình hình hiện tại thế nào?"),
        "sop_title": None,
        "fallback_keyword": None,
    },
}


def test_flood_scenario_retrieves_flood_sop():
    result = knowledge_agent(SCENARIOS["flood"]["state"])
    assert SCENARIOS["flood"]["sop_title"] in result["knowledge_summary"]


def test_aqi_scenario_retrieves_aqi_sop():
    result = knowledge_agent(SCENARIOS["aqi"]["state"])
    assert SCENARIOS["aqi"]["sop_title"] in result["knowledge_summary"]


def test_heatwave_scenario_retrieves_heatwave_sop():
    result = knowledge_agent(SCENARIOS["heatwave"]["state"])
    assert SCENARIOS["heatwave"]["sop_title"] in result["knowledge_summary"]


def test_traffic_scenario_retrieves_traffic_sop():
    result = knowledge_agent(SCENARIOS["traffic"]["state"])
    assert SCENARIOS["traffic"]["sop_title"] in result["knowledge_summary"]


def test_event_scenario_retrieves_event_sop():
    result = knowledge_agent(SCENARIOS["event"]["state"])
    assert SCENARIOS["event"]["sop_title"] in result["knowledge_summary"]


def test_baseline_scenario_retrieves_no_sop():
    result = knowledge_agent(SCENARIOS["baseline"]["state"])
    assert result["knowledge_summary"] == "No specific SOP matched. Apply general city operations protocol."
