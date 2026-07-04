import pytest
from src.models.decision import AgentDecision
from datetime import datetime, timezone


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
