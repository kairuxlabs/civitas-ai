# backend/src/crawlers/news_crawler.py
"""News crawler: pulls the VnExpress thời-sự RSS feed, keeps urban/Hanoi
relevant items and stores them as Event rows (category="news").

Uses stdlib xml.etree — no new dependencies. Network failures raise and
are isolated by crawl_service.
"""
import xml.etree.ElementTree as ET
from datetime import datetime, timezone

import aiohttp
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.models.event import Event
from src.utils.logger import get_logger

logger = get_logger(__name__)

RSS_URL = "https://vnexpress.net/rss/thoi-su.rss"

_RELEVANT_KEYWORDS = (
    "hà nội", "giao thông", "ngập", "mưa", "ô nhiễm", "cháy", "tắc",
    "bão", "nắng nóng", "tai nạn", "úng", "không khí", "đô thị",
)
_HIGH_IMPACT = ("ngập", "cháy", "bão", "lũ", "tai nạn nghiêm trọng", "sập")
_MEDIUM_IMPACT = ("mưa lớn", "tắc", "ùn tắc", "ô nhiễm", "nắng nóng", "tai nạn")


async def fetch_rss(url: str = RSS_URL) -> str:
    timeout = aiohttp.ClientTimeout(total=15)
    async with aiohttp.ClientSession(timeout=timeout) as http:
        async with http.get(url) as resp:
            return await resp.text()


def parse_items(xml_text: str) -> list[dict]:
    root = ET.fromstring(xml_text)
    items = []
    for item in root.iter("item"):
        items.append({
            "title": (item.findtext("title") or "").strip(),
            "description": (item.findtext("description") or "").strip(),
            "link": (item.findtext("link") or "").strip(),
            "pub_date": (item.findtext("pubDate") or "").strip(),
        })
    return [i for i in items if i["title"]]


def _is_relevant(item: dict) -> bool:
    text = f"{item['title']} {item['description']}".lower()
    return any(kw in text for kw in _RELEVANT_KEYWORDS)


def impact_for(text: str) -> str:
    t = text.lower()
    if any(kw in t for kw in _HIGH_IMPACT):
        return "high"
    if any(kw in t for kw in _MEDIUM_IMPACT):
        return "medium"
    return "low"


async def crawl_news(session: AsyncSession) -> int:
    """Fetch, filter and store news items. Returns number of new events."""
    xml_text = await fetch_rss()
    items = [i for i in parse_items(xml_text) if _is_relevant(i)]
    if not items:
        return 0

    existing = set(
        (await session.execute(
            select(Event.title).where(Event.category == "news")
        )).scalars().all()
    )

    inserted = 0
    now = datetime.now(timezone.utc)
    for item in items:
        if item["title"] in existing:
            continue
        session.add(Event(
            city_id="hanoi",
            district_id=None,
            title=item["title"],
            category="news",
            start_time=now,
            impact_level=impact_for(f"{item['title']} {item['description']}"),
        ))
        existing.add(item["title"])
        inserted += 1

    await session.commit()
    logger.info(f"News crawl: {inserted} new events from {len(items)} relevant items")
    return inserted
