import asyncio

from fastapi import APIRouter, Query

from src.knowledge_pipeline.loaders.neo4j_loader import Neo4jLoader
from src.schemas.knowledge import KnowledgeEntityRef, KnowledgeLabelCount, KnowledgeSummaryOut
from src.utils.config import settings

router = APIRouter(prefix="/api/knowledge", tags=["knowledge"])


@router.get("/summary", response_model=KnowledgeSummaryOut)
async def knowledge_summary(q: str | None = None, limit: int = Query(default=5, le=100)):
    if not settings.neo4j_uri:
        return KnowledgeSummaryOut(configured=False, entities=0, relations=0, sample=[])

    keywords = [q] if q else ["Hanoi", "Hoan Kiem"]
    loader = Neo4jLoader()
    try:
        counts = await asyncio.to_thread(loader.count_summary)
        sample = await asyncio.to_thread(loader.find_related, keywords, limit)
    finally:
        loader.close()

    return KnowledgeSummaryOut(
        configured=True,
        entities=counts["entities"],
        relations=counts["relations"],
        sample=sample,
    )


@router.get("/labels", response_model=list[KnowledgeLabelCount])
async def knowledge_labels():
    if not settings.neo4j_uri:
        return []
    loader = Neo4jLoader()
    try:
        rows = await asyncio.to_thread(loader.list_labels)
    finally:
        loader.close()
    return [KnowledgeLabelCount(**r) for r in rows]


@router.get("/entities", response_model=list[KnowledgeEntityRef])
async def knowledge_entities(label: str, limit: int = Query(default=50, le=200)):
    if not settings.neo4j_uri:
        return []
    loader = Neo4jLoader()
    try:
        rows = await asyncio.to_thread(loader.list_entities_by_label, label, limit)
    finally:
        loader.close()
    return [KnowledgeEntityRef(**r) for r in rows]
