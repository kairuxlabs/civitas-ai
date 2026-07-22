import pytest
from datetime import datetime, timezone

from src.models.aqi import AQI
from src.models.district import District


@pytest.mark.asyncio
async def test_get_aqi_history_empty(client):
    response = await client.get("/api/aqi/history/1")
    assert response.status_code == 200
    assert response.json() == []


@pytest.mark.asyncio
async def test_get_aqi_history_returns_recent_readings(db_session, client):
    district = District(city_id="hanoi", name="Test")
    db_session.add(district)
    await db_session.flush()
    db_session.add(AQI(
        city_id="hanoi", district_id=district.id, timestamp=datetime.now(timezone.utc),
        pm25=50.0, pm10=80.0, co=1.0, no2=40.0, aqi_index=100,
    ))
    await db_session.commit()

    response = await client.get(f"/api/aqi/history/{district.id}")
    assert response.status_code == 200
    assert len(response.json()) == 1


@pytest.mark.asyncio
async def test_get_aqi_history_limit_over_cap_rejected(client):
    response = await client.get("/api/aqi/history/1?limit=99999")
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_get_aqi_history_limit_within_cap_ok(client):
    response = await client.get("/api/aqi/history/1?limit=100")
    assert response.status_code == 200
