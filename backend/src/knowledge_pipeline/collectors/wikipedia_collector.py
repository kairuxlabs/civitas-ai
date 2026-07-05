import aiohttp

from src.knowledge_pipeline.collectors.base import BaseCollector
from src.knowledge_pipeline.parsers.wikipedia_parser import parse_wikipedia_page
from src.utils.logger import get_logger

logger = get_logger(__name__)

WIKIPEDIA_API_URL = "https://en.wikipedia.org/w/api.php"

# (title, category) — organized by category for easy extension later.
TOPICS: list[tuple[str, str]] = [
    ("Hanoi", "city"),
    ("Flood", "disaster"),
    ("Natural disaster", "disaster"),
    ("Transportation", "transportation"),
    ("Public health", "healthcare"),
    ("Air pollution", "environment"),
    ("Climate change", "environment"),
    ("Emergency management", "emergency"),
]


class WikipediaCollector(BaseCollector):
    async def collect(self) -> list[dict]:
        docs: list[dict] = []
        async with aiohttp.ClientSession() as http:
            for title, category in TOPICS:
                try:
                    params = {
                        "action": "query", "prop": "extracts", "explaintext": 1,
                        "titles": title, "format": "json", "redirects": 1,
                    }
                    async with http.get(WIKIPEDIA_API_URL, params=params) as resp:
                        data = await resp.json()
                    pages = data.get("query", {}).get("pages", {})
                    for page in pages.values():
                        doc = parse_wikipedia_page(page, category)
                        if doc:
                            docs.append(doc)
                except Exception as e:
                    logger.warning(f"Wikipedia collector failed for '{title}': {e}")
        return docs
