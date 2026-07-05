import pytest
from sqlalchemy import select

import src.crawlers.news_crawler as news_mod
from src.crawlers.crawl_service import run_crawl
from src.crawlers.news_crawler import crawl_news, impact_for, parse_items
from src.models.event import Event

FIXTURE_RSS = """<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0">
  <channel>
    <title>Tin thời sự</title>
    <item>
      <title>Hà Nội mưa lớn, nhiều tuyến phố ngập sâu</title>
      <description><![CDATA[Mưa lớn kéo dài gây ngập úng nhiều nơi tại Hà Nội.]]></description>
      <link>https://example.com/1</link>
      <pubDate>Sat, 05 Jul 2026 08:00:00 +0700</pubDate>
    </item>
    <item>
      <title>Giá vàng tăng mạnh phiên cuối tuần</title>
      <description>Thị trường vàng biến động.</description>
      <link>https://example.com/2</link>
      <pubDate>Sat, 05 Jul 2026 07:00:00 +0700</pubDate>
    </item>
    <item>
      <title>Cháy lớn tại kho hàng ở Hà Nội, huy động nhiều xe cứu hỏa</title>
      <description>Đám cháy bùng phát lúc rạng sáng.</description>
      <link>https://example.com/3</link>
      <pubDate>Sat, 05 Jul 2026 06:00:00 +0700</pubDate>
    </item>
  </channel>
</rss>"""


def test_parse_items_extracts_fields():
    items = parse_items(FIXTURE_RSS)
    assert len(items) == 3
    assert items[0]["title"].startswith("Hà Nội mưa lớn")
    assert items[0]["link"] == "https://example.com/1"


def test_impact_heuristic():
    assert impact_for("Hà Nội ngập sâu sau mưa") == "high"
    assert impact_for("Cháy lớn tại kho hàng") == "high"
    assert impact_for("Ùn tắc kéo dài trên vành đai 3") == "medium"
    assert impact_for("Khai mạc triển lãm tranh") == "low"


@pytest.mark.asyncio
async def test_crawl_news_filters_and_dedupes(db_session, monkeypatch):
    async def fake_fetch(url: str = "") -> str:
        return FIXTURE_RSS

    monkeypatch.setattr(news_mod, "fetch_rss", fake_fetch)

    inserted = await crawl_news(db_session)
    # "Giá vàng" item is not urban-relevant → only 2 inserted
    assert inserted == 2

    rows = (await db_session.execute(select(Event).where(Event.category == "news"))).scalars().all()
    assert len(rows) == 2
    assert any(r.impact_level == "high" for r in rows)

    # second crawl inserts nothing (dedupe by title)
    assert await crawl_news(db_session) == 0


@pytest.mark.asyncio
async def test_run_crawl_isolates_failures(db_session, monkeypatch):
    async def ok(session):
        return 3

    async def boom(session):
        raise RuntimeError("network down")

    monkeypatch.setitem(run_crawl.__globals__["CRAWLERS"], "news", ok)
    monkeypatch.setitem(run_crawl.__globals__["CRAWLERS"], "weather", boom)

    result = await run_crawl(["weather", "news", "unknown"], db_session)
    assert result["news"] == {"ok": True, "count": 3}
    assert result["weather"]["ok"] is False
    assert "network down" in result["weather"]["error"]
    assert result["unknown"]["ok"] is False
