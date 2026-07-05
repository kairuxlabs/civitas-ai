from src.knowledge_pipeline.processors.chunking import chunk_text


def test_short_text_returns_single_chunk():
    assert chunk_text("A short sentence.") == ["A short sentence."]


def test_empty_text_returns_no_chunks():
    assert chunk_text("") == []


def test_long_text_splits_into_multiple_chunks_under_max_chars():
    sentence = "The quick brown fox jumps over the lazy dog. "
    long_text = sentence * 200  # ~9400 chars
    chunks = chunk_text(long_text, max_chars=1000, overlap=50)

    assert len(chunks) > 1
    for chunk in chunks:
        assert len(chunk) <= 1000 + 50 + len(sentence)


def test_content_is_preserved_across_chunks():
    text = "First sentence here. Second sentence here. Third sentence here."
    chunks = chunk_text(text, max_chars=30, overlap=5)
    joined = " ".join(chunks)
    assert "First sentence" in joined
    assert "Third sentence" in joined
