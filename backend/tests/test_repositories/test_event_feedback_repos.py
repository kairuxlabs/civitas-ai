import pytest
from datetime import datetime, timezone, timedelta
from src.models.district import District
from src.models.event import Event
from src.models.feedback import CitizenFeedback
from src.repositories.event_repo import EventRepo
from src.repositories.feedback_repo import FeedbackRepo


@pytest.mark.asyncio
async def test_event_repo_returns_recent_events(db_session):
    district = District(city_id="hanoi", name="Test District")
    db_session.add(district)
    await db_session.flush()

    now = datetime.now(timezone.utc)
    # Add an event 12h ago (should be returned)
    recent = Event(
        city_id="hanoi",
        district_id=district.id,
        title="Recent Event",
        impact_level="high",
        start_time=now - timedelta(hours=12),
    )
    # Add an event 25h ago (outside 24h window, should NOT be returned)
    old = Event(
        city_id="hanoi",
        district_id=district.id,
        title="Old Event",
        impact_level="low",
        start_time=now - timedelta(hours=25),
    )
    db_session.add_all([recent, old])
    await db_session.commit()

    events = await EventRepo.get_current(db_session, district.id)
    titles = [e.title for e in events]
    assert "Recent Event" in titles
    assert "Old Event" not in titles


@pytest.mark.asyncio
async def test_event_repo_empty_when_no_events(db_session):
    district = District(city_id="hanoi", name="Empty District")
    db_session.add(district)
    await db_session.flush()
    await db_session.commit()

    events = await EventRepo.get_current(db_session, district.id)
    assert events == []


@pytest.mark.asyncio
async def test_feedback_repo_returns_recent_feedback(db_session):
    district = District(city_id="hanoi", name="FB District")
    db_session.add(district)
    await db_session.flush()

    fb = CitizenFeedback(
        city_id="hanoi",
        district_id=district.id,
        category="traffic",
        sentiment="negative",
        content="Kẹt xe kinh khủng",
    )
    db_session.add(fb)
    await db_session.commit()

    results = await FeedbackRepo.get_recent(db_session, district.id)
    assert len(results) >= 1
    assert results[0].category == "traffic"


@pytest.mark.asyncio
async def test_feedback_repo_respects_limit(db_session):
    district = District(city_id="hanoi", name="Limit District")
    db_session.add(district)
    await db_session.flush()

    for i in range(15):
        db_session.add(CitizenFeedback(
            city_id="hanoi",
            district_id=district.id,
            category="traffic",
            sentiment="negative",
            content=f"Feedback {i}",
        ))
    await db_session.commit()

    results = await FeedbackRepo.get_recent(db_session, district.id, limit=5)
    assert len(results) == 5
