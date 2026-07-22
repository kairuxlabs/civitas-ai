import asyncio

import pytest

from src.runtime.engine import engine
from src.utils.config import settings


@pytest.fixture(autouse=True)
def offline(monkeypatch):
    monkeypatch.setattr(settings, "gemini_api_key", "")
    monkeypatch.setattr(settings, "qdrant_url", "")
    monkeypatch.setattr(settings, "neo4j_uri", "")


@pytest.mark.asyncio
async def test_goal_lifecycle(client):
    resp = await client.post("/api/v2/goal", json={"goal": "Prepare the city for tonight's heavy rain"})
    assert resp.status_code == 202
    run_id = resp.json()["run_id"]

    await engine.wait_for(run_id)

    detail = (await client.get(f"/api/v2/runs/{run_id}")).json()
    assert detail["status"] == "awaiting_approval"
    assert detail["decision"] is not None
    assert detail["tasks"], "expected planned tasks"
    assert detail["timeline"], "expected timeline entries"

    resolved = await client.post(f"/api/v2/runs/{run_id}/approval", json={"approved": True})
    assert resolved.status_code == 200
    body = resolved.json()
    assert body["status"] == "done"
    assert [s["step"] for s in body["workflow_steps"]] == ["notify", "create_incident", "store_memory", "done"]

    runs = (await client.get("/api/v2/runs")).json()["runs"]
    assert any(r["run_id"] == run_id for r in runs)


@pytest.mark.asyncio
async def test_unknown_run_returns_404(client):
    assert (await client.get("/api/v2/runs/deadbeef")).status_code == 404
    resp = await client.post("/api/v2/runs/deadbeef/approval", json={"approved": True})
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_monitor_shape(client):
    resp = await client.get("/api/v2/monitor")
    assert resp.status_code == 200
    body = resp.json()
    assert {"agents", "active_runs", "total_runs"} <= set(body)


@pytest.mark.asyncio
async def test_goal_validation(client):
    resp = await client.post("/api/v2/goal", json={"goal": "ab"})
    assert resp.status_code == 422


@pytest.mark.asyncio
async def test_goal_and_approval_require_api_key_when_configured(monkeypatch, client):
    monkeypatch.setattr(settings, "api_key", "secret123")

    no_header = await client.post(
        "/api/v2/goal", json={"goal": "Prepare the city for tonight's heavy rain"}
    )
    assert no_header.status_code == 401

    wrong_header = await client.post(
        "/api/v2/goal",
        json={"goal": "Prepare the city for tonight's heavy rain"},
        headers={"X-API-Key": "wrong"},
    )
    assert wrong_header.status_code == 401

    ok = await client.post(
        "/api/v2/goal",
        json={"goal": "Prepare the city for tonight's heavy rain"},
        headers={"X-API-Key": "secret123"},
    )
    assert ok.status_code == 202
    run_id = ok.json()["run_id"]

    await engine.wait_for(run_id)

    approval_no_header = await client.post(
        f"/api/v2/runs/{run_id}/approval", json={"approved": True}
    )
    assert approval_no_header.status_code == 401

    approval_ok = await client.post(
        f"/api/v2/runs/{run_id}/approval",
        json={"approved": True},
        headers={"X-API-Key": "secret123"},
    )
    assert approval_ok.status_code == 200
