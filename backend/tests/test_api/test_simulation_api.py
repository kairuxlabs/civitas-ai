import pytest

from src.crawlers import crawl_service
from src.simulation.engine import simulation


@pytest.fixture(autouse=True)
async def stop_simulation_after():
    yield
    await simulation.stop()


@pytest.mark.asyncio
async def test_simulation_start_status_stop(client, monkeypatch):
    monkeypatch.setattr(simulation, "_persist_enabled", False)

    resp = await client.post("/api/v2/simulation/start", json={"scenario": "heavy_rain", "interval_s": 60})
    assert resp.status_code == 200
    body = resp.json()
    assert body["running"] is True
    assert body["scenario"] == "heavy_rain"

    status = (await client.get("/api/v2/simulation/status")).json()
    assert status["running"] is True
    assert status["scenario_label"]

    stopped = (await client.post("/api/v2/simulation/stop")).json()
    assert stopped["running"] is False


@pytest.mark.asyncio
async def test_simulation_unknown_scenario_422(client):
    resp = await client.post("/api/v2/simulation/start", json={"scenario": "zombie"})
    assert resp.status_code == 422


@pytest.mark.asyncio
async def test_simulation_interval_minimum_enforced(client):
    resp = await client.post("/api/v2/simulation/start", json={"scenario": "normal", "interval_s": 0.001})
    assert resp.status_code == 422


@pytest.mark.asyncio
async def test_crawl_endpoint(client, monkeypatch):
    async def ok(session):
        return 5

    async def fail(session):
        raise RuntimeError("offline")

    monkeypatch.setitem(crawl_service.CRAWLERS, "news", ok)
    monkeypatch.setitem(crawl_service.CRAWLERS, "weather", ok)
    monkeypatch.setitem(crawl_service.CRAWLERS, "aqi", fail)

    resp = await client.post("/api/v2/crawl", json={"sources": ["weather", "aqi", "news"]})
    assert resp.status_code == 200
    body = resp.json()
    assert body["results"]["news"]["ok"] is True
    assert body["results"]["aqi"]["ok"] is False


@pytest.mark.asyncio
async def test_crawl_defaults_to_all_sources(client, monkeypatch):
    async def ok(session):
        return 1

    for src in list(crawl_service.CRAWLERS):
        monkeypatch.setitem(crawl_service.CRAWLERS, src, ok)

    resp = await client.post("/api/v2/crawl", json={})
    assert resp.status_code == 200
    assert set(resp.json()["results"]) == set(crawl_service.ALL_SOURCES)
