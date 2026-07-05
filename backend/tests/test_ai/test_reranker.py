import pytest
from unittest.mock import AsyncMock, patch

from src.ai.reranker import rerank


@pytest.mark.asyncio
async def test_returns_reordered_indices_when_gateway_succeeds():
    with patch(
        "src.ai.reranker.call_openrouter",
        new=AsyncMock(
            return_value={
                "results": [
                    {"index": 2, "relevance_score": 0.9},
                    {"index": 0, "relevance_score": 0.5},
                    {"index": 1, "relevance_score": 0.1},
                ]
            }
        ),
    ):
        result = await rerank("query", ["doc0", "doc1", "doc2"], top_k=5)

    assert result == [2, 0, 1]


@pytest.mark.asyncio
async def test_returns_passthrough_when_gateway_returns_none():
    with patch("src.ai.reranker.call_openrouter", new=AsyncMock(return_value=None)):
        result = await rerank("query", ["doc0", "doc1", "doc2"], top_k=2)

    assert result == [0, 1]


@pytest.mark.asyncio
async def test_returns_passthrough_when_gateway_returns_malformed_response():
    with patch(
        "src.ai.reranker.call_openrouter",
        new=AsyncMock(return_value={"results": [{"index": 0}]}),
    ):
        result = await rerank("query", ["doc0", "doc1", "doc2"], top_k=2)

    assert result == [0, 1]


@pytest.mark.asyncio
async def test_returns_empty_list_without_calling_gateway_when_no_documents():
    mock_call = AsyncMock(return_value=None)
    with patch("src.ai.reranker.call_openrouter", new=mock_call):
        result = await rerank("query", [], top_k=5)

    assert result == []
    mock_call.assert_not_called()
