from datetime import datetime, timezone
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
