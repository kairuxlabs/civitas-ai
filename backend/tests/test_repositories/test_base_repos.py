from datetime import datetime, timedelta, timezone
from unittest.mock import AsyncMock

from src.models.district import District
from src.models.city_score import CityScore
from src.models.weather import Weather
from src.models.aqi import AQI
from src.repositories.district_repo import DistrictRepo
from src.repositories.city_score_repo import CityScoreRepo
from src.repositories.weather_repo import WeatherRepo
from src.repositories.aqi_repo import AQIRepo


async def test_district_repo_get_all(db_session):
    db_session.add(District(city_id="hanoi", name="Hoàn Kiếm"))
    db_session.add(District(city_id="hanoi", name="Ba Đình"))
    await db_session.commit()
    districts = await DistrictRepo.get_all(db_session)
    assert len(districts) == 2


async def test_city_score_repo_latest(db_session):
    d = District(city_id="hanoi", name="Test")
    db_session.add(d)
    await db_session.flush()
    score = CityScore(
        city_id="hanoi",
        district_id=d.id,
        timestamp=datetime.now(timezone.utc),
        traffic_score=70.0,
        environment_score=65.0,
        citizen_score=80.0,
        risk_score=30.0,
        overall_score=73.0,
    )
    await CityScoreRepo.save(db_session, score)
    latest = await CityScoreRepo.get_latest_by_district(db_session, d.id)
    assert latest is not None
    assert latest.overall_score == 73.0


async def test_city_score_repo_get_city_overview_returns_latest_per_district(db_session):
    d1 = District(city_id="hanoi", name="D1")
    d2 = District(city_id="hanoi", name="D2")
    db_session.add_all([d1, d2])
    await db_session.flush()

    base = datetime.now(timezone.utc)
    # Each district has two rows with different timestamps; only the newest
    # per district should come back — this is the regression the swap from
    # a per-district-loop N+1 query to a single query must not break.
    db_session.add_all([
        CityScore(
            city_id="hanoi", district_id=d1.id, timestamp=base - timedelta(minutes=30),
            traffic_score=1, environment_score=1, citizen_score=1, risk_score=1, overall_score=1,
        ),
        CityScore(
            city_id="hanoi", district_id=d1.id, timestamp=base,
            traffic_score=10, environment_score=10, citizen_score=10, risk_score=10, overall_score=10,
        ),
        CityScore(
            city_id="hanoi", district_id=d2.id, timestamp=base - timedelta(minutes=15),
            traffic_score=2, environment_score=2, citizen_score=2, risk_score=2, overall_score=2,
        ),
        CityScore(
            city_id="hanoi", district_id=d2.id, timestamp=base,
            traffic_score=20, environment_score=20, citizen_score=20, risk_score=20, overall_score=20,
        ),
    ])
    await db_session.commit()

    overview = await CityScoreRepo.get_city_overview(db_session)

    assert len(overview) == 2
    by_district = {s.district_id: s for s in overview}
    assert by_district[d1.id].overall_score == 10
    assert by_district[d2.id].overall_score == 20


async def test_city_score_repo_get_city_overview_empty(db_session):
    assert await CityScoreRepo.get_city_overview(db_session) == []


async def test_weather_repo_save_all_commits_once(db_session):
    district = District(city_id="hanoi", name="Test")
    db_session.add(district)
    await db_session.flush()

    original_commit = db_session.commit
    commit_spy = AsyncMock(side_effect=original_commit)
    db_session.commit = commit_spy

    now = datetime.now(timezone.utc)
    weathers = [
        Weather(city_id="hanoi", district_id=district.id, timestamp=now, temperature=t)
        for t in (28.0, 29.0, 30.0)
    ]
    await WeatherRepo.save_all(db_session, weathers)

    assert commit_spy.await_count == 1
    from sqlalchemy import select
    result = await db_session.execute(select(Weather))
    assert len(result.scalars().all()) == 3


async def test_aqi_repo_save_all_commits_once(db_session):
    district = District(city_id="hanoi", name="Test")
    db_session.add(district)
    await db_session.flush()

    original_commit = db_session.commit
    commit_spy = AsyncMock(side_effect=original_commit)
    db_session.commit = commit_spy

    now = datetime.now(timezone.utc)
    aqis = [
        AQI(city_id="hanoi", district_id=district.id, timestamp=now, aqi_index=idx)
        for idx in (80, 90, 100)
    ]
    await AQIRepo.save_all(db_session, aqis)

    assert commit_spy.await_count == 1
    from sqlalchemy import select
    result = await db_session.execute(select(AQI))
    assert len(result.scalars().all()) == 3
