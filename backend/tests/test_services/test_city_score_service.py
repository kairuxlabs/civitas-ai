from datetime import datetime, timezone
from src.models.district import District
from src.models.aqi import AQI
from src.models.weather import Weather
from src.services.city_score_service import CityScoreService


async def test_calculate_city_score(db_session):
    district = District(city_id="hanoi", name="Test")
    db_session.add(district)
    await db_session.flush()

    now = datetime.now(timezone.utc)
    db_session.add(AQI(
        city_id="hanoi", district_id=district.id, timestamp=now,
        pm25=50.0, pm10=80.0, co=1.0, no2=40.0, aqi_index=100
    ))
    db_session.add(Weather(
        city_id="hanoi", district_id=district.id, timestamp=now,
        temperature=30.0, humidity=70.0, rain=0.0, wind_speed=10.0
    ))
    await db_session.flush()

    score = await CityScoreService.calculate_and_save(db_session, district.id)

    assert score is not None
    assert 0 <= score.traffic_score <= 100
    assert 0 <= score.environment_score <= 100
    assert 0 <= score.overall_score <= 100
