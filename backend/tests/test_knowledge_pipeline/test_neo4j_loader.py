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


def test_merge_relation_by_name_runs_merge_query_with_no_metadata(monkeypatch):
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
    assert "MERGE (a)-[r:IMPACTS]->(b)" in args[0]
    assert "SET r.source = $source, r.confidence = $confidence, r.created_at = $created_at" in args[0]
    assert kwargs == {
        "from_name": "Flood", "to_name": "Bach Mai Hospital",
        "source": None, "confidence": None, "created_at": None,
    }


def test_merge_relation_by_name_passes_through_metadata(monkeypatch):
    monkeypatch.setattr(settings, "neo4j_uri", "neo4j+s://fake")
    monkeypatch.setattr(settings, "neo4j_user", "neo4j")
    monkeypatch.setattr(settings, "neo4j_password", "pw")

    mock_session = MagicMock()
    mock_driver = MagicMock()
    mock_driver.session.return_value.__enter__.return_value = mock_session
    mock_driver.session.return_value.__exit__.return_value = None

    with patch("src.knowledge_pipeline.loaders.neo4j_loader.GraphDatabase.driver", return_value=mock_driver):
        loader = Neo4jLoader()
        loader.merge_relation_by_name(
            "Flood", "Flood", "IMPACTS", "Hospital", "Bach Mai Hospital",
            source="Wikipedia", confidence=None, created_at="2026-07-21T09:00:00+00:00",
        )

    _, kwargs = mock_session.run.call_args
    assert kwargs["source"] == "Wikipedia"
    assert kwargs["created_at"] == "2026-07-21T09:00:00+00:00"


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
        {
            "name": "Metro Line 2A", "label": "Road", "relation": "CONNECTS", "related_name": "Cat Linh",
            "rel_source": "Wikipedia", "rel_confidence": None, "rel_created_at": "2026-07-21T09:00:00+00:00",
        },
    ]
    mock_driver = MagicMock()
    mock_driver.session.return_value.__enter__.return_value = mock_session
    mock_driver.session.return_value.__exit__.return_value = None

    with patch("src.knowledge_pipeline.loaders.neo4j_loader.GraphDatabase.driver", return_value=mock_driver):
        loader = Neo4jLoader()
        result = loader.find_related(["Metro"], limit=5)

    assert result == [{
        "name": "Metro Line 2A", "label": "Road", "relation": "CONNECTS", "related_name": "Cat Linh",
        "rel_source": "Wikipedia", "rel_confidence": None, "rel_created_at": "2026-07-21T09:00:00+00:00",
    }]
    args, kwargs = mock_session.run.call_args
    assert "r.source AS rel_source" in args[0]
    assert "r.confidence AS rel_confidence" in args[0]
    assert "r.created_at AS rel_created_at" in args[0]
    assert kwargs == {"keywords": ["Metro"], "limit": 5}


def test_count_summary_no_op_when_not_configured(monkeypatch):
    monkeypatch.setattr(settings, "neo4j_uri", "")
    loader = Neo4jLoader()
    assert loader.count_summary() == {"entities": 0, "relations": 0}


def test_count_summary_runs_count_queries(monkeypatch):
    monkeypatch.setattr(settings, "neo4j_uri", "neo4j+s://fake")
    monkeypatch.setattr(settings, "neo4j_user", "neo4j")
    monkeypatch.setattr(settings, "neo4j_password", "pw")

    mock_session = MagicMock()
    mock_session.run.side_effect = [
        [{"count": 128}],
        [{"count": 426}],
    ]
    mock_driver = MagicMock()
    mock_driver.session.return_value.__enter__.return_value = mock_session
    mock_driver.session.return_value.__exit__.return_value = None

    with patch("src.knowledge_pipeline.loaders.neo4j_loader.GraphDatabase.driver", return_value=mock_driver):
        loader = Neo4jLoader()
        result = loader.count_summary()

    assert result == {"entities": 128, "relations": 426}


def test_count_summary_returns_zeros_on_driver_error(monkeypatch):
    monkeypatch.setattr(settings, "neo4j_uri", "neo4j+s://fake")
    monkeypatch.setattr(settings, "neo4j_user", "neo4j")
    monkeypatch.setattr(settings, "neo4j_password", "pw")

    mock_driver = MagicMock()
    mock_driver.session.side_effect = RuntimeError("connection refused")

    with patch("src.knowledge_pipeline.loaders.neo4j_loader.GraphDatabase.driver", return_value=mock_driver):
        loader = Neo4jLoader()
        result = loader.count_summary()

    assert result == {"entities": 0, "relations": 0}


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


# --- Cypher injection guard: unsafe label/rel_type rejection ---------------

def test_upsert_nodes_rejects_unsafe_label(monkeypatch):
    monkeypatch.setattr(settings, "neo4j_uri", "neo4j+s://fake")
    monkeypatch.setattr(settings, "neo4j_user", "neo4j")
    monkeypatch.setattr(settings, "neo4j_password", "pw")

    mock_driver = MagicMock()
    with patch("src.knowledge_pipeline.loaders.neo4j_loader.GraphDatabase.driver", return_value=mock_driver):
        loader = Neo4jLoader()
        count = loader.upsert_nodes("Hospital}) DETACH DELETE n //", [{"id": "h1"}])

    assert count == 0
    mock_driver.session.assert_not_called()


def test_upsert_nodes_accepts_known_valid_labels(monkeypatch):
    monkeypatch.setattr(settings, "neo4j_uri", "neo4j+s://fake")
    monkeypatch.setattr(settings, "neo4j_user", "neo4j")
    monkeypatch.setattr(settings, "neo4j_password", "pw")

    mock_session = MagicMock()
    mock_driver = MagicMock()
    mock_driver.session.return_value.__enter__.return_value = mock_session
    mock_driver.session.return_value.__exit__.return_value = None

    with patch("src.knowledge_pipeline.loaders.neo4j_loader.GraphDatabase.driver", return_value=mock_driver):
        loader = Neo4jLoader()
        for label in ("District", "Hospital"):
            count = loader.upsert_nodes(label, [{"id": "x1"}])
            assert count == 1


def test_merge_relation_by_name_rejects_unsafe_rel_type(monkeypatch):
    monkeypatch.setattr(settings, "neo4j_uri", "neo4j+s://fake")
    monkeypatch.setattr(settings, "neo4j_user", "neo4j")
    monkeypatch.setattr(settings, "neo4j_password", "pw")

    mock_driver = MagicMock()
    with patch("src.knowledge_pipeline.loaders.neo4j_loader.GraphDatabase.driver", return_value=mock_driver):
        loader = Neo4jLoader()
        ok = loader.merge_relation_by_name(
            "Flood", "Flood", "IMPACTS]->(b) DETACH DELETE b //", "Hospital", "Bach Mai",
        )

    assert ok is False
    mock_driver.session.assert_not_called()


def test_merge_relation_by_name_rejects_unsafe_from_or_to_label(monkeypatch):
    monkeypatch.setattr(settings, "neo4j_uri", "neo4j+s://fake")
    monkeypatch.setattr(settings, "neo4j_user", "neo4j")
    monkeypatch.setattr(settings, "neo4j_password", "pw")

    mock_driver = MagicMock()
    with patch("src.knowledge_pipeline.loaders.neo4j_loader.GraphDatabase.driver", return_value=mock_driver):
        loader = Neo4jLoader()
        ok = loader.merge_relation_by_name(
            "Flood}) DETACH DELETE (a", "Flood", "IMPACTS", "Hospital", "Bach Mai",
        )

    assert ok is False
    mock_driver.session.assert_not_called()


def test_merge_relation_by_name_accepts_valid_identifiers(monkeypatch):
    monkeypatch.setattr(settings, "neo4j_uri", "neo4j+s://fake")
    monkeypatch.setattr(settings, "neo4j_user", "neo4j")
    monkeypatch.setattr(settings, "neo4j_password", "pw")

    mock_session = MagicMock()
    mock_driver = MagicMock()
    mock_driver.session.return_value.__enter__.return_value = mock_session
    mock_driver.session.return_value.__exit__.return_value = None

    with patch("src.knowledge_pipeline.loaders.neo4j_loader.GraphDatabase.driver", return_value=mock_driver):
        loader = Neo4jLoader()
        ok = loader.merge_relation_by_name("District", "Hoan Kiem", "NEAR", "Hospital", "Bach Mai")

    assert ok is True
