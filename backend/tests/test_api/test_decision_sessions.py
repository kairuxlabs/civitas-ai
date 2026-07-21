from datetime import datetime, timezone
from src.models.district import District
from src.models.aqi import AQI
from src.models.weather import Weather
from src.services.decision_session_service import DecisionSessionService


async def _seed_district(db_session, aqi_index=100):
    district = District(city_id="hanoi", name="Test")
    db_session.add(district)
    await db_session.flush()
    now = datetime.now(timezone.utc)
    db_session.add(AQI(city_id="hanoi", district_id=district.id, timestamp=now,
                        pm25=50.0, pm10=80.0, co=1.0, no2=40.0, aqi_index=aqi_index))
    db_session.add(Weather(city_id="hanoi", district_id=district.id, timestamp=now,
                            temperature=30.0, humidity=70.0, rain=0.0, wind_speed=10.0))
    await db_session.flush()
    return district


async def test_list_empty(client):
    resp = await client.get("/api/decision-sessions")
    assert resp.status_code == 200
    assert resp.json() == []


async def test_get_unknown_session_returns_404(client):
    resp = await client.get("/api/decision-sessions/999999")
    assert resp.status_code == 404


async def test_analytics_route_before_id_route(client, db_session):
    # Regression guard: /analytics must not be captured by GET /{session_id}
    await _seed_district(db_session)
    resp = await client.get("/api/decision-sessions/analytics")
    assert resp.status_code == 200
    assert resp.json()["total_sessions"] == 0


async def test_list_and_get_after_create(client, db_session):
    district = await _seed_district(db_session)
    await DecisionSessionService.create(db_session, "run-api-1", "Reduce congestion", district.id)

    list_resp = await client.get("/api/decision-sessions")
    assert list_resp.status_code == 200
    assert len(list_resp.json()) == 1
    session_id = list_resp.json()[0]["id"]

    get_resp = await client.get(f"/api/decision-sessions/{session_id}")
    assert get_resp.status_code == 200
    assert get_resp.json()["run_id"] == "run-api-1"


async def test_observe_returns_409_when_not_observing(client, db_session):
    district = await _seed_district(db_session)
    await DecisionSessionService.create(db_session, "run-api-2", "goal", district.id)
    list_resp = await client.get("/api/decision-sessions")
    session_id = list_resp.json()[0]["id"]

    resp = await client.post(f"/api/decision-sessions/{session_id}/observe")
    assert resp.status_code == 409  # still "collecting", never approved


async def test_observe_success_after_approval(client, db_session):
    district = await _seed_district(db_session, aqi_index=200)
    await DecisionSessionService.create(db_session, "run-api-3", "goal", district.id)
    list_resp = await client.get("/api/decision-sessions")
    session_id = list_resp.json()[0]["id"]

    approved = await DecisionSessionService.mark_approved(db_session, "run-api-3")
    assert approved.id == session_id

    db_session.add(AQI(city_id="hanoi", district_id=district.id, timestamp=datetime.now(timezone.utc),
                        pm25=10.0, pm10=20.0, co=0.5, no2=10.0, aqi_index=40))
    await db_session.flush()

    resp = await client.post(f"/api/decision-sessions/{session_id}/observe")
    assert resp.status_code == 200
    assert resp.json()["status"] == "evaluated"

    second = await client.post(f"/api/decision-sessions/{session_id}/observe")
    assert second.status_code == 409  # already evaluated
