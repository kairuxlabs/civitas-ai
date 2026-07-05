import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from src.knowledge_pipeline.collectors.wikidata_collector import WikidataCollector


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
async def test_returns_empty_when_no_entity_has_a_qid():
    entities = [{"id": "hospital_1", "metadata": {}}]
    result = await WikidataCollector(entities).collect()
    assert result == []


@pytest.mark.asyncio
async def test_enriches_matching_entity_and_mutates_in_place():
    entities = [{"id": "hospital_1", "metadata": {"wikidata_qid": "Q123"}, "confidence": 1.0}]
    sparql_response = {
        "results": {"bindings": [{
            "item": {"value": "http://www.wikidata.org/entity/Q123"},
            "itemLabel": {"value": "Bach Mai Hospital"},
            "instanceOfLabel": {"value": "hospital"},
        }]}
    }
    with patch("src.knowledge_pipeline.collectors.wikidata_collector.aiohttp.ClientSession") as mock_client:
        mock_client.return_value = _mock_http_session(sparql_response)
        result = await WikidataCollector(entities).collect()

    assert len(result) == 1
    assert entities[0]["metadata"]["wikidata_label"] == "Bach Mai Hospital"
    assert entities[0]["metadata"]["wikidata_instance_of"] == "hospital"
    assert entities[0]["confidence"] == 0.9


@pytest.mark.asyncio
async def test_survives_sparql_failure():
    entities = [{"id": "hospital_1", "metadata": {"wikidata_qid": "Q123"}}]
    with patch("src.knowledge_pipeline.collectors.wikidata_collector.aiohttp.ClientSession") as mock_client:
        mock_session = MagicMock()
        mock_session.get = MagicMock(side_effect=RuntimeError("timeout"))
        mock_session.__aenter__ = AsyncMock(return_value=mock_session)
        mock_session.__aexit__ = AsyncMock(return_value=None)
        mock_client.return_value = mock_session

        result = await WikidataCollector(entities).collect()
    assert result == []
