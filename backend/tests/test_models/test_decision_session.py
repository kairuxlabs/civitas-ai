from datetime import datetime, timezone
from src.models.decision_session import DecisionSession


async def test_create_and_to_dict(db_session):
    record = DecisionSession(
        run_id="abc123", goal="Reduce congestion", district_id=1,
        status="collecting", created_at=datetime.now(timezone.utc),
    )
    db_session.add(record)
    await db_session.commit()
    await db_session.refresh(record)

    d = record.to_dict()
    assert d["run_id"] == "abc123"
    assert d["status"] == "collecting"
    assert d["baseline_scores"] is None
    assert d["created_at"] is not None
