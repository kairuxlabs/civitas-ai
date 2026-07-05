from src.knowledge_pipeline.processors import entity_extractor


def test_extracts_entities_and_relations_from_valid_response(monkeypatch):
    canned = '{"entities": [{"type": "Hospital", "name": "Bach Mai"}], "relations": [{"from": "Flood", "relation": "impacts", "to": "Bach Mai"}]}'
    monkeypatch.setattr(entity_extractor, "call_gemini", lambda prompt, expect_json=False: canned)
    monkeypatch.setattr(entity_extractor, "parse_json_safe", lambda text: __import__("json").loads(text))

    result = entity_extractor.extract_entities("Heavy rain flooded the area near Bach Mai hospital.")
    assert result["entities"] == [{"type": "Hospital", "name": "Bach Mai"}]
    assert result["relations"] == [{"from": "Flood", "relation": "impacts", "to": "Bach Mai"}]


def test_returns_empty_when_gemini_unavailable(monkeypatch):
    monkeypatch.setattr(entity_extractor, "call_gemini", lambda prompt, expect_json=False: None)
    result = entity_extractor.extract_entities("Some text.")
    assert result == {"entities": [], "relations": []}


def test_returns_empty_when_response_is_not_json(monkeypatch):
    monkeypatch.setattr(entity_extractor, "call_gemini", lambda prompt, expect_json=False: "not json")
    monkeypatch.setattr(entity_extractor, "parse_json_safe", lambda text: None)
    result = entity_extractor.extract_entities("Some text.")
    assert result == {"entities": [], "relations": []}


def test_returns_empty_when_parsed_is_non_dict_truthy(monkeypatch):
    """Verify non-dict truthy values (e.g., array) don't raise AttributeError."""
    monkeypatch.setattr(entity_extractor, "call_gemini", lambda prompt, expect_json=False: "something")
    monkeypatch.setattr(entity_extractor, "parse_json_safe", lambda text: ["oops"])
    result = entity_extractor.extract_entities("Some text.")
    assert result == {"entities": [], "relations": []}
