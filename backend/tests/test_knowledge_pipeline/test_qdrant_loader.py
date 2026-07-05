from unittest.mock import MagicMock, patch

from src.knowledge_pipeline.loaders import qdrant_loader
from src.utils.config import settings


def test_returns_zero_when_qdrant_not_configured(monkeypatch):
    monkeypatch.setattr(settings, "qdrant_url", "")
    assert qdrant_loader.load_chunks([{"content": "x"}]) == 0


def test_returns_zero_for_empty_chunks(monkeypatch):
    monkeypatch.setattr(settings, "qdrant_url", "https://fake.qdrant.io")
    assert qdrant_loader.load_chunks([]) == 0


def test_loads_chunks_with_embeddings(monkeypatch):
    monkeypatch.setattr(settings, "qdrant_url", "https://fake.qdrant.io")
    monkeypatch.setattr(settings, "qdrant_api_key", "fake-key")
    monkeypatch.setattr(qdrant_loader, "embed_text", lambda text, task_type=None: [0.1, 0.2, 0.3])

    mock_client = MagicMock()
    mock_client.collection_exists.return_value = True
    with patch("src.knowledge_pipeline.loaders.qdrant_loader.QdrantClient", return_value=mock_client):
        count = qdrant_loader.load_chunks([
            {"content": "Chunk one.", "title": "Doc A", "chunk_index": 0},
            {"content": "Chunk two.", "title": "Doc A", "chunk_index": 1},
        ])

    assert count == 2
    mock_client.upsert.assert_called_once()
    _, kwargs = mock_client.upsert.call_args
    assert kwargs["collection_name"] == "city_knowledge"
    assert len(kwargs["points"]) == 2


def test_skips_chunk_when_embedding_fails(monkeypatch):
    monkeypatch.setattr(settings, "qdrant_url", "https://fake.qdrant.io")
    monkeypatch.setattr(qdrant_loader, "embed_text", lambda text, task_type=None: None)

    mock_client = MagicMock()
    mock_client.collection_exists.return_value = True
    with patch("src.knowledge_pipeline.loaders.qdrant_loader.QdrantClient", return_value=mock_client):
        count = qdrant_loader.load_chunks([{"content": "x", "title": "t", "chunk_index": 0}])

    assert count == 0
    mock_client.upsert.assert_not_called()


def test_point_ids_are_deterministic_across_calls(monkeypatch):
    """Same chunk must produce the same point id on repeated calls, even
    across separate load_chunks() invocations (simulating separate process
    runs) — proves ids don't depend on Python's randomized hash()."""
    monkeypatch.setattr(settings, "qdrant_url", "https://fake.qdrant.io")
    monkeypatch.setattr(qdrant_loader, "embed_text", lambda text, task_type=None: [0.1, 0.2, 0.3])

    chunk_a = {"content": "Chunk one.", "title": "Doc A", "chunk_index": 0}
    chunk_b = {"content": "Chunk two.", "title": "Doc A", "chunk_index": 1}

    ids_per_run = []
    for _ in range(2):
        mock_client = MagicMock()
        mock_client.collection_exists.return_value = True
        with patch("src.knowledge_pipeline.loaders.qdrant_loader.QdrantClient", return_value=mock_client):
            qdrant_loader.load_chunks([chunk_a, chunk_b])
        _, kwargs = mock_client.upsert.call_args
        ids_per_run.append([p.id for p in kwargs["points"]])

    # Same chunks -> same ids across independent calls.
    assert ids_per_run[0] == ids_per_run[1]
    # Different chunks (different title/chunk_index) -> different ids.
    assert ids_per_run[0][0] != ids_per_run[0][1]


def test_returns_zero_when_qdrant_network_call_fails(monkeypatch):
    monkeypatch.setattr(settings, "qdrant_url", "https://fake.qdrant.io")
    monkeypatch.setattr(qdrant_loader, "embed_text", lambda text, task_type=None: [0.1, 0.2, 0.3])

    mock_client = MagicMock()
    mock_client.collection_exists.side_effect = Exception("connection refused")
    with patch("src.knowledge_pipeline.loaders.qdrant_loader.QdrantClient", return_value=mock_client):
        count = qdrant_loader.load_chunks([{"content": "x", "title": "t", "chunk_index": 0}])

    assert count == 0
