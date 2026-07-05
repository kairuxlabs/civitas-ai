from src.knowledge_pipeline.parsers.wikipedia_parser import parse_wikipedia_page


def test_parses_page_with_title_and_extract():
    payload = {"title": "Flood", "extract": "A flood is an overflow of water.\n\n\nIt can be caused by rain."}
    doc = parse_wikipedia_page(payload, category="disaster")
    assert doc["title"] == "Flood"
    assert doc["content"] == "A flood is an overflow of water.\n\nIt can be caused by rain."
    assert doc["language"] == "en"
    assert doc["category"] == "disaster"
    assert doc["source"] == "Wikipedia"
    assert doc["confidence"] == 0.85


def test_returns_none_for_missing_page():
    assert parse_wikipedia_page({"title": "Flood", "missing": True}, category="disaster") is None


def test_returns_none_for_empty_extract():
    assert parse_wikipedia_page({"title": "Flood", "extract": ""}, category="disaster") is None
