from datetime import datetime, timedelta, timezone

from src.models.aqi import AQI
from src.models.city_score import CityScore
from src.models.district import District
from src.models.weather import Weather


async def test_get_all_scores_returns_latest_per_district(client, db_session):
    d1 = District(city_id="hanoi", name="Hoàn Kiếm")
    d2 = District(city_id="hanoi", name="Ba Đình")
    db_session.add_all([d1, d2])
    await db_session.flush()

    base = datetime.now(timezone.utc)
    # Older scores for both districts, plus a newer one each — the route
    # must return only the latest per district via the single-query path
    # (CityScoreRepo.get_city_overview), not the newest-looking-but-wrong row.
    db_session.add_all([
        CityScore(
            city_id="hanoi", district_id=d1.id, timestamp=base - timedelta(minutes=30),
            traffic_score=10, environment_score=10, citizen_score=10, risk_score=10, overall_score=10,
        ),
        CityScore(
            city_id="hanoi", district_id=d1.id, timestamp=base,
            traffic_score=90, environment_score=90, citizen_score=90, risk_score=10, overall_score=90,
        ),
        CityScore(
            city_id="hanoi", district_id=d2.id, timestamp=base - timedelta(minutes=15),
            traffic_score=20, environment_score=20, citizen_score=20, risk_score=20, overall_score=20,
        ),
        CityScore(
            city_id="hanoi", district_id=d2.id, timestamp=base,
            traffic_score=80, environment_score=80, citizen_score=80, risk_score=20, overall_score=80,
        ),
    ])
    await db_session.commit()

    response = await client.get("/api/scores")
    assert response.status_code == 200
    data = response.json()

    assert len(data) == 2
    by_district = {row["district_id"]: row for row in data}
    assert by_district[d1.id]["overall_score"] == 90
    assert by_district[d2.id]["overall_score"] == 80


async def test_get_all_scores_computes_missing_district_score(client, db_session):
    # One district already has a score, the other has none and must fall
    # back to CityScoreService.calculate_and_save (unchanged behavior).
    scored = District(city_id="hanoi", name="Đống Đa")
    unscored = District(city_id="hanoi", name="Tây Hồ")
    db_session.add_all([scored, unscored])
    await db_session.flush()

    now = datetime.now(timezone.utc)
    db_session.add(CityScore(
        city_id="hanoi", district_id=scored.id, timestamp=now,
        traffic_score=50, environment_score=50, citizen_score=50, risk_score=50, overall_score=50,
    ))
    db_session.add(Weather(city_id="hanoi", district_id=unscored.id, timestamp=now, rain=0.0))
    db_session.add(AQI(city_id="hanoi", district_id=unscored.id, timestamp=now, aqi_index=100, pm25=50))
    await db_session.commit()

    response = await client.get("/api/scores")
    assert response.status_code == 200
    data = response.json()

    assert len(data) == 2
    district_ids = {row["district_id"] for row in data}
    assert district_ids == {scored.id, unscored.id}


async def test_get_all_scores_empty(client):
    response = await client.get("/api/scores")
    assert response.status_code == 200
    assert response.json() == []


async def test_get_score_history_empty(client):
    response = await client.get("/api/scores/history/1")
    assert response.status_code == 200
    assert response.json() == []


async def test_get_score_history_returns_recent_rows_chronologically(client, db_session):
    district = District(city_id="hanoi", name="Test")
    db_session.add(district)
    await db_session.flush()

    base = datetime.now(timezone.utc)
    db_session.add_all([
        CityScore(
            city_id="hanoi", district_id=district.id, timestamp=base - timedelta(minutes=10),
            traffic_score=40, environment_score=50, citizen_score=60, risk_score=20, overall_score=55,
        ),
        CityScore(
            city_id="hanoi", district_id=district.id, timestamp=base,
            traffic_score=45, environment_score=55, citizen_score=65, risk_score=25, overall_score=60,
        ),
    ])
    await db_session.commit()

    response = await client.get(f"/api/scores/history/{district.id}")
    assert response.status_code == 200
    data = response.json()

    assert len(data) == 2
    assert data[0]["traffic_score"] == 40
    assert data[1]["traffic_score"] == 45


async def test_get_score_history_limit_over_cap_rejected(client):
    response = await client.get("/api/scores/history/1?limit=99999")
    assert response.status_code == 422
