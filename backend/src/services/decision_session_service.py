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
    # Compute raw deltas (unrounded) for threshold comparisons.
    observed_raw_delta = observed.get("overall_score", 0.0) - baseline.get("overall_score", 0.0)

    # Build rounded delta dict for display.
    delta = {k: round(observed[k] - baseline[k], 1) for k in observed if k in baseline}

    if expected and "overall_score" in expected:
        expected_raw_delta = expected["overall_score"] - baseline.get("overall_score", 0.0)
        if expected_raw_delta == 0:
            success_rate = 100.0 if observed_raw_delta >= 0 else 0.0
        elif (observed_raw_delta >= 0) != (expected_raw_delta >= 0):
            success_rate = 0.0
        else:
            success_rate = max(0.0, min(1.0, observed_raw_delta / expected_raw_delta)) * 100
        status = (
            "improved" if success_rate >= SUCCESS_RATE_IMPROVED
            else "worse" if success_rate < SUCCESS_RATE_WORSE
            else "no_change"
        )
        return delta, round(success_rate, 1), status

    status = (
        "improved" if observed_raw_delta > NO_EXPECTED_IMPROVED_DELTA
        else "worse" if observed_raw_delta < NO_EXPECTED_WORSE_DELTA
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

    @staticmethod
    async def mark_approved(session: AsyncSession, run_id: str) -> DecisionSession | None:
        """Captures the baseline CityScore + weather/AQI context, and moves
        straight to "observing". Does NOT schedule the follow-up job — the
        caller owns the scheduler (see src/runtime/workflow.py's integration
        in Task 5)."""
        record = await DecisionSessionService._get_by_run_id(session, run_id)
        if record is None or record.district_id is None:
            return None
        score = await CityScoreService.calculate_and_save(session, record.district_id)
        record.status = "observing"
        record.baseline_scores = _score_dict(score)
        record.context_snapshot = await DecisionSessionService._context_snapshot(session, record.district_id)
        record.approved_at = datetime.now(timezone.utc)
        await session.commit()
        await session.refresh(record)
        return record

    @staticmethod
    async def _context_snapshot(session: AsyncSession, district_id: int) -> dict:
        from src.repositories.aqi_repo import AQIRepo
        from src.repositories.weather_repo import WeatherRepo
        weather = await WeatherRepo.get_latest(session, district_id)
        aqi = await AQIRepo.get_latest(session, district_id)
        return {
            "rain": weather.rain if weather else None,
            "aqi_index": aqi.aqi_index if aqi else None,
            "pm25": aqi.pm25 if aqi else None,
        }

    @staticmethod
    async def _outcome_confidence(session: AsyncSession, district_id: int) -> int:
        """90 if the AQI reading behind the outcome score is < 20 min old,
        else 60 — Decision Session spec §5.2's freshness heuristic."""
        from src.repositories.aqi_repo import AQIRepo
        aqi = await AQIRepo.get_latest(session, district_id)
        if aqi is None:
            return 60
        # SQLite round-trips DateTime(timezone=True) as naive under aiosqlite —
        # values are always written via datetime.now(timezone.utc), so a naive
        # read-back is safely assumed to already be UTC.
        aqi_ts = aqi.timestamp if aqi.timestamp.tzinfo else aqi.timestamp.replace(tzinfo=timezone.utc)
        age_minutes = (datetime.now(timezone.utc) - aqi_ts).total_seconds() / 60
        return 90 if age_minutes < 20 else 60

    @staticmethod
    async def observe(session: AsyncSession, session_id: int) -> DecisionSession | None:
        result = await session.execute(select(DecisionSession).where(DecisionSession.id == session_id))
        record = result.scalar_one_or_none()
        if record is None or record.status != "observing" or record.district_id is None:
            return None

        score = await CityScoreService.calculate_and_save(session, record.district_id)
        observed = _score_dict(score)
        delta, success_rate, status = evaluate_outcome(
            record.baseline_scores or {}, observed, record.expected_outcome,
        )
        confidence = await DecisionSessionService._outcome_confidence(session, record.district_id)

        now = datetime.now(timezone.utc)
        record.observed_scores = observed
        record.outcome_delta = delta
        record.success_rate = success_rate
        record.outcome_status = status
        record.outcome_evidence = [
            {"source": "CityScoreService", "type": "sensor_derived", "metric": key,
             "value": value, "confidence": confidence, "timestamp": now.isoformat()}
            for key, value in observed.items()
        ]
        record.observed_at = now
        record.evaluated_at = now
        record.status = "evaluated"
        await session.commit()
        await session.refresh(record)
        return record

    @staticmethod
    async def get(session: AsyncSession, session_id: int) -> DecisionSession | None:
        result = await session.execute(select(DecisionSession).where(DecisionSession.id == session_id))
        return result.scalar_one_or_none()

    @staticmethod
    async def list_sessions(session: AsyncSession, status: str | None = None) -> list[DecisionSession]:
        query = select(DecisionSession).order_by(DecisionSession.created_at.desc())
        if status:
            query = query.where(DecisionSession.status == status)
        result = await session.execute(query)
        return list(result.scalars().all())

    @staticmethod
    async def analytics(session: AsyncSession) -> dict:
        result = await session.execute(select(DecisionSession))
        sessions = list(result.scalars().all())

        decided = [s for s in sessions if s.status != "collecting" and s.status != "analyzing"
                   and s.status != "recommend" and s.status != "awaiting_approval"]
        approved = [s for s in decided if s.status != "rejected"]
        evaluated = [s for s in sessions if s.status == "evaluated"]
        improved = [s for s in evaluated if s.outcome_status == "improved"]
        latencies = [
            (s.approved_at - s.created_at).total_seconds() / 60
            for s in sessions if s.approved_at is not None
        ]
        improvements = [
            s.outcome_delta["overall_score"] for s in evaluated
            if s.outcome_delta and "overall_score" in s.outcome_delta
        ]

        return {
            "total_sessions": len(sessions),
            "approval_rate": round(len(approved) / len(decided) * 100, 1) if decided else None,
            "evaluated_count": len(evaluated),
            "improved_rate": round(len(improved) / len(evaluated) * 100, 1) if evaluated else None,
            "avg_improvement": round(sum(improvements) / len(improvements), 1) if improvements else None,
            "avg_decision_latency_minutes": round(sum(latencies) / len(latencies), 1) if latencies else None,
        }


async def observe_session_job(session_id: int) -> None:
    """APScheduler entry point — best-effort, matches workflow.py's
    persistence philosophy. Never raises (a failed scheduled job must not
    crash the scheduler thread)."""
    from src.database.connection import AsyncSessionLocal
    from src.utils.logger import get_logger
    logger = get_logger(__name__)
    try:
        async with AsyncSessionLocal() as session:
            await DecisionSessionService.observe(session, session_id)
    except Exception as e:
        logger.warning(f"DecisionSession observe job skipped for session {session_id}: {e}")
