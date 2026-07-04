# backend/src/crawlers/crawl_service.py
"""On-demand crawl dispatcher. Each source runs independently; failures
are captured per-source so one dead API never breaks the request."""
from sqlalchemy.ext.asyncio import AsyncSession

from src.crawlers.news_crawler import crawl_news
from src.pipelines.aqi_pipeline import AQIPipeline
from src.pipelines.weather_pipeline import WeatherPipeline
from src.utils.logger import get_logger

logger = get_logger(__name__)

CRAWLERS = {
    "weather": WeatherPipeline.run,
    "aqi": AQIPipeline.run,
    "news": crawl_news,
}

ALL_SOURCES = list(CRAWLERS)


async def run_crawl(sources: list[str], session: AsyncSession) -> dict[str, dict]:
    results: dict[str, dict] = {}
    for source in sources:
        crawler = CRAWLERS.get(source)
        if crawler is None:
            results[source] = {"ok": False, "error": f"Unknown source. Available: {ALL_SOURCES}"}
            continue
        try:
            count = await crawler(session)
            results[source] = {"ok": True, "count": count} if count is not None else {"ok": True}
        except Exception as e:
            logger.warning(f"Crawl '{source}' failed: {e}")
            results[source] = {"ok": False, "error": str(e)}
    return results
