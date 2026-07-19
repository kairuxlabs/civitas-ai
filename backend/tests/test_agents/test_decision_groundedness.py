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
import pytest

import src.agents.decision_agent as decision_agent_module
from src.agents.base import AgentState
from src.agents.decision_agent import decision_agent, _rule_based_decision
from src.agents.knowledge_agent import knowledge_agent
from src.utils.config import settings


@pytest.fixture(autouse=True)
def _force_offline(monkeypatch):
    """Force both LLM keys empty so every test in this file stays fully
    offline, regardless of what's in a local .env — knowledge_agent()
    and decision_agent() both call call_gemini() internally, which only
    skips real network calls when both keys are unset."""
    monkeypatch.setattr(settings, "gemini_api_key", "")
    monkeypatch.setattr(settings, "openrouter_api_key", "")


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


def _decision_prompt_for(scenario_name: str, monkeypatch) -> str:
    """Run knowledge_agent for real to get the actual retrieved SOP summary,
    inject it into the scenario's state, then call decision_agent with
    call_gemini mocked to capture the prompt it was given."""
    state = dict(SCENARIOS[scenario_name]["state"])
    state["knowledge_summary"] = knowledge_agent(state)["knowledge_summary"]

    captured_prompts = []

    def fake_call_gemini(prompt, expect_json=False):
        captured_prompts.append(prompt)
        return None  # force the rule-based fallback path; we only care about the prompt here

    monkeypatch.setattr(decision_agent_module, "call_gemini", fake_call_gemini)
    decision_agent(state)

    assert len(captured_prompts) == 1
    return captured_prompts[0]


def test_flood_decision_prompt_includes_retrieved_sop(monkeypatch):
    prompt = _decision_prompt_for("flood", monkeypatch)
    summary = knowledge_agent(SCENARIOS["flood"]["state"])["knowledge_summary"]
    assert summary in prompt


def test_aqi_decision_prompt_includes_retrieved_sop(monkeypatch):
    prompt = _decision_prompt_for("aqi", monkeypatch)
    summary = knowledge_agent(SCENARIOS["aqi"]["state"])["knowledge_summary"]
    assert summary in prompt


def test_heatwave_decision_prompt_includes_retrieved_sop(monkeypatch):
    prompt = _decision_prompt_for("heatwave", monkeypatch)
    summary = knowledge_agent(SCENARIOS["heatwave"]["state"])["knowledge_summary"]
    assert summary in prompt


def test_traffic_decision_prompt_includes_retrieved_sop(monkeypatch):
    prompt = _decision_prompt_for("traffic", monkeypatch)
    summary = knowledge_agent(SCENARIOS["traffic"]["state"])["knowledge_summary"]
    assert summary in prompt


def test_event_decision_prompt_includes_retrieved_sop(monkeypatch):
    prompt = _decision_prompt_for("event", monkeypatch)
    summary = knowledge_agent(SCENARIOS["event"]["state"])["knowledge_summary"]
    assert summary in prompt


def test_flood_fallback_recommends_drainage_action():
    decision = _rule_based_decision(SCENARIOS["flood"]["state"])
    recommendations_text = " ".join(decision["recommendations"])
    assert SCENARIOS["flood"]["fallback_keyword"] in recommendations_text


def test_aqi_fallback_recommends_health_advisory():
    decision = _rule_based_decision(SCENARIOS["aqi"]["state"])
    recommendations_text = " ".join(decision["recommendations"])
    assert SCENARIOS["aqi"]["fallback_keyword"] in recommendations_text


def test_heatwave_fallback_recommends_cooling_centers():
    decision = _rule_based_decision(SCENARIOS["heatwave"]["state"])
    recommendations_text = " ".join(decision["recommendations"])
    assert SCENARIOS["heatwave"]["fallback_keyword"] in recommendations_text


def test_event_fallback_recommends_security_and_medical():
    decision = _rule_based_decision(SCENARIOS["event"]["state"])
    recommendations_text = " ".join(decision["recommendations"])
    assert SCENARIOS["event"]["fallback_keyword"] in recommendations_text


def test_traffic_fallback_has_no_scenario_specific_recommendation():
    """Documents a known pre-existing gap: _rule_based_decision has no
    traffic-specific branch, so a pure-traffic scenario (no other risk
    factors triggered) falls through to the generic stable-conditions
    message rather than anything referencing traffic. Not a bug to fix in
    this plan — see Task 3, Step 1."""
    decision = _rule_based_decision(SCENARIOS["traffic"]["state"])
    assert decision["recommendations"] == ["Các chỉ số thành phố ổn định — duy trì giám sát thường xuyên"]


def test_baseline_fallback_recommends_stable_monitoring_only():
    decision = _rule_based_decision(SCENARIOS["baseline"]["state"])
    assert decision["recommendations"] == ["Các chỉ số thành phố ổn định — duy trì giám sát thường xuyên"]
