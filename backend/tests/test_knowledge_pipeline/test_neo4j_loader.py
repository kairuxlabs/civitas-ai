from unittest.mock import MagicMock, patch

from src.knowledge_pipeline.loaders.neo4j_loader import Neo4jLoader
from src.utils.config import settings


def test_no_op_when_neo4j_not_configured(monkeypatch):
    monkeypatch.setattr(settings, "neo4j_uri", "")
    loader = Neo4jLoader()
    assert loader.upsert_nodes("Hospital", [{"id": "h1"}]) == 0
    assert loader.merge_relation_by_name("Flood", "Flood", "IMPACTS", "Hospital", "Bach Mai") is False


def test_upsert_nodes_runs_merge_query_with_rows(monkeypatch):
    monkeypatch.setattr(settings, "neo4j_uri", "neo4j+s://fake")
    monkeypatch.setattr(settings, "neo4j_user", "neo4j")
    monkeypatch.setattr(settings, "neo4j_password", "pw")

    mock_session = MagicMock()
    mock_driver = MagicMock()
    mock_driver.session.return_value.__enter__.return_value = mock_session
    mock_driver.session.return_value.__exit__.return_value = None

    with patch("src.knowledge_pipeline.loaders.neo4j_loader.GraphDatabase.driver", return_value=mock_driver):
        loader = Neo4jLoader()
        count = loader.upsert_nodes("Hospital", [{"id": "h1", "name": "Bach Mai"}])

    assert count == 1
    args, kwargs = mock_session.run.call_args
    assert "MERGE (n:Hospital {id: row.id})" in args[0]
    assert kwargs["rows"] == [{"id": "h1", "name": "Bach Mai"}]


def test_merge_relation_by_name_runs_merge_query(monkeypatch):
    monkeypatch.setattr(settings, "neo4j_uri", "neo4j+s://fake")
    monkeypatch.setattr(settings, "neo4j_user", "neo4j")
    monkeypatch.setattr(settings, "neo4j_password", "pw")

    mock_session = MagicMock()
    mock_driver = MagicMock()
    mock_driver.session.return_value.__enter__.return_value = mock_session
    mock_driver.session.return_value.__exit__.return_value = None

    with patch("src.knowledge_pipeline.loaders.neo4j_loader.GraphDatabase.driver", return_value=mock_driver):
        loader = Neo4jLoader()
        ok = loader.merge_relation_by_name("Flood", "Flood", "IMPACTS", "Hospital", "Bach Mai Hospital")

    assert ok is True
    args, kwargs = mock_session.run.call_args
    assert "MERGE (a:Flood {name: $from_name})" in args[0]
    assert "MERGE (b:Hospital {name: $to_name})" in args[0]
    assert "MERGE (a)-[:IMPACTS]->(b)" in args[0]
    assert kwargs == {"from_name": "Flood", "to_name": "Bach Mai Hospital"}


def test_upsert_nodes_returns_zero_on_driver_error(monkeypatch):
    monkeypatch.setattr(settings, "neo4j_uri", "neo4j+s://fake")
    monkeypatch.setattr(settings, "neo4j_user", "neo4j")
    monkeypatch.setattr(settings, "neo4j_password", "pw")

    mock_driver = MagicMock()
    mock_driver.session.side_effect = RuntimeError("connection refused")

    with patch("src.knowledge_pipeline.loaders.neo4j_loader.GraphDatabase.driver", return_value=mock_driver):
        loader = Neo4jLoader()
        count = loader.upsert_nodes("Hospital", [{"id": "h1"}])

    assert count == 0


def test_init_handles_driver_construction_failure(monkeypatch):
    """Verify that driver construction errors degrade to no-op instead of crashing."""
    monkeypatch.setattr(settings, "neo4j_uri", "neo4j+s://invalid-uri-scheme")
    monkeypatch.setattr(settings, "neo4j_user", "neo4j")
    monkeypatch.setattr(settings, "neo4j_password", "pw")

    with patch(
        "src.knowledge_pipeline.loaders.neo4j_loader.GraphDatabase.driver",
        side_effect=ValueError("invalid URI scheme")
    ):
        loader = Neo4jLoader()  # Should not raise

    # Verify it degraded to no-op
    assert loader.upsert_nodes("Hospital", [{"id": "h1"}]) == 0
    assert loader.merge_relation_by_name("Flood", "Flood", "IMPACTS", "Hospital", "Bach Mai") is False


def test_find_related_no_op_when_not_configured(monkeypatch):
    monkeypatch.setattr(settings, "neo4j_uri", "")
    loader = Neo4jLoader()
    assert loader.find_related(["Metro"]) == []


def test_find_related_no_op_when_keywords_empty(monkeypatch):
    monkeypatch.setattr(settings, "neo4j_uri", "neo4j+s://fake")
    monkeypatch.setattr(settings, "neo4j_user", "neo4j")
    monkeypatch.setattr(settings, "neo4j_password", "pw")

    mock_driver = MagicMock()
    with patch("src.knowledge_pipeline.loaders.neo4j_loader.GraphDatabase.driver", return_value=mock_driver):
        loader = Neo4jLoader()
        result = loader.find_related([])

    assert result == []
    mock_driver.session.assert_not_called()


def test_find_related_runs_query_and_maps_rows(monkeypatch):
    monkeypatch.setattr(settings, "neo4j_uri", "neo4j+s://fake")
    monkeypatch.setattr(settings, "neo4j_user", "neo4j")
    monkeypatch.setattr(settings, "neo4j_password", "pw")

    mock_session = MagicMock()
    mock_session.run.return_value = [
        {"name": "Metro Line 2A", "label": "Road", "relation": "CONNECTS", "related_name": "Cat Linh"},
    ]
    mock_driver = MagicMock()
    mock_driver.session.return_value.__enter__.return_value = mock_session
    mock_driver.session.return_value.__exit__.return_value = None

    with patch("src.knowledge_pipeline.loaders.neo4j_loader.GraphDatabase.driver", return_value=mock_driver):
        loader = Neo4jLoader()
        result = loader.find_related(["Metro"], limit=5)

    assert result == [
        {"name": "Metro Line 2A", "label": "Road", "relation": "CONNECTS", "related_name": "Cat Linh"},
    ]
    args, kwargs = mock_session.run.call_args
    assert "UNWIND $keywords AS kw" in args[0]
    assert "CONTAINS toLower(kw)" in args[0]
    assert kwargs == {"keywords": ["Metro"], "limit": 5}


def test_find_related_returns_empty_list_on_driver_error(monkeypatch):
    monkeypatch.setattr(settings, "neo4j_uri", "neo4j+s://fake")
    monkeypatch.setattr(settings, "neo4j_user", "neo4j")
    monkeypatch.setattr(settings, "neo4j_password", "pw")

    mock_driver = MagicMock()
    mock_driver.session.side_effect = RuntimeError("connection refused")

    with patch("src.knowledge_pipeline.loaders.neo4j_loader.GraphDatabase.driver", return_value=mock_driver):
        loader = Neo4jLoader()
        result = loader.find_related(["Metro"])

    assert result == []
