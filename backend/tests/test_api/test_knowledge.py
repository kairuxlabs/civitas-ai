import pytest
from unittest.mock import patch

from src.utils.config import settings


@pytest.mark.asyncio
async def test_knowledge_summary_not_configured(monkeypatch, client):
    monkeypatch.setattr(settings, "neo4j_uri", "")

    response = await client.get("/api/knowledge/summary")
    assert response.status_code == 200
    data = response.json()
    assert data["configured"] is False
    assert data["entities"] == 0
    assert data["relations"] == 0
    assert data["sample"] == []


@pytest.mark.asyncio
async def test_knowledge_summary_configured_returns_counts_and_sample(monkeypatch, client):
    monkeypatch.setattr(settings, "neo4j_uri", "neo4j+s://fake")

    with patch(
        "src.api.routes.knowledge.Neo4jLoader.count_summary",
        return_value={"entities": 128, "relations": 426},
    ), patch(
        "src.api.routes.knowledge.Neo4jLoader.find_related",
        return_value=[
            {
                "name": "Hoan Kiem", "label": "District", "relation": "NEAR",
                "related_name": "Old Quarter", "rel_source": "OSM",
                "rel_confidence": None, "rel_created_at": None,
            },
        ],
    ):
        response = await client.get("/api/knowledge/summary")

    assert response.status_code == 200
    data = response.json()
    assert data["configured"] is True
    assert data["entities"] == 128
    assert data["relations"] == 426
    assert data["sample"][0]["name"] == "Hoan Kiem"


@pytest.mark.asyncio
async def test_knowledge_summary_search_uses_query_as_keyword(monkeypatch, client):
    monkeypatch.setattr(settings, "neo4j_uri", "neo4j+s://fake")

    with patch(
        "src.api.routes.knowledge.Neo4jLoader.count_summary",
        return_value={"entities": 128, "relations": 426},
    ), patch(
        "src.api.routes.knowledge.Neo4jLoader.find_related",
        return_value=[],
    ) as mock_find_related:
        response = await client.get("/api/knowledge/summary?q=Cau+Giay&limit=10")

    assert response.status_code == 200
    mock_find_related.assert_called_once_with(["Cau Giay"], 10)
