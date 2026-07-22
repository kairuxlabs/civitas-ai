import pytest
from src.models.decision import AgentDecision
from src.utils.config import settings
from datetime import datetime, timezone


async def _seed_decision(db_session, query="test query"):
    decision = AgentDecision(
        city_id="hanoi",
        district_id=None,
        query=query,
        prediction={},
        impact={},
        recommendations=[],
        confidence=70.0,
        explanation=["item1"],
        requires_approval=True,
        approved=None,
        created_at=datetime.now(timezone.utc),
    )
    db_session.add(decision)
    await db_session.commit()
    await db_session.refresh(decision)
    return decision


@pytest.mark.asyncio
async def test_approve_decision(db_session, client):
    decision = AgentDecision(
        city_id="hanoi",
        district_id=None,
        query="test query",
        prediction={"flood_risk": "high"},
        impact={},
        recommendations=["Action 1"],
        confidence=60.0,
        explanation=["item1"],
        requires_approval=True,
        approved=None,
        created_at=datetime.now(timezone.utc),
    )
    db_session.add(decision)
    await db_session.commit()
    await db_session.refresh(decision)

    response = await client.post(f"/api/decisions/{decision.id}/approve")
    assert response.status_code == 200
    data = response.json()
    assert data["approved"] is True
    assert data["id"] == decision.id


@pytest.mark.asyncio
async def test_reject_decision(db_session, client):
    decision = AgentDecision(
        city_id="hanoi",
        district_id=None,
        query="test query 2",
        prediction={},
        impact={},
        recommendations=[],
        confidence=70.0,
        explanation=["item1"],
        requires_approval=True,
        approved=None,
        created_at=datetime.now(timezone.utc),
    )
    db_session.add(decision)
    await db_session.commit()
    await db_session.refresh(decision)

    response = await client.post(f"/api/decisions/{decision.id}/reject")
    assert response.status_code == 200
    data = response.json()
    assert data["approved"] is False


@pytest.mark.asyncio
async def test_approve_nonexistent_decision(client):
    response = await client.post("/api/decisions/99999/approve")
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_reject_nonexistent_decision(client):
    response = await client.post("/api/decisions/99999/reject")
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_approve_decision_works_without_header_when_api_key_unset(db_session, client):
    decision = await _seed_decision(db_session)
    response = await client.post(f"/api/decisions/{decision.id}/approve")
    assert response.status_code == 200


@pytest.mark.asyncio
async def test_approve_decision_requires_api_key_when_configured(monkeypatch, db_session, client):
    monkeypatch.setattr(settings, "api_key", "secret123")
    decision = await _seed_decision(db_session)

    no_header = await client.post(f"/api/decisions/{decision.id}/approve")
    assert no_header.status_code == 401

    wrong_header = await client.post(
        f"/api/decisions/{decision.id}/approve", headers={"X-API-Key": "wrong"}
    )
    assert wrong_header.status_code == 401

    ok = await client.post(
        f"/api/decisions/{decision.id}/approve", headers={"X-API-Key": "secret123"}
    )
    assert ok.status_code == 200
    assert ok.json()["approved"] is True


@pytest.mark.asyncio
async def test_reject_decision_requires_api_key_when_configured(monkeypatch, db_session, client):
    monkeypatch.setattr(settings, "api_key", "secret123")
    decision = await _seed_decision(db_session)

    no_header = await client.post(f"/api/decisions/{decision.id}/reject")
    assert no_header.status_code == 401

    ok = await client.post(
        f"/api/decisions/{decision.id}/reject", headers={"X-API-Key": "secret123"}
    )
    assert ok.status_code == 200
    assert ok.json()["approved"] is False
