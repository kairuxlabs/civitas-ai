# backend/tests/test_knowledge_pipeline/test_bootstrap.py
import asyncio

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
async def test_bootstrap_upserts_entities_after_wikidata_enrichment(monkeypatch, db_session):
    """Regression test for the whole-branch review finding: Wikidata
    enrichment must run BEFORE the Neo4j upsert so enriched fields (and the
    bumped confidence) actually reach `build_entity_graph`/`upsert_nodes`."""
    class _CtxWrapper:
        async def __aenter__(self):
            return db_session
        async def __aexit__(self, *exc):
            return None
    monkeypatch.setattr(bootstrap_module, "AsyncSessionLocal", lambda: _CtxWrapper())

    entity = {
        "id": "hospital_1", "type": "hospital", "name": "A", "confidence": 1.0,
        "metadata": {"wikidata_qid": "Q194189"},
    }

    def fake_enrich(entities):
        # Mimic WikidataCollector.collect() mutating entities in place.
        for e in entities:
            e["metadata"]["wikidata_label"] = "Bach Mai Hospital"
            e["metadata"]["wikidata_instance_of"] = "hospital"
            e["confidence"] = 0.9
        return list(entities)

    captured_entities = {}

    def fake_build_entity_graph(entities, loader):
        captured_entities["entities"] = [dict(e) for e in entities]
        return {"Hospital": len(entities)}

    with patch.object(bootstrap_module, "OSMCollector") as mock_osm_cls, \
         patch.object(bootstrap_module, "WikidataCollector") as mock_wikidata_cls, \
         patch.object(bootstrap_module, "WikipediaCollector") as mock_wiki_cls, \
         patch.object(bootstrap_module, "GovernmentPDFCollector") as mock_pdf_cls, \
         patch.object(bootstrap_module, "Neo4jLoader") as mock_neo4j_cls, \
         patch.object(bootstrap_module.graph_builder, "build_entity_graph", side_effect=fake_build_entity_graph), \
         patch.object(bootstrap_module.graph_builder, "build_relation_graph", return_value=0), \
         patch.object(bootstrap_module.postgres_loader, "update_district_geojson", new=AsyncMock(return_value=1)), \
         patch.object(bootstrap_module.qdrant_loader, "load_chunks", return_value=0), \
         patch.object(bootstrap_module, "extract_entities", return_value={"entities": [], "relations": []}):

        mock_osm = mock_osm_cls.return_value
        mock_osm.collect = AsyncMock(return_value=[entity])
        mock_osm.collect_district_boundaries = AsyncMock(return_value=[])

        mock_wikidata_cls.return_value.collect = AsyncMock(side_effect=lambda: fake_enrich(mock_osm.collect.return_value))
        mock_wiki_cls.return_value.collect = AsyncMock(return_value=[])
        mock_pdf_cls.return_value.collect = AsyncMock(return_value=[])
        mock_neo4j_cls.return_value.close = lambda: None

        summary = await bootstrap_module.bootstrap()

    assert summary["wikidata_enriched"] == 1
    assert summary["neo4j_nodes"] == {"Hospital": 1}
    upserted = captured_entities["entities"][0]
    assert upserted["confidence"] == 0.9
    assert upserted["metadata"]["wikidata_label"] == "Bach Mai Hospital"


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

    # OSM collection failing degrades independently: the Wikidata enrichment
    # and Neo4j upsert steps still run (on an empty entity list) rather than
    # being skipped as a cascading side effect of the OSM failure.
    assert summary["wikidata_enriched"] == 0
    assert summary["neo4j_nodes"] == {}
    assert summary["qdrant_chunks"] == 0


@pytest.mark.asyncio
async def test_bootstrap_survives_wikidata_failure_and_still_upserts_to_neo4j(monkeypatch, db_session):
    """A Wikidata enrichment failure must not cascade into skipping the
    Neo4j upsert — the un-enriched OSM entities should still be upserted."""
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
         patch.object(bootstrap_module.postgres_loader, "update_district_geojson", new=AsyncMock(return_value=0)), \
         patch.object(bootstrap_module.qdrant_loader, "load_chunks", return_value=0):

        mock_osm = mock_osm_cls.return_value
        mock_osm.collect = AsyncMock(return_value=[{"id": "hospital_1", "type": "hospital", "name": "A", "metadata": {}}])
        mock_osm.collect_district_boundaries = AsyncMock(return_value=[])
        mock_wikidata_cls.return_value.collect = AsyncMock(side_effect=RuntimeError("Wikidata down"))
        mock_wiki_cls.return_value.collect = AsyncMock(return_value=[])
        mock_pdf_cls.return_value.collect = AsyncMock(return_value=[])
        mock_neo4j_cls.return_value.close = lambda: None

        summary = await bootstrap_module.bootstrap()

    assert "wikidata_enriched" not in summary
    assert summary["neo4j_nodes"] == {"Hospital": 1}


@pytest.mark.asyncio
async def test_bootstrap_calls_extract_entities_off_the_event_loop_thread(monkeypatch, db_session):
    """extract_entities() -> call_gemini() may bridge to the OpenRouter fallback
    via asyncio.run(), which raises if invoked while a loop is already running
    on the calling thread. bootstrap() is itself a coroutine, so this call must
    go through asyncio.to_thread (matching every other call_gemini call site
    in this codebase) rather than being invoked directly."""
    class _CtxWrapper:
        async def __aenter__(self):
            return db_session
        async def __aexit__(self, *exc):
            return None
    monkeypatch.setattr(bootstrap_module, "AsyncSessionLocal", lambda: _CtxWrapper())

    result_holder = {}

    def fake_extract_entities(chunk_text):
        try:
            asyncio.get_running_loop()
            result_holder["called_on_loop_thread"] = True
        except RuntimeError:
            result_holder["called_on_loop_thread"] = False
        return {"entities": [], "relations": []}

    with patch.object(bootstrap_module, "OSMCollector") as mock_osm_cls, \
         patch.object(bootstrap_module, "WikidataCollector") as mock_wikidata_cls, \
         patch.object(bootstrap_module, "WikipediaCollector") as mock_wiki_cls, \
         patch.object(bootstrap_module, "GovernmentPDFCollector") as mock_pdf_cls, \
         patch.object(bootstrap_module, "Neo4jLoader") as mock_neo4j_cls, \
         patch.object(bootstrap_module.graph_builder, "build_entity_graph", return_value={}), \
         patch.object(bootstrap_module.postgres_loader, "update_district_geojson", new=AsyncMock(return_value=0)), \
         patch.object(bootstrap_module.qdrant_loader, "load_chunks", return_value=0), \
         patch.object(bootstrap_module, "extract_entities", side_effect=fake_extract_entities):

        mock_osm = mock_osm_cls.return_value
        mock_osm.collect = AsyncMock(return_value=[])
        mock_osm.collect_district_boundaries = AsyncMock(return_value=[])
        mock_wikidata_cls.return_value.collect = AsyncMock(return_value=[])
        mock_wiki_cls.return_value.collect = AsyncMock(return_value=[
            {"title": "Flood", "content": "Flood text.", "language": "en", "category": "disaster", "source": "Wikipedia", "confidence": 0.85}
        ])
        mock_pdf_cls.return_value.collect = AsyncMock(return_value=[])
        mock_neo4j_cls.return_value.close = lambda: None

        await bootstrap_module.bootstrap()

    assert result_holder["called_on_loop_thread"] is False


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
