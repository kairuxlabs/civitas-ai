# backend/src/knowledge_pipeline/bootstrap.py
import asyncio

from src.database.connection import AsyncSessionLocal
from src.knowledge_pipeline.collectors.geojson_collector import build_district_geojson
from src.knowledge_pipeline.collectors.government_pdf_collector import GovernmentPDFCollector
from src.knowledge_pipeline.collectors.osm_collector import OSMCollector
from src.knowledge_pipeline.collectors.wikidata_collector import WikidataCollector
from src.knowledge_pipeline.collectors.wikipedia_collector import WikipediaCollector
from src.knowledge_pipeline.loaders import postgres_loader, qdrant_loader
from src.knowledge_pipeline.loaders.neo4j_loader import Neo4jLoader
from src.knowledge_pipeline.processors import graph_builder
from src.knowledge_pipeline.processors.chunking import chunk_text
from src.knowledge_pipeline.processors.cleaner import clean_text
from src.knowledge_pipeline.processors.entity_extractor import extract_entities
from src.knowledge_pipeline.processors.metadata_builder import build_chunk_metadata
from src.utils.logger import get_logger

logger = get_logger(__name__)


def _docs_to_chunks(docs: list[dict]) -> list[dict]:
    chunks = []
    for doc in docs:
        cleaned = clean_text(doc["content"])
        for i, piece in enumerate(chunk_text(cleaned)):
            chunks.append(build_chunk_metadata(piece, doc, i))
    return chunks


async def bootstrap() -> dict:
    summary: dict = {}
    osm = OSMCollector()

    # 1. OSM entities -> Neo4j nodes
    entities: list[dict] = []
    try:
        entities = await osm.collect()
        loader = Neo4jLoader()
        summary["neo4j_nodes"] = graph_builder.build_entity_graph(entities, loader)
        loader.close()
    except Exception as e:
        logger.warning(f"OSM -> Neo4j step failed: {e}")

    # 2. District admin boundaries -> Postgres districts.geojson
    try:
        boundary_elements = await osm.collect_district_boundaries()
        district_geojson = build_district_geojson(boundary_elements)
        async with AsyncSessionLocal() as session:
            summary["districts_updated"] = await postgres_loader.update_district_geojson(session, district_geojson)
    except Exception as e:
        logger.warning(f"GeoJSON -> Postgres step failed: {e}")

    # 3. Wikidata enrichment (best-effort, mutates `entities` in place)
    try:
        enriched = await WikidataCollector(entities).collect()
        summary["wikidata_enriched"] = len(enriched)
    except Exception as e:
        logger.warning(f"Wikidata enrichment step failed: {e}")

    # 4. Wikipedia + Government PDF -> chunks -> Qdrant
    docs: list[dict] = []
    try:
        docs.extend(await WikipediaCollector().collect())
    except Exception as e:
        logger.warning(f"Wikipedia collection failed: {e}")
    try:
        docs.extend(await GovernmentPDFCollector().collect())
    except Exception as e:
        logger.warning(f"Government PDF collection failed: {e}")

    chunks = _docs_to_chunks(docs)
    try:
        summary["qdrant_chunks"] = qdrant_loader.load_chunks(chunks)
    except Exception as e:
        logger.warning(f"Qdrant load step failed: {e}")

    # 5. Entity extraction over the same chunks -> Neo4j relations
    relations: list[dict] = []
    for chunk in chunks:
        try:
            extraction = extract_entities(chunk["content"])
            type_by_name = {e["name"]: e["type"] for e in extraction.get("entities", []) if e.get("name")}
            for rel in extraction.get("relations", []):
                from_name, to_name = rel.get("from", ""), rel.get("to", "")
                if not from_name or not to_name:
                    continue
                relations.append({
                    "from_type": type_by_name.get(from_name, "concept"),
                    "from_name": from_name,
                    "rel": rel.get("relation", "RELATED_TO").upper().replace(" ", "_"),
                    "to_type": type_by_name.get(to_name, "concept"),
                    "to_name": to_name,
                })
        except Exception as e:
            logger.warning(f"Entity extraction failed for a chunk: {e}")

    if relations:
        try:
            loader = Neo4jLoader()
            summary["neo4j_relations"] = graph_builder.build_relation_graph(relations, loader)
            loader.close()
        except Exception as e:
            logger.warning(f"Relation graph step failed: {e}")

    logger.info(f"Bootstrap complete: {summary}")
    return summary


if __name__ == "__main__":
    asyncio.run(bootstrap())
