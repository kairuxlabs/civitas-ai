import pytest
from datetime import datetime, timezone

from src.models.decision import AgentDecision


@pytest.mark.asyncio
async def test_get_timeline_empty(client):
    response = await client.get("/api/timeline")
    assert response.status_code == 200
    assert response.json() == []


@pytest.mark.asyncio
async def test_get_timeline_returns_recent_decisions(db_session, client):
    decision = AgentDecision(
        city_id="hanoi",
        district_id=None,
        query="test query",
        prediction={},
        impact={},
        recommendations=[],
        confidence=80.0,
        explanation=["item1"],
        requires_approval=False,
        approved=None,
        created_at=datetime.now(timezone.utc),
    )
    db_session.add(decision)
    await db_session.commit()

    response = await client.get("/api/timeline")
    assert response.status_code == 200
    assert len(response.json()) == 1


@pytest.mark.asyncio
async def test_get_timeline_limit_over_cap_rejected(client):
    response = await client.get("/api/timeline?limit=99999")
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_get_timeline_limit_within_cap_ok(client):
    response = await client.get("/api/timeline?limit=100")
    assert response.status_code == 200
