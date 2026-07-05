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
