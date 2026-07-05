from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from src.runtime.memory import DecisionMemory, KnowledgeMemory
from src.utils.config import settings


@pytest.fixture(autouse=True)
def _force_keyword_fallback(monkeypatch):
    # Keep this test file offline regardless of a locally-configured QDRANT_URL
    monkeypatch.setattr(settings, "qdrant_url", "")


class _FakeHit:
    def __init__(self, id, payload, score):
        self.id = id
        self.payload = payload
        self.score = score


def _make_hits(n):
    return [
        _FakeHit(
            id=i,
            payload={"doc_id": f"doc-{i}", "title": f"Title {i}", "content": f"Content {i}"},
            score=1.0 - i * 0.01,
        )
        for i in range(n)
    ]


def test_knowledge_memory_finds_flood_sop():
    memory = KnowledgeMemory()
    results = memory.search("heavy rain flood in Hanoi", k=2)
    assert results
    assert any("flood" in r["title"].lower() for r in results)
    assert {"id", "title", "content", "score"} <= set(results[0])


def test_knowledge_memory_empty_for_unrelated_query():
    memory = KnowledgeMemory()
    assert memory.search("quantum computing budget", k=3) == []


def test_decision_memory_stores_and_returns_chain():
    memory = DecisionMemory()
    memory.store_chain(
        incident={"type": "heavy_rain", "district_id": 1},
        decision={"summary": "deploy pumps", "confidence": 90},
        workflow={"steps": ["notify", "create_incident"]},
        outcome="approved",
    )
    chains = memory.recent(5)
    assert len(chains) == 1
    chain = chains[0]
    assert chain["incident"]["type"] == "heavy_rain"
    assert chain["outcome"] == "approved"
    assert chain["ts"]


def test_decision_memory_recent_limit_and_order():
    memory = DecisionMemory()
    for i in range(5):
        memory.store_chain({"i": i}, {}, {}, "done")
    recent = memory.recent(3)
    assert len(recent) == 3
    assert recent[0]["incident"]["i"] == 4  # newest first


def test_qdrant_search_reranks_when_openrouter_key_set(monkeypatch):
    monkeypatch.setattr(settings, "qdrant_url", "https://fake.qdrant.io")
    monkeypatch.setattr(settings, "openrouter_api_key", "fake-key")
    monkeypatch.setattr(
        "src.agents.gemini_client.embed_text",
        lambda text, task_type=None: [0.1, 0.2, 0.3],
    )

    mock_client = MagicMock()
    mock_client.search.return_value = _make_hits(20)

    with (
        patch("qdrant_client.QdrantClient", return_value=mock_client),
        patch("src.ai.reranker.rerank", new=AsyncMock(return_value=[2, 0, 1])),
    ):
        memory = KnowledgeMemory()
        results = memory.search("flood", k=3)

    # Qdrant is queried with a widened candidate set before reranking.
    _, kwargs = mock_client.search.call_args
    assert kwargs["limit"] == max(3 * 4, 20)

    # Final order follows the reranker's index order, not Qdrant's.
    assert [r["id"] for r in results] == ["doc-2", "doc-0", "doc-1"]


def test_qdrant_search_unset_key_matches_pre_existing_behavior(monkeypatch):
    monkeypatch.setattr(settings, "qdrant_url", "https://fake.qdrant.io")
    monkeypatch.setattr(settings, "openrouter_api_key", "")  # explicit default/unset
    monkeypatch.setattr(
        "src.agents.gemini_client.embed_text",
        lambda text, task_type=None: [0.1, 0.2, 0.3],
    )

    mock_client = MagicMock()
    mock_client.search.return_value = _make_hits(3)
    rerank_mock = AsyncMock()

    with (
        patch("qdrant_client.QdrantClient", return_value=mock_client),
        patch("src.ai.reranker.rerank", new=rerank_mock),
    ):
        memory = KnowledgeMemory()
        results = memory.search("flood", k=3)

    # Same limit as before reranking existed - no widening.
    _, kwargs = mock_client.search.call_args
    assert kwargs["limit"] == 3
    rerank_mock.assert_not_called()

    # Original Qdrant order, unchanged.
    assert [r["id"] for r in results] == ["doc-0", "doc-1", "doc-2"]


def test_qdrant_search_falls_back_to_qdrant_order_when_rerank_raises(monkeypatch):
    monkeypatch.setattr(settings, "qdrant_url", "https://fake.qdrant.io")
    monkeypatch.setattr(settings, "openrouter_api_key", "fake-key")
    monkeypatch.setattr(
        "src.agents.gemini_client.embed_text",
        lambda text, task_type=None: [0.1, 0.2, 0.3],
    )

    mock_client = MagicMock()
    mock_client.search.return_value = _make_hits(20)

    with (
        patch("qdrant_client.QdrantClient", return_value=mock_client),
        patch("src.ai.reranker.rerank", new=AsyncMock(side_effect=RuntimeError("gateway boom"))),
    ):
        memory = KnowledgeMemory()
        results = memory.search("flood", k=3)

    # Falls back to the widened Qdrant result, truncated to k, in original order.
    assert [r["id"] for r in results] == ["doc-0", "doc-1", "doc-2"]
