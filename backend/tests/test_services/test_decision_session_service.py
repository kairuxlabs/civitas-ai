from datetime import datetime, timezone
from src.models.decision_session import DecisionSession
from src.services.decision_session_service import DecisionSessionService, evaluate_outcome


def test_evaluate_outcome_improved_with_expected():
    baseline = {"overall_score": 50.0}
    expected = {"overall_score": 65.0}
    observed = {"overall_score": 63.0}
    delta, success_rate, status = evaluate_outcome(baseline, observed, expected)
    assert delta == {"overall_score": 13.0}
    assert success_rate == round(13 / 15 * 100, 1)
    assert status == "improved"


def test_evaluate_outcome_worse_when_opposite_sign():
    baseline = {"overall_score": 50.0}
    expected = {"overall_score": 65.0}
    observed = {"overall_score": 45.0}
    delta, success_rate, status = evaluate_outcome(baseline, observed, expected)
    assert success_rate == 0.0
    assert status == "worse"


def test_evaluate_outcome_no_expected_uses_fallback_thresholds():
    baseline = {"overall_score": 50.0}
    observed_improved = {"overall_score": 53.0}
    delta, success_rate, status = evaluate_outcome(baseline, observed_improved, None)
    assert success_rate is None
    assert status == "improved"

    observed_worse = {"overall_score": 47.0}
    _, _, status_worse = evaluate_outcome(baseline, observed_worse, None)
    assert status_worse == "worse"

    observed_flat = {"overall_score": 50.5}
    _, _, status_flat = evaluate_outcome(baseline, observed_flat, None)
    assert status_flat == "no_change"


def test_evaluate_outcome_no_expected_boundary_worse():
    """Regression: raw delta -2.04 rounds to -2.0; must use raw value for threshold comparison."""
    baseline = {"overall_score": 50.0}
    observed = {"overall_score": 47.96}
    _, _, status = evaluate_outcome(baseline, observed, None)
    assert status == "worse"


def test_evaluate_outcome_no_expected_boundary_improved():
    """Regression: raw delta 2.04 rounds to 2.0; must use raw value for threshold comparison."""
    baseline = {"overall_score": 50.0}
    observed = {"overall_score": 52.04}
    _, _, status = evaluate_outcome(baseline, observed, None)
    assert status == "improved"


async def test_create_sets_collecting_status(db_session):
    record = await DecisionSessionService.create(db_session, "run-1", "Reduce congestion", 1)
    assert record.status == "collecting"
    assert record.run_id == "run-1"


async def test_mark_analyzing_updates_existing_session(db_session):
    await DecisionSessionService.create(db_session, "run-2", "goal", 1)
    await DecisionSessionService.mark_analyzing(db_session, "run-2")

    from sqlalchemy import select
    result = await db_session.execute(select(DecisionSession).where(DecisionSession.run_id == "run-2"))
    assert result.scalar_one().status == "analyzing"


async def test_mark_analyzing_unknown_run_id_is_a_noop(db_session):
    await DecisionSessionService.mark_analyzing(db_session, "does-not-exist")  # must not raise

    from sqlalchemy import select
    result = await db_session.execute(select(DecisionSession))
    assert result.scalars().all() == []  # confirms no row was created or touched


async def test_mark_recommend_updates_existing_session(db_session):
    await DecisionSessionService.create(db_session, "run-rec", "goal", 1)
    await DecisionSessionService.mark_recommend(db_session, "run-rec")

    from sqlalchemy import select
    result = await db_session.execute(select(DecisionSession).where(DecisionSession.run_id == "run-rec"))
    assert result.scalar_one().status == "recommend"


async def test_mark_awaiting_approval_sets_decision_id(db_session):
    await DecisionSessionService.create(db_session, "run-3", "goal", 1)
    await DecisionSessionService.mark_awaiting_approval(db_session, "run-3", decision_id=42)

    from sqlalchemy import select
    result = await db_session.execute(select(DecisionSession).where(DecisionSession.run_id == "run-3"))
    record = result.scalar_one()
    assert record.status == "awaiting_approval"
    assert record.decision_id == 42


async def test_mark_rejected(db_session):
    await DecisionSessionService.create(db_session, "run-4", "goal", 1)
    await DecisionSessionService.mark_rejected(db_session, "run-4")

    from sqlalchemy import select
    result = await db_session.execute(select(DecisionSession).where(DecisionSession.run_id == "run-4"))
    assert result.scalar_one().status == "rejected"
