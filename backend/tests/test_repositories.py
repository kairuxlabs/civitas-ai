from datetime import datetime, timezone

from src.models.district import District
from src.models.city_score import CityScore
from src.repositories.district_repo import DistrictRepo
from src.repositories.city_score_repo import CityScoreRepo


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
