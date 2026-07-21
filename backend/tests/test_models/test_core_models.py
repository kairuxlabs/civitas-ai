# backend/tests/test_models.py
from src.models import District, Weather, AQI, CityScore


async def test_district_model(db_session):
    district = District(city_id="hanoi", name="Test District")
    db_session.add(district)
    await db_session.commit()
    await db_session.refresh(district)
    assert district.id is not None
    assert district.name == "Test District"
    assert district.city_id == "hanoi"


async def test_city_score_model(db_session):
    from datetime import datetime, timezone
    district = District(city_id="hanoi", name="D1")
    db_session.add(district)
    await db_session.flush()
    score = CityScore(
        city_id="hanoi",
        district_id=district.id,
        timestamp=datetime.now(timezone.utc),
        traffic_score=75.0,
        environment_score=60.0,
        citizen_score=80.0,
        risk_score=40.0,
        overall_score=72.0,
    )
    db_session.add(score)
    await db_session.commit()
    assert score.id is not None
    assert score.overall_score == 72.0
