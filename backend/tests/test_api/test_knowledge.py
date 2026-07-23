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


@pytest.mark.asyncio
async def test_knowledge_summary_limit_over_cap_rejected(client):
    response = await client.get("/api/knowledge/summary?limit=99999")
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_knowledge_labels_not_configured(monkeypatch, client):
    monkeypatch.setattr(settings, "neo4j_uri", "")
    response = await client.get("/api/knowledge/labels")
    assert response.status_code == 200
    assert response.json() == []


@pytest.mark.asyncio
async def test_knowledge_labels_configured_returns_counts(monkeypatch, client):
    monkeypatch.setattr(settings, "neo4j_uri", "neo4j+s://fake")

    with patch(
        "src.api.routes.knowledge.Neo4jLoader.list_labels",
        return_value=[{"label": "District", "count": 12}, {"label": "Hospital", "count": 8}],
    ):
        response = await client.get("/api/knowledge/labels")

    assert response.status_code == 200
    assert response.json() == [{"label": "District", "count": 12}, {"label": "Hospital", "count": 8}]


@pytest.mark.asyncio
async def test_knowledge_entities_not_configured(monkeypatch, client):
    monkeypatch.setattr(settings, "neo4j_uri", "")
    response = await client.get("/api/knowledge/entities?label=District")
    assert response.status_code == 200
    assert response.json() == []


@pytest.mark.asyncio
async def test_knowledge_entities_configured_passes_label_and_limit(monkeypatch, client):
    monkeypatch.setattr(settings, "neo4j_uri", "neo4j+s://fake")

    with patch(
        "src.api.routes.knowledge.Neo4jLoader.list_entities_by_label",
        return_value=[{"name": "Hoan Kiem", "display_name": "Hoan Kiem District"}],
    ) as mock_list:
        response = await client.get("/api/knowledge/entities?label=District&limit=10")

    assert response.status_code == 200
    assert response.json() == [{"name": "Hoan Kiem", "display_name": "Hoan Kiem District"}]
    mock_list.assert_called_once_with("District", 10)


@pytest.mark.asyncio
async def test_knowledge_entities_limit_over_cap_rejected(client):
    response = await client.get("/api/knowledge/entities?label=District&limit=99999")
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_knowledge_entities_missing_label_rejected(client):
    response = await client.get("/api/knowledge/entities")
    assert response.status_code == 422
