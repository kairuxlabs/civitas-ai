import asyncio

import pytest
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from unittest.mock import AsyncMock, patch

from src.knowledge_pipeline import scheduler as kp_scheduler


@pytest.mark.asyncio
async def test_register_skips_when_no_llm_key_configured(monkeypatch):
    monkeypatch.setattr("src.utils.config.settings.gemini_api_key", "")
    monkeypatch.setattr("src.utils.config.settings.openrouter_api_key", "")

    scheduler = AsyncIOScheduler()
    registered = kp_scheduler.register(scheduler)

    assert registered is False
    assert scheduler.get_job("wikipedia_refresh") is None


@pytest.mark.asyncio
async def test_register_adds_weekly_job_when_gemini_key_configured(monkeypatch):
    monkeypatch.setattr("src.utils.config.settings.gemini_api_key", "test-key")
    monkeypatch.setattr("src.utils.config.settings.openrouter_api_key", "")

    scheduler = AsyncIOScheduler()
    registered = kp_scheduler.register(scheduler)

    assert registered is True
    job = scheduler.get_job("wikipedia_refresh")
    assert job is not None


@pytest.mark.asyncio
async def test_register_adds_weekly_job_when_openrouter_key_configured(monkeypatch):
    monkeypatch.setattr("src.utils.config.settings.gemini_api_key", "")
    monkeypatch.setattr("src.utils.config.settings.openrouter_api_key", "test-key")

    scheduler = AsyncIOScheduler()
    registered = kp_scheduler.register(scheduler)

    assert registered is True
    assert scheduler.get_job("wikipedia_refresh") is not None


@pytest.mark.asyncio
async def test_refresh_wikipedia_loads_chunks_off_the_event_loop_thread():
    result_holder = {}

    def fake_load_chunks(chunks):
        try:
            asyncio.get_running_loop()
            result_holder["called_on_loop_thread"] = True
        except RuntimeError:
            result_holder["called_on_loop_thread"] = False
        return len(chunks)

    with patch.object(kp_scheduler, "WikipediaCollector") as mock_wiki_cls, \
         patch.object(kp_scheduler.qdrant_loader, "load_chunks", side_effect=fake_load_chunks):
        mock_wiki_cls.return_value.collect = AsyncMock(return_value=[
            {"title": "Flood", "content": "Flood text.", "language": "en", "category": "disaster", "source": "Wikipedia", "confidence": 0.85}
        ])

        count = await kp_scheduler.refresh_wikipedia()

    assert result_holder["called_on_loop_thread"] is False
    assert count == 1


@pytest.mark.asyncio
async def test_refresh_wikipedia_survives_collector_failure():
    with patch.object(kp_scheduler, "WikipediaCollector") as mock_wiki_cls:
        mock_wiki_cls.return_value.collect = AsyncMock(side_effect=RuntimeError("Wikipedia API down"))

        count = await kp_scheduler.refresh_wikipedia()

    assert count == 0
