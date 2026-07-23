import pytest

from src.crawlers import crawl_service
from src.simulation.engine import simulation
from src.utils.config import settings


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
async def test_simulation_start_passes_district_id_through(client, monkeypatch):
    monkeypatch.setattr(simulation, "_persist_enabled", False)

    resp = await client.post(
        "/api/v2/simulation/start",
        json={"scenario": "heavy_rain", "interval_s": 60, "district_id": 5},
    )
    assert resp.status_code == 200
    assert resp.json()["district_id"] == 5

    status = (await client.get("/api/v2/simulation/status")).json()
    assert status["district_id"] == 5


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
async def test_crawl_reports_zero_count_when_aqi_key_unconfigured(client, monkeypatch):
    """End-to-end: without OPENAQ_API_KEY, AQIPipeline must not fabricate
    data, and the crawl endpoint must surface that honestly as count 0
    rather than a bare 'ok' the frontend would render as a fake success."""
    monkeypatch.setattr(settings, "openaq_api_key", "")

    resp = await client.post("/api/v2/crawl", json={"sources": ["aqi"]})
    assert resp.status_code == 200
    assert resp.json()["results"]["aqi"] == {"ok": True, "count": 0}


@pytest.mark.asyncio
async def test_crawl_defaults_to_all_sources(client, monkeypatch):
    async def ok(session):
        return 1

    for src in list(crawl_service.CRAWLERS):
        monkeypatch.setitem(crawl_service.CRAWLERS, src, ok)

    resp = await client.post("/api/v2/crawl", json={})
    assert resp.status_code == 200
    assert set(resp.json()["results"]) == set(crawl_service.ALL_SOURCES)


@pytest.mark.asyncio
async def test_simulation_start_stop_and_crawl_require_api_key_when_configured(monkeypatch, client):
    monkeypatch.setattr(settings, "api_key", "secret123")
    monkeypatch.setattr(simulation, "_persist_enabled", False)

    start_no_header = await client.post(
        "/api/v2/simulation/start", json={"scenario": "heavy_rain", "interval_s": 60}
    )
    assert start_no_header.status_code == 401

    start_wrong_header = await client.post(
        "/api/v2/simulation/start",
        json={"scenario": "heavy_rain", "interval_s": 60},
        headers={"X-API-Key": "wrong"},
    )
    assert start_wrong_header.status_code == 401

    start_ok = await client.post(
        "/api/v2/simulation/start",
        json={"scenario": "heavy_rain", "interval_s": 60},
        headers={"X-API-Key": "secret123"},
    )
    assert start_ok.status_code == 200

    stop_no_header = await client.post("/api/v2/simulation/stop")
    assert stop_no_header.status_code == 401

    stop_ok = await client.post(
        "/api/v2/simulation/stop", headers={"X-API-Key": "secret123"}
    )
    assert stop_ok.status_code == 200

    crawl_no_header = await client.post("/api/v2/crawl", json={})
    assert crawl_no_header.status_code == 401

    async def ok(session):
        return 1

    for src in list(crawl_service.CRAWLERS):
        monkeypatch.setitem(crawl_service.CRAWLERS, src, ok)

    crawl_ok = await client.post(
        "/api/v2/crawl", json={}, headers={"X-API-Key": "secret123"}
    )
    assert crawl_ok.status_code == 200
