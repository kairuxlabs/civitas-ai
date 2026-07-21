import pytest
from src.utils.config import settings


@pytest.mark.asyncio
async def test_system_status_reports_database_ok(client):
    response = await client.get("/api/system/status")
    assert response.status_code == 200
    data = response.json()
    assert data["database"] is True


@pytest.mark.asyncio
async def test_system_status_reports_real_gemini_model_and_temperature(client):
    from src.agents.gemini_client import GEMINI_MODEL, GEMINI_TEMPERATURE
    from src.ai.planner import PLANNER_MODELS

    response = await client.get("/api/system/status")
    data = response.json()
    assert data["gemini_model"] == GEMINI_MODEL
    assert data["gemini_temperature"] == GEMINI_TEMPERATURE
    assert data["openrouter_fallback_models"] == PLANNER_MODELS


@pytest.mark.asyncio
async def test_system_status_reflects_unconfigured_optional_services(monkeypatch, client):
    monkeypatch.setattr(settings, "neo4j_uri", "")
    monkeypatch.setattr(settings, "qdrant_url", "")
    monkeypatch.setattr(settings, "openrouter_api_key", "")

    response = await client.get("/api/system/status")
    data = response.json()
    assert data["neo4j_configured"] is False
    assert data["qdrant_configured"] is False
    assert data["openrouter_configured"] is False


@pytest.mark.asyncio
async def test_system_status_reflects_configured_optional_services(monkeypatch, client):
    monkeypatch.setattr(settings, "neo4j_uri", "bolt://localhost:7687")
    monkeypatch.setattr(settings, "qdrant_url", "http://localhost:6333")
    monkeypatch.setattr(settings, "openrouter_api_key", "sk-test")

    response = await client.get("/api/system/status")
    data = response.json()
    assert data["neo4j_configured"] is True
    assert data["qdrant_configured"] is True
    assert data["openrouter_configured"] is True
