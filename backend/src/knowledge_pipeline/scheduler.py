"""Knowledge pipeline v2: weekly automated Wikipedia refresh.

Re-runs WikipediaCollector.collect() on a schedule, re-chunks and re-embeds
the result, and upserts into the same `city_knowledge` Qdrant collection.
OSM / Government PDF / GeoJSON change rarely and stay manual — re-run
bootstrap.py by hand when they do.

qdrant_loader.load_chunks() is already idempotent (deterministic point ids
derived from title + chunk_index), so re-running this weekly is safe
without any loader changes — unchanged pages simply upsert onto the same
points with identical payloads.

See docs/superpowers/specs/2026-07-05-knowledge-bootstrap-pipeline-design.md
for the original v1/v2/v3 roadmap this implements.
"""
import asyncio

from apscheduler.schedulers.asyncio import AsyncIOScheduler

from src.knowledge_pipeline.bootstrap import _docs_to_chunks
from src.knowledge_pipeline.collectors.wikipedia_collector import WikipediaCollector
from src.knowledge_pipeline.loaders import qdrant_loader
from src.utils.config import settings
from src.utils.logger import get_logger

logger = get_logger(__name__)


async def refresh_wikipedia() -> int:
    """Re-collect all Wikipedia topics and idempotently upsert their chunks
    into the `city_knowledge` Qdrant collection. Returns the number of
    chunks upserted (0 on any failure — this step fails in isolation,
    matching bootstrap.py's per-step error handling convention)."""
    try:
        docs = await WikipediaCollector().collect()
    except Exception as e:
        logger.warning(f"Wikipedia refresh collection failed: {e}")
        return 0

    chunks = _docs_to_chunks(docs)
    count = await asyncio.to_thread(qdrant_loader.load_chunks, chunks)
    logger.info(f"Wikipedia refresh upserted {count} chunks")
    return count


def register(scheduler: AsyncIOScheduler) -> bool:
    """Register the weekly Wikipedia refresh job (Mondays 03:00) if an LLM
    key is configured. Returns True if registered, False if skipped."""
    if not (settings.gemini_api_key or settings.openrouter_api_key):
        logger.info("Knowledge pipeline weekly refresh skipped: no LLM key configured")
        return False

    scheduler.add_job(refresh_wikipedia, "cron", day_of_week="mon", hour=3, id="wikipedia_refresh")
    logger.info("Knowledge pipeline weekly refresh registered (Mondays 03:00)")
    return True
