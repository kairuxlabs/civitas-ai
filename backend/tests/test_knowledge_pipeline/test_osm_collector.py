import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from src.knowledge_pipeline.collectors.osm_collector import (
    OSMCollector, build_tag_query, build_river_query, build_boundary_query,
)
from src.knowledge_pipeline.config.entity_types import ENTITY_TYPES, ROAD_TYPES, NAMED_RIVERS


def test_build_tag_query_includes_tag_value_and_bbox():
    query = build_tag_query("amenity", "hospital")
    assert 'amenity"="hospital"' in query
    assert "20.95,105.75,21.15,105.95" in query


def test_build_river_query_includes_name():
    query = build_river_query("Sông Hồng")
    assert "Sông Hồng" in query
    assert "waterway" in query


def test_build_boundary_query_targets_admin_level_8():
    query = build_boundary_query()
    assert 'admin_level"="8"' in query


def _mock_http_session(fixed_response: dict):
    mock_resp = MagicMock()
    mock_resp.json = AsyncMock(return_value=fixed_response)
    mock_resp.__aenter__ = AsyncMock(return_value=mock_resp)
    mock_resp.__aexit__ = AsyncMock(return_value=None)

    mock_session = MagicMock()
    mock_session.post = MagicMock(return_value=mock_resp)
    mock_session.__aenter__ = AsyncMock(return_value=mock_session)
    mock_session.__aexit__ = AsyncMock(return_value=None)
    return mock_session


@pytest.mark.asyncio
async def test_collect_aggregates_across_all_entity_types_roads_and_rivers():
    one_element = {
        "elements": [{"type": "node", "id": 1, "lat": 21.0, "lon": 105.8, "tags": {"name": "X"}}]
    }
    with patch("src.knowledge_pipeline.collectors.osm_collector.aiohttp.ClientSession") as mock_client:
        mock_client.return_value = _mock_http_session(one_element)
        entities = await OSMCollector().collect()

    expected_count = len(ENTITY_TYPES) + len(ROAD_TYPES["values"]) + len(NAMED_RIVERS)
    assert len(entities) == expected_count
    assert {e["type"] for e in entities} >= set(ENTITY_TYPES) | {"road", "river"}


@pytest.mark.asyncio
async def test_collect_survives_a_failing_request():
    with patch("src.knowledge_pipeline.collectors.osm_collector.aiohttp.ClientSession") as mock_client:
        mock_session = MagicMock()
        mock_session.post = MagicMock(side_effect=RuntimeError("network down"))
        mock_session.__aenter__ = AsyncMock(return_value=mock_session)
        mock_session.__aexit__ = AsyncMock(return_value=None)
        mock_client.return_value = mock_session

        entities = await OSMCollector().collect()

    assert entities == []


@pytest.mark.asyncio
async def test_collect_returns_partial_results_when_one_query_fails():
    """Test that when one Overpass query fails, others still succeed and results are aggregated."""
    one_element = {
        "elements": [{"type": "node", "id": 1, "lat": 21.0, "lon": 105.8, "tags": {"name": "X"}}]
    }

    # Create a mocked response for successful queries
    mock_resp = MagicMock()
    mock_resp.json = AsyncMock(return_value=one_element)
    mock_resp.__aenter__ = AsyncMock(return_value=mock_resp)
    mock_resp.__aexit__ = AsyncMock(return_value=None)

    # Total number of queries: entity_types + road_types + rivers
    total_queries = len(ENTITY_TYPES) + len(ROAD_TYPES["values"]) + len(NAMED_RIVERS)

    # Side effect: first query fails, all others succeed
    side_effect = [RuntimeError("first query down")] + [mock_resp] * (total_queries - 1)

    with patch("src.knowledge_pipeline.collectors.osm_collector.aiohttp.ClientSession") as mock_client:
        mock_session = MagicMock()
        mock_session.post = MagicMock(side_effect=side_effect)
        mock_session.__aenter__ = AsyncMock(return_value=mock_session)
        mock_session.__aexit__ = AsyncMock(return_value=None)
        mock_client.return_value = mock_session

        entities = await OSMCollector().collect()

    # Assert that results from the successful queries are returned (non-empty)
    assert len(entities) > 0, "Expected partial results from successful queries, but got empty list"
    # Verify no exception was raised (would have happened if one failure aborted the loop)


@pytest.mark.asyncio
async def test_collect_district_boundaries_returns_raw_elements():
    boundary_response = {"elements": [{"type": "relation", "id": 99, "tags": {"name": "Ba Dinh"}}]}
    with patch("src.knowledge_pipeline.collectors.osm_collector.aiohttp.ClientSession") as mock_client:
        mock_client.return_value = _mock_http_session(boundary_response)
        elements = await OSMCollector().collect_district_boundaries()

    assert elements == boundary_response["elements"]
