from src.knowledge_pipeline.processors.metadata_builder import build_chunk_metadata


def test_builds_metadata_with_defaults():
    doc = {"title": "Flood", "category": "disaster", "language": "en", "source": "Wikipedia", "confidence": 0.85}
    result = build_chunk_metadata("Flood chunk text.", doc, chunk_index=2)
    assert result == {
        "content": "Flood chunk text.",
        "title": "Flood",
        "category": "disaster",
        "language": "en",
        "source": "Wikipedia",
        "city": "Hanoi",
        "chunk_index": 2,
        "confidence": 0.85,
    }


def test_fills_missing_fields_with_defaults():
    result = build_chunk_metadata("Text.", {}, chunk_index=0)
    assert result["title"] == ""
    assert result["category"] == "general"
    assert result["language"] == "en"
    assert result["source"] == "unknown"
    assert result["confidence"] == 0.85
