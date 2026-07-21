"""Decision Session lifecycle. Every method takes an AsyncSession as its
first argument (matches CityScoreService.calculate_and_save's convention)
so the service is directly testable against the `db_session` fixture —
callers in the v2 runtime (engine.py, workflow.py) open their own
best-effort AsyncSessionLocal() around these calls, matching
src/runtime/workflow.py's existing _persist_decision convention.
"""
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.models.decision_session import DecisionSession
from src.services.city_score_service import CityScoreService

DECISION_OBSERVE_DELAY_MIN = 30
SUCCESS_RATE_IMPROVED = 50
SUCCESS_RATE_WORSE = 20
NO_EXPECTED_IMPROVED_DELTA = 2.0
NO_EXPECTED_WORSE_DELTA = -2.0


def _score_dict(score) -> dict:
    return {
        "traffic_score": score.traffic_score,
        "environment_score": score.environment_score,
        "citizen_score": score.citizen_score,
        "risk_score": score.risk_score,
        "overall_score": score.overall_score,
    }


def evaluate_outcome(
    baseline: dict, observed: dict, expected: dict | None,
) -> tuple[dict, float | None, str]:
    """Decision Session spec §7. Only overall_score drives success_rate/status;
    other fields are carried in `delta` for display only."""
    delta = {k: round(observed[k] - baseline[k], 1) for k in observed if k in baseline}
    observed_delta = delta.get("overall_score", 0.0)

    if expected and "overall_score" in expected:
        expected_delta = expected["overall_score"] - baseline.get("overall_score", 0.0)
        if expected_delta == 0:
            success_rate = 100.0 if observed_delta >= 0 else 0.0
        elif (observed_delta >= 0) != (expected_delta >= 0):
            success_rate = 0.0
        else:
            success_rate = max(0.0, min(1.0, observed_delta / expected_delta)) * 100
        status = (
            "improved" if success_rate >= SUCCESS_RATE_IMPROVED
            else "worse" if success_rate < SUCCESS_RATE_WORSE
            else "no_change"
        )
        return delta, round(success_rate, 1), status

    status = (
        "improved" if observed_delta > NO_EXPECTED_IMPROVED_DELTA
        else "worse" if observed_delta < NO_EXPECTED_WORSE_DELTA
        else "no_change"
    )
    return delta, None, status


class DecisionSessionService:
    @staticmethod
    async def create(session: AsyncSession, run_id: str, goal: str, district_id: int) -> DecisionSession:
        record = DecisionSession(
            run_id=run_id, goal=goal, district_id=district_id,
            status="collecting", created_at=datetime.now(timezone.utc),
        )
        session.add(record)
        await session.commit()
        await session.refresh(record)
        return record

    @staticmethod
    async def _get_by_run_id(session: AsyncSession, run_id: str) -> DecisionSession | None:
        result = await session.execute(select(DecisionSession).where(DecisionSession.run_id == run_id))
        return result.scalar_one_or_none()

    @staticmethod
    async def mark_analyzing(session: AsyncSession, run_id: str) -> None:
        record = await DecisionSessionService._get_by_run_id(session, run_id)
        if record is not None:
            record.status = "analyzing"
            await session.commit()

    @staticmethod
    async def mark_recommend(session: AsyncSession, run_id: str) -> None:
        record = await DecisionSessionService._get_by_run_id(session, run_id)
        if record is not None:
            record.status = "recommend"
            await session.commit()

    @staticmethod
    async def mark_awaiting_approval(session: AsyncSession, run_id: str, decision_id: int | None) -> None:
        record = await DecisionSessionService._get_by_run_id(session, run_id)
        if record is not None:
            record.status = "awaiting_approval"
            record.decision_id = decision_id
            await session.commit()

    @staticmethod
    async def mark_rejected(session: AsyncSession, run_id: str) -> None:
        record = await DecisionSessionService._get_by_run_id(session, run_id)
        if record is not None:
            record.status = "rejected"
            await session.commit()
