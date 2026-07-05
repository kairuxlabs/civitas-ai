import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from src.knowledge_pipeline.collectors.wikipedia_collector import WikipediaCollector, TOPICS


def _mock_http_session(fixed_response: dict):
    mock_resp = MagicMock()
    mock_resp.json = AsyncMock(return_value=fixed_response)
    mock_resp.__aenter__ = AsyncMock(return_value=mock_resp)
    mock_resp.__aexit__ = AsyncMock(return_value=None)

    mock_session = MagicMock()
    mock_session.get = MagicMock(return_value=mock_resp)
    mock_session.__aenter__ = AsyncMock(return_value=mock_session)
    mock_session.__aexit__ = AsyncMock(return_value=None)
    return mock_session


@pytest.mark.asyncio
async def test_collect_returns_one_doc_per_topic_page():
    response = {"query": {"pages": {"123": {"title": "Any Title", "extract": "Some content."}}}}
    with patch("src.knowledge_pipeline.collectors.wikipedia_collector.aiohttp.ClientSession") as mock_client:
        mock_client.return_value = _mock_http_session(response)
        docs = await WikipediaCollector().collect()

    assert len(docs) == len(TOPICS)
    assert all(d["content"] == "Some content." for d in docs)


@pytest.mark.asyncio
async def test_collect_survives_a_missing_page():
    with patch("src.knowledge_pipeline.collectors.wikipedia_collector.aiohttp.ClientSession") as mock_client:
        mock_session = MagicMock()
        mock_session.get = MagicMock(side_effect=RuntimeError("network error"))
        mock_session.__aenter__ = AsyncMock(return_value=mock_session)
        mock_session.__aexit__ = AsyncMock(return_value=None)
        mock_client.return_value = mock_session

        docs = await WikipediaCollector().collect()
    assert docs == []
