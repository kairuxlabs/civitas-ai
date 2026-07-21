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


from src.models.district import District
from src.models.aqi import AQI
from src.models.weather import Weather


async def _seed_district_with_readings(db_session, aqi_index=100, pm25=50.0, rain=0.0):
    district = District(city_id="hanoi", name="Test District")
    db_session.add(district)
    await db_session.flush()
    now = datetime.now(timezone.utc)
    db_session.add(AQI(city_id="hanoi", district_id=district.id, timestamp=now,
                        pm25=pm25, pm10=80.0, co=1.0, no2=40.0, aqi_index=aqi_index))
    db_session.add(Weather(city_id="hanoi", district_id=district.id, timestamp=now,
                            temperature=30.0, humidity=70.0, rain=rain, wind_speed=10.0))
    await db_session.flush()
    return district


async def test_mark_approved_captures_baseline_and_moves_to_observing(db_session):
    district = await _seed_district_with_readings(db_session, aqi_index=120, pm25=55.0, rain=3.0)
    await DecisionSessionService.create(db_session, "run-5", "goal", district.id)

    record = await DecisionSessionService.mark_approved(db_session, "run-5")

    assert record.status == "observing"
    assert record.baseline_scores is not None
    assert "overall_score" in record.baseline_scores
    assert record.approved_at is not None
    assert record.context_snapshot == {"rain": 3.0, "aqi_index": 120, "pm25": 55.0}


async def test_mark_approved_unknown_run_id_returns_none(db_session):
    assert await DecisionSessionService.mark_approved(db_session, "nope") is None


async def test_observe_computes_outcome_and_finalizes(db_session):
    district = await _seed_district_with_readings(db_session, aqi_index=200)  # bad baseline
    await DecisionSessionService.create(db_session, "run-6", "goal", district.id)
    approved = await DecisionSessionService.mark_approved(db_session, "run-6")

    # Improve conditions before observing, simulating a real pipeline tick
    db_session.add(AQI(city_id="hanoi", district_id=district.id, timestamp=datetime.now(timezone.utc),
                        pm25=10.0, pm10=20.0, co=0.5, no2=10.0, aqi_index=40))
    db_session.add(Weather(city_id="hanoi", district_id=district.id, timestamp=datetime.now(timezone.utc),
                            temperature=28.0, humidity=60.0, rain=0.0, wind_speed=5.0))
    await db_session.flush()

    result = await DecisionSessionService.observe(db_session, approved.id)

    assert result.status == "evaluated"
    assert result.observed_scores is not None
    assert result.outcome_delta is not None
    assert result.outcome_status in ("improved", "worse", "no_change")
    assert result.outcome_status == "improved"  # AQI 200 -> 40 must read as improved
    assert len(result.outcome_evidence) == 5  # one per score field
    assert all(e["source"] == "CityScoreService" for e in result.outcome_evidence)
    # the AQI row just inserted is fresh (< 20 min old) -> confidence 90
    assert all(e["confidence"] == 90 for e in result.outcome_evidence)
    assert result.evaluated_at is not None


async def test_observe_uses_lower_confidence_for_stale_reading(db_session):
    from datetime import timedelta
    district = await _seed_district_with_readings(db_session, aqi_index=100)
    await DecisionSessionService.create(db_session, "run-6b", "goal", district.id)
    approved = await DecisionSessionService.mark_approved(db_session, "run-6b")

    # Replace the fixture's fresh reading with an older one (25 min ago) so
    # it's still the latest row by timestamp, but stale by the confidence check
    from sqlalchemy import delete
    await db_session.execute(delete(AQI).where(AQI.district_id == district.id))
    await db_session.execute(delete(Weather).where(Weather.district_id == district.id))
    stale_ts = datetime.now(timezone.utc) - timedelta(minutes=25)
    db_session.add(AQI(city_id="hanoi", district_id=district.id, timestamp=stale_ts,
                        pm25=45.0, pm10=70.0, co=0.8, no2=30.0, aqi_index=90))
    db_session.add(Weather(city_id="hanoi", district_id=district.id, timestamp=stale_ts,
                            temperature=29.0, humidity=65.0, rain=0.0, wind_speed=8.0))
    await db_session.flush()

    result = await DecisionSessionService.observe(db_session, approved.id)
    assert all(e["confidence"] == 60 for e in result.outcome_evidence)


async def test_observe_returns_none_when_not_observing(db_session):
    district = await _seed_district_with_readings(db_session)
    record = await DecisionSessionService.create(db_session, "run-7", "goal", district.id)
    # still "collecting" — never approved
    assert await DecisionSessionService.observe(db_session, record.id) is None


async def test_observe_unknown_session_id_returns_none(db_session):
    assert await DecisionSessionService.observe(db_session, 999999) is None


async def test_get_returns_none_for_unknown_id(db_session):
    assert await DecisionSessionService.get(db_session, 999999) is None


async def test_list_sessions_orders_newest_first(db_session):
    await DecisionSessionService.create(db_session, "run-a", "goal a", 1)
    await DecisionSessionService.create(db_session, "run-b", "goal b", 1)

    sessions = await DecisionSessionService.list_sessions(db_session)
    run_ids = [s.run_id for s in sessions]
    assert run_ids.index("run-b") < run_ids.index("run-a")


async def test_list_sessions_filters_by_status(db_session):
    await DecisionSessionService.create(db_session, "run-c", "goal", 1)
    d = await DecisionSessionService.create(db_session, "run-d", "goal", 1)
    await DecisionSessionService.mark_rejected(db_session, d.run_id)

    rejected = await DecisionSessionService.list_sessions(db_session, status="rejected")
    assert [s.run_id for s in rejected] == ["run-d"]


async def test_analytics_empty_is_zero_safe(db_session):
    result = await DecisionSessionService.analytics(db_session)
    assert result == {
        "total_sessions": 0, "approval_rate": None, "evaluated_count": 0,
        "improved_rate": None, "avg_improvement": None, "avg_decision_latency_minutes": None,
    }


async def test_analytics_computes_rates(db_session):
    district = await _seed_district_with_readings(db_session, aqi_index=200)
    a = await DecisionSessionService.create(db_session, "run-e", "goal", district.id)
    await DecisionSessionService.mark_rejected(db_session, a.run_id)

    await DecisionSessionService.create(db_session, "run-f", "goal", district.id)
    approved = await DecisionSessionService.mark_approved(db_session, "run-f")
    db_session.add(AQI(city_id="hanoi", district_id=district.id, timestamp=datetime.now(timezone.utc),
                        pm25=10.0, pm10=20.0, co=0.5, no2=10.0, aqi_index=40))
    await db_session.flush()
    await DecisionSessionService.observe(db_session, approved.id)

    result = await DecisionSessionService.analytics(db_session)
    assert result["total_sessions"] == 2
    assert result["approval_rate"] == 50.0  # 1 approved out of 2 decided
    assert result["evaluated_count"] == 1
    assert result["improved_rate"] == 100.0
    assert result["avg_improvement"] is not None
    assert result["avg_decision_latency_minutes"] is not None
