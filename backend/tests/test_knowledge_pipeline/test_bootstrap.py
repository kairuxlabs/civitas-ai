# backend/tests/test_knowledge_pipeline/test_bootstrap.py
import pytest
from unittest.mock import AsyncMock, patch

from src.knowledge_pipeline import bootstrap as bootstrap_module


@pytest.mark.asyncio
async def test_bootstrap_aggregates_summary_from_all_steps(monkeypatch, db_session):
    # AsyncSessionLocal is normally an async context manager factory; db_session
    # fixture already yields a usable AsyncSession, so wrap it minimally:
    class _CtxWrapper:
        async def __aenter__(self):
            return db_session
        async def __aexit__(self, *exc):
            return None
    monkeypatch.setattr(bootstrap_module, "AsyncSessionLocal", lambda: _CtxWrapper())

    with patch.object(bootstrap_module, "OSMCollector") as mock_osm_cls, \
         patch.object(bootstrap_module, "WikidataCollector") as mock_wikidata_cls, \
         patch.object(bootstrap_module, "WikipediaCollector") as mock_wiki_cls, \
         patch.object(bootstrap_module, "GovernmentPDFCollector") as mock_pdf_cls, \
         patch.object(bootstrap_module, "Neo4jLoader") as mock_neo4j_cls, \
         patch.object(bootstrap_module.graph_builder, "build_entity_graph", return_value={"Hospital": 1}), \
         patch.object(bootstrap_module.graph_builder, "build_relation_graph", return_value=0), \
         patch.object(bootstrap_module.postgres_loader, "update_district_geojson", new=AsyncMock(return_value=1)), \
         patch.object(bootstrap_module.qdrant_loader, "load_chunks", return_value=2), \
         patch.object(bootstrap_module, "extract_entities", return_value={"entities": [], "relations": []}):

        mock_osm = mock_osm_cls.return_value
        mock_osm.collect = AsyncMock(return_value=[{"id": "hospital_1", "type": "hospital", "name": "A", "metadata": {}}])
        mock_osm.collect_district_boundaries = AsyncMock(return_value=[])

        mock_wikidata_cls.return_value.collect = AsyncMock(return_value=[])
        mock_wiki_cls.return_value.collect = AsyncMock(return_value=[
            {"title": "Flood", "content": "Flood text.", "language": "en", "category": "disaster", "source": "Wikipedia", "confidence": 0.85}
        ])
        mock_pdf_cls.return_value.collect = AsyncMock(return_value=[])
        mock_neo4j_cls.return_value.close = lambda: None

        summary = await bootstrap_module.bootstrap()

    assert summary["neo4j_nodes"] == {"Hospital": 1}
    assert summary["districts_updated"] == 1
    assert summary["qdrant_chunks"] == 2


@pytest.mark.asyncio
async def test_bootstrap_survives_osm_collector_failure(monkeypatch, db_session):
    class _CtxWrapper:
        async def __aenter__(self):
            return db_session
        async def __aexit__(self, *exc):
            return None
    monkeypatch.setattr(bootstrap_module, "AsyncSessionLocal", lambda: _CtxWrapper())

    with patch.object(bootstrap_module, "OSMCollector") as mock_osm_cls, \
         patch.object(bootstrap_module, "WikidataCollector") as mock_wikidata_cls, \
         patch.object(bootstrap_module, "WikipediaCollector") as mock_wiki_cls, \
         patch.object(bootstrap_module, "GovernmentPDFCollector") as mock_pdf_cls, \
         patch.object(bootstrap_module.postgres_loader, "update_district_geojson", new=AsyncMock(return_value=0)), \
         patch.object(bootstrap_module.qdrant_loader, "load_chunks", return_value=0):

        mock_osm_cls.return_value.collect = AsyncMock(side_effect=RuntimeError("Overpass down"))
        mock_osm_cls.return_value.collect_district_boundaries = AsyncMock(side_effect=RuntimeError("Overpass down"))
        mock_wikidata_cls.return_value.collect = AsyncMock(return_value=[])
        mock_wiki_cls.return_value.collect = AsyncMock(return_value=[])
        mock_pdf_cls.return_value.collect = AsyncMock(return_value=[])

        summary = await bootstrap_module.bootstrap()

    assert "neo4j_nodes" not in summary
    assert summary["qdrant_chunks"] == 0


@pytest.mark.asyncio
async def test_bootstrap_survives_chunking_failure(monkeypatch, db_session):
    class _CtxWrapper:
        async def __aenter__(self):
            return db_session
        async def __aexit__(self, *exc):
            return None
    monkeypatch.setattr(bootstrap_module, "AsyncSessionLocal", lambda: _CtxWrapper())

    with patch.object(bootstrap_module, "OSMCollector") as mock_osm_cls, \
         patch.object(bootstrap_module, "WikidataCollector") as mock_wikidata_cls, \
         patch.object(bootstrap_module, "WikipediaCollector") as mock_wiki_cls, \
         patch.object(bootstrap_module, "GovernmentPDFCollector") as mock_pdf_cls, \
         patch.object(bootstrap_module, "Neo4jLoader") as mock_neo4j_cls, \
         patch.object(bootstrap_module.graph_builder, "build_entity_graph", return_value={"Hospital": 1}), \
         patch.object(bootstrap_module.postgres_loader, "update_district_geojson", new=AsyncMock(return_value=1)), \
         patch.object(bootstrap_module, "_docs_to_chunks", side_effect=RuntimeError("chunking exploded")), \
         patch.object(bootstrap_module.qdrant_loader, "load_chunks", return_value=0):

        mock_osm = mock_osm_cls.return_value
        mock_osm.collect = AsyncMock(return_value=[{"id": "hospital_1", "type": "hospital", "name": "A", "metadata": {}}])
        mock_osm.collect_district_boundaries = AsyncMock(return_value=[])

        mock_wikidata_cls.return_value.collect = AsyncMock(return_value=[])
        mock_wiki_cls.return_value.collect = AsyncMock(return_value=[
            {"title": "Flood", "content": "Flood text.", "language": "en", "category": "disaster", "source": "Wikipedia", "confidence": 0.85}
        ])
        mock_pdf_cls.return_value.collect = AsyncMock(return_value=[])
        mock_neo4j_cls.return_value.close = lambda: None

        summary = await bootstrap_module.bootstrap()

    assert summary["neo4j_nodes"] == {"Hospital": 1}
    assert summary["qdrant_chunks"] == 0
    assert "neo4j_relations" not in summary
