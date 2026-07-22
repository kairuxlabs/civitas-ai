from src.agents.knowledge_agent import knowledge_agent
from src.agents.base import AgentState
import pytest
from unittest.mock import MagicMock
from src.utils.config import settings


@pytest.fixture(autouse=True)
def _force_offline(monkeypatch):
    """Force all LLM/Qdrant/Neo4j keys empty so every test in this file stays
    fully offline, regardless of what's in a local .env — knowledge_agent()
    calls call_gemini() internally, qdrant_loader.search_chunks() when
    qdrant_url is set, and Neo4jLoader.find_related() when neo4j_uri is set."""
    monkeypatch.setattr(settings, "gemini_api_key", "")
    monkeypatch.setattr(settings, "openrouter_api_key", "")
    monkeypatch.setattr(settings, "qdrant_url", "")
    monkeypatch.setattr(settings, "neo4j_uri", "")


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


def test_falls_back_to_sop_only_when_gemini_raises(monkeypatch):
    """If call_gemini raises instead of returning None (e.g. a transient SDK
    error), the agent must not crash — it should log and fall through to the
    same deterministic SOP-only summary as the None-return case."""
    monkeypatch.setattr(settings, "qdrant_url", "https://fake.qdrant.io")
    monkeypatch.setattr(
        "src.agents.knowledge_agent.qdrant_loader.search_chunks",
        lambda query, k=2: [{"title": "Ho Hoan Kiem", "content": "Ho trung tam Ha Noi.", "category": "geography", "source": "Wikipedia"}],
    )

    def _raise(prompt):
        raise RuntimeError("simulated Gemini failure")

    monkeypatch.setattr("src.agents.knowledge_agent.call_gemini", _raise)

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


def test_no_match_produces_gap_evidence():
    """Supersedes the old test_no_match_produces_no_evidence: 'no match' now
    produces a gap evidence item instead of an empty list, so Critic (and
    the operator) can see *why* nothing was found."""
    state = _state("What is the current status?", aqi=80, rain=0)
    result = knowledge_agent(state)
    ev = result["knowledge_evidence"]
    assert len(ev) == 1
    assert ev[0]["type"] == "gap"
    assert ev[0]["source"] == "Knowledge Retrieval"
    assert ev[0]["confidence"] == 0
    assert ev[0]["agent"] == "knowledge"


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


def test_graph_keywords_extracts_longest_terms_first():
    from src.agents.knowledge_agent import _graph_keywords
    assert _graph_keywords("Why is Hoan Kiem traffic bad?") == ["traffic", "Hoan", "Kiem"]


def test_graph_keywords_excludes_stopwords():
    from src.agents.knowledge_agent import _graph_keywords
    assert _graph_keywords("What should we do about this situation?") == []


def test_graph_keywords_caps_at_three():
    from src.agents.knowledge_agent import _graph_keywords
    result = _graph_keywords("Metro railway bridge tunnel station platform")
    assert len(result) == 3


def test_does_not_query_neo4j_when_keywords_empty(monkeypatch):
    import src.agents.knowledge_agent as ka

    monkeypatch.setattr(settings, "neo4j_uri", "neo4j+s://fake")
    mock_loader_cls = MagicMock()
    monkeypatch.setattr(ka, "Neo4jLoader", mock_loader_cls)

    state = _state("Why is it?", aqi=80, rain=0)
    knowledge_agent(state)

    mock_loader_cls.assert_not_called()


def test_does_not_query_neo4j_when_unset(monkeypatch):
    import src.agents.knowledge_agent as ka

    # settings.neo4j_uri is already forced empty by the file's autouse fixture
    mock_loader_cls = MagicMock()
    monkeypatch.setattr(ka, "Neo4jLoader", mock_loader_cls)

    state = _state("Tell me about Metro Line 2A", aqi=80, rain=0)
    knowledge_agent(state)

    mock_loader_cls.assert_not_called()


def test_graph_facts_produce_evidence_when_neo4j_configured(monkeypatch):
    import src.agents.knowledge_agent as ka

    monkeypatch.setattr(settings, "neo4j_uri", "neo4j+s://fake")
    fake_loader = MagicMock()
    fake_loader.find_related.return_value = [
        {"name": "Metro Line 2A", "label": "Road", "relation": "CONNECTS", "related_name": "Cat Linh"},
    ]
    monkeypatch.setattr(ka, "Neo4jLoader", lambda: fake_loader)

    state = _state("Tell me about Metro Line 2A", aqi=80, rain=0)
    result = knowledge_agent(state)

    ev = result["knowledge_evidence"]
    graph_items = [e for e in ev if e["source"] == "Neo4j Knowledge Graph"]
    assert len(graph_items) == 1
    assert graph_items[0]["type"] == "knowledge"
    assert graph_items[0]["agent"] == "knowledge"
    assert graph_items[0]["confidence"] == 0.6
    assert graph_items[0]["time"] == "static"
    assert "Metro Line 2A" in graph_items[0]["content"]
    assert "Cat Linh" in graph_items[0]["content"]
    fake_loader.close.assert_called_once()


def test_graph_facts_with_no_relation_still_produce_evidence(monkeypatch):
    import src.agents.knowledge_agent as ka

    monkeypatch.setattr(settings, "neo4j_uri", "neo4j+s://fake")
    fake_loader = MagicMock()
    fake_loader.find_related.return_value = [
        {"name": "Metro Line 2A", "label": "Road", "relation": None, "related_name": None},
    ]
    monkeypatch.setattr(ka, "Neo4jLoader", lambda: fake_loader)

    state = _state("Tell me about Metro Line 2A", aqi=80, rain=0)
    result = knowledge_agent(state)

    graph_items = [e for e in result["knowledge_evidence"] if e["source"] == "Neo4j Knowledge Graph"]
    assert len(graph_items) == 1
    assert "Metro Line 2A" in graph_items[0]["content"]


def test_graph_facts_included_in_gemini_prompt(monkeypatch):
    import src.agents.knowledge_agent as ka

    monkeypatch.setattr(settings, "neo4j_uri", "neo4j+s://fake")
    fake_loader = MagicMock()
    fake_loader.find_related.return_value = [
        {"name": "Metro Line 2A", "label": "Road", "relation": "CONNECTS", "related_name": "Cat Linh"},
    ]
    monkeypatch.setattr(ka, "Neo4jLoader", lambda: fake_loader)

    captured_prompts = []

    def _capture(prompt):
        captured_prompts.append(prompt)
        return "Đã ghi nhận."

    monkeypatch.setattr(ka, "call_gemini", _capture)

    state = _state("Tell me about Metro Line 2A", aqi=80, rain=0)
    knowledge_agent(state)

    assert captured_prompts
    assert "Metro Line 2A" in captured_prompts[0]


def test_graph_facts_use_real_provenance_when_present(monkeypatch):
    import src.agents.knowledge_agent as ka

    monkeypatch.setattr(settings, "neo4j_uri", "neo4j+s://fake")
    fake_loader = MagicMock()
    fake_loader.find_related.return_value = [
        {"name": "Metro Line 2A", "label": "Road", "relation": "CONNECTS", "related_name": "Cat Linh",
         "rel_source": "Wikipedia", "rel_confidence": 0.92, "rel_created_at": "2026-07-21T09:00:00+00:00"},
    ]
    monkeypatch.setattr(ka, "Neo4jLoader", lambda: fake_loader)

    state = _state("Tell me about Metro Line 2A", aqi=80, rain=0)
    result = knowledge_agent(state)

    graph_items = [e for e in result["knowledge_evidence"] if e["type"] == "knowledge" and "Metro Line 2A" in e["content"]]
    assert len(graph_items) == 1
    assert graph_items[0]["source"] == "Wikipedia"
    assert graph_items[0]["confidence"] == 0.92
    assert graph_items[0]["time"] == "2026-07-21T09:00:00+00:00"


def test_graph_only_match_does_not_return_baseline_message(monkeypatch):
    """When neither SOP nor Qdrant match but the graph does, the early-return
    'No specific SOP matched' baseline must NOT fire — the Gemini synthesis
    path (or its fallback) should still run with the graph context."""
    import src.agents.knowledge_agent as ka

    monkeypatch.setattr(settings, "neo4j_uri", "neo4j+s://fake")
    fake_loader = MagicMock()
    fake_loader.find_related.return_value = [
        {"name": "Metro Line 2A", "label": "Road", "relation": "CONNECTS", "related_name": "Cat Linh"},
    ]
    monkeypatch.setattr(ka, "Neo4jLoader", lambda: fake_loader)
    monkeypatch.setattr(ka, "call_gemini", lambda prompt: "Metro Line 2A kết nối Cát Linh.")

    state = _state("Tell me about Metro Line 2A", aqi=80, rain=0)
    result = knowledge_agent(state)

    assert result["knowledge_summary"] != "No specific SOP matched. Apply general city operations protocol."
