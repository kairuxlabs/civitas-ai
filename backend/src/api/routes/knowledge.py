import asyncio

from fastapi import APIRouter, Query

from src.knowledge_pipeline.loaders.neo4j_loader import Neo4jLoader
from src.schemas.knowledge import KnowledgeSummaryOut
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
