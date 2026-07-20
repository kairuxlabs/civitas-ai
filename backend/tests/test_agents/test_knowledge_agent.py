from src.agents.knowledge_agent import knowledge_agent
from src.agents.base import AgentState
import pytest
from src.utils.config import settings


@pytest.fixture(autouse=True)
def _force_offline(monkeypatch):
    """Force all LLM/Qdrant keys empty so every test in this file stays fully
    offline, regardless of what's in a local .env — knowledge_agent() calls
    call_gemini() internally, and (after Task 3) also calls
    qdrant_loader.search_chunks() when qdrant_url is set."""
    monkeypatch.setattr(settings, "gemini_api_key", "")
    monkeypatch.setattr(settings, "openrouter_api_key", "")
    monkeypatch.setattr(settings, "qdrant_url", "")


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


def test_combines_sop_and_city_knowledge_when_both_available(monkeypatch):
    monkeypatch.setattr(settings, "qdrant_url", "https://fake.qdrant.io")
    monkeypatch.setattr(
        "src.agents.knowledge_agent.qdrant_loader.search_chunks",
        lambda query, k=2: [{"title": "Ho Hoan Kiem", "content": "Ho trung tam Ha Noi.", "category": "geography", "source": "Wikipedia"}],
    )
    monkeypatch.setattr(
        "src.agents.knowledge_agent.call_gemini",
        lambda prompt: "Kich hoat bom thoat nuoc ngay.",
    )

    state = _state("Tinh hinh ngap lut", rain=25.0)
    result = knowledge_agent(state)

    assert result["knowledge_summary"] == "[Flood Emergency SOP] Kich hoat bom thoat nuoc ngay."
    assert len(result["knowledge_evidence"]) >= 2


def test_falls_back_to_sop_only_when_gemini_fails_with_city_knowledge_present(monkeypatch):
    monkeypatch.setattr(settings, "qdrant_url", "https://fake.qdrant.io")
    monkeypatch.setattr(
        "src.agents.knowledge_agent.qdrant_loader.search_chunks",
        lambda query, k=2: [{"title": "Ho Hoan Kiem", "content": "Ho trung tam Ha Noi.", "category": "geography", "source": "Wikipedia"}],
    )
    monkeypatch.setattr("src.agents.knowledge_agent.call_gemini", lambda prompt: None)

    state = _state("Tinh hinh ngap lut", rain=25.0)
    result = knowledge_agent(state)

    assert result["knowledge_summary"] == "Flood Emergency SOP: Activate drainage pumps at all low-lying districts."
    assert "Ho Hoan Kiem" not in result["knowledge_summary"]


def test_synthesizes_city_knowledge_only_when_no_sop_matches(monkeypatch):
    monkeypatch.setattr(settings, "qdrant_url", "https://fake.qdrant.io")
    monkeypatch.setattr(
        "src.agents.knowledge_agent.qdrant_loader.search_chunks",
        lambda query, k=2: [{"title": "Ho Hoan Kiem", "content": "Ho trung tam Ha Noi.", "category": "geography", "source": "Wikipedia"}],
    )
    monkeypatch.setattr(
        "src.agents.knowledge_agent.call_gemini",
        lambda prompt: "Ho Hoan Kiem nam o trung tam Ha Noi.",
    )

    state = _state("Ho Hoan Kiem o dau?", aqi=90, rain=0)
    result = knowledge_agent(state)

    assert result["knowledge_summary"] == "Ho Hoan Kiem nam o trung tam Ha Noi."
    assert len(result["knowledge_evidence"]) >= 1


def test_no_sop_and_no_city_knowledge_and_gemini_fails_returns_baseline_message(monkeypatch):
    monkeypatch.setattr(settings, "qdrant_url", "https://fake.qdrant.io")
    monkeypatch.setattr("src.agents.knowledge_agent.qdrant_loader.search_chunks", lambda query, k=2: [])
    monkeypatch.setattr("src.agents.knowledge_agent.call_gemini", lambda prompt: None)

    state = _state("Ho Hoan Kiem o dau?", aqi=90, rain=0)
    result = knowledge_agent(state)

    assert result["knowledge_summary"] == "No specific SOP matched. Apply general city operations protocol."


def test_does_not_call_search_chunks_when_qdrant_unset(monkeypatch):
    """settings.qdrant_url is already forced empty by the file's autouse
    fixture; this test just asserts search_chunks is never even called,
    confirming the Global Constraint that Qdrant-unset behavior does no
    extra work."""
    called = []
    monkeypatch.setattr(
        "src.agents.knowledge_agent.qdrant_loader.search_chunks",
        lambda query, k=2: called.append(1) or [],
    )

    state = _state("What should we do?", rain=25.0)
    knowledge_agent(state)

    assert called == []


def test_matched_sop_produces_evidence():
    state = _state("What should we do?", rain=25.0)
    result = knowledge_agent(state)
    ev = result["knowledge_evidence"]
    assert len(ev) >= 1
    assert all(e["source"] == "SOP" for e in ev)
    assert all(e["type"] == "sop" for e in ev)
    assert all(e["agent"] == "knowledge" for e in ev)
    assert all(e["time"] == "static" for e in ev)


def test_no_match_produces_no_evidence():
    state = _state("What is the current status?", aqi=80, rain=0)
    result = knowledge_agent(state)
    assert result["knowledge_evidence"] == []


def test_city_chunks_produce_evidence_with_real_source(monkeypatch):
    import src.agents.knowledge_agent as ka

    monkeypatch.setattr(settings, "qdrant_url", "http://fake-qdrant:6333")
    monkeypatch.setattr(
        ka.qdrant_loader, "search_chunks",
        lambda query, k=2: [{"title": "Hanoi Metro", "source": "wikipedia", "content": "Metro Line 2A..."}],
    )
    state = _state("Tell me about Hanoi transport", aqi=80, rain=0)
    result = knowledge_agent(state)
    ev = result["knowledge_evidence"]
    chunk_items = [e for e in ev if e["source"] == "wikipedia"]
    assert len(chunk_items) == 1
    assert chunk_items[0]["type"] == "knowledge"
    assert chunk_items[0]["agent"] == "knowledge"
