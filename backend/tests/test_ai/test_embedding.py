import pytest
from unittest.mock import AsyncMock, patch

from src.ai.embedding import embed


@pytest.mark.asyncio
async def test_returns_vector_when_gateway_succeeds():
    with patch(
        "src.ai.embedding.call_openrouter",
        new=AsyncMock(return_value={"data": [{"embedding": [0.1, 0.2, 0.3]}]}),
    ):
        result = await embed("hello world")

    assert result == [0.1, 0.2, 0.3]


@pytest.mark.asyncio
async def test_returns_none_when_gateway_returns_none():
    with patch("src.ai.embedding.call_openrouter", new=AsyncMock(return_value=None)):
        result = await embed("anything")

    assert result is None


@pytest.mark.asyncio
async def test_returns_none_on_malformed_response_shape():
    with patch(
        "src.ai.embedding.call_openrouter",
        new=AsyncMock(return_value={"unexpected": "shape"}),
    ):
        result = await embed("anything")

    assert result is None
