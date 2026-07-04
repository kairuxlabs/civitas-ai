# backend/tests/test_agents/test_orchestrator.py
from datetime import datetime, timezone

from src.models.district import District
from src.models.weather import Weather
from src.models.aqi import AQI
from src.orchestrator.graph import run_agent_graph


async def test_agent_graph_returns_decision(db_session):
    district = District(city_id="hanoi", name="Test")
    db_session.add(district)
    await db_session.flush()

    now = datetime.now(timezone.utc)
    db_session.add(Weather(
        city_id="hanoi", district_id=district.id, timestamp=now,
        temperature=33.0, humidity=80.0, rain=5.0, wind_speed=8.0
    ))
    db_session.add(AQI(
        city_id="hanoi", district_id=district.id, timestamp=now,
        pm25=75.0, pm10=110.0, co=1.5, no2=55.0, aqi_index=130
    ))
    await db_session.flush()

    result = await run_agent_graph(
        query="What is the current urban situation?",
        district_id=district.id,
        session=db_session,
    )

    assert result.prediction != {}
    assert result.impact != {}
    assert len(result.recommendations) >= 1
    assert 0 <= result.confidence <= 100
    assert len(result.explanation) >= 4


async def test_agent_graph_no_sensor_data(db_session):
    """Pipeline must not crash when no weather/AQI rows exist (all defaults)."""
    district = District(city_id="hanoi", name="Empty")
    db_session.add(district)
    await db_session.flush()

    result = await run_agent_graph(
        query="Status check",
        district_id=district.id,
        session=db_session,
    )

    assert result.prediction != {}
    assert len(result.recommendations) >= 1
    assert 0 <= result.confidence <= 100


async def test_agent_graph_null_rain_field(db_session):
    """Pipeline must handle None rain field without TypeError."""
    district = District(city_id="hanoi", name="NullRain")
    db_session.add(district)
    await db_session.flush()

    now = datetime.now(timezone.utc)
    db_session.add(Weather(
        city_id="hanoi", district_id=district.id, timestamp=now,
        temperature=35.0, humidity=90.0, rain=None, wind_speed=None
    ))
    db_session.add(AQI(
        city_id="hanoi", district_id=district.id, timestamp=now,
        pm25=None, pm10=None, co=None, no2=None, aqi_index=None
    ))
    await db_session.flush()

    result = await run_agent_graph(
        query="Null sensor test",
        district_id=district.id,
        session=db_session,
    )

    assert result.prediction != {}
    assert 0 <= result.confidence <= 100


async def test_simulate_heavy_rain_via_api(db_session, client):
    """Simulate endpoint must apply rain multiplier and return valid decision."""
    district = District(city_id="hanoi", name="Sim")
    db_session.add(district)
    await db_session.flush()

    now = datetime.now(timezone.utc)
    db_session.add(Weather(
        city_id="hanoi", district_id=district.id, timestamp=now,
        temperature=28.0, humidity=85.0, rain=3.0, wind_speed=5.0
    ))
    db_session.add(AQI(
        city_id="hanoi", district_id=district.id, timestamp=now,
        pm25=40.0, pm10=70.0, co=1.0, no2=35.0, aqi_index=90
    ))
    await db_session.commit()

    response = await client.post(
        "/api/simulate",
        json={"scenario": "heavy_rain", "district_id": district.id},
    )
    assert response.status_code == 200
    data = response.json()
    assert "prediction" in data
    assert "recommendations" in data
    assert data["prediction"]["flood_risk"] == "high"


async def test_simulate_air_pollution_via_api(db_session, client):
    """air_pollution scenario raises AQI enough to trigger hazardous recommendations."""
    district = District(city_id="hanoi", name="Polluted")
    db_session.add(district)
    await db_session.flush()

    now = datetime.now(timezone.utc)
    db_session.add(Weather(
        city_id="hanoi", district_id=district.id, timestamp=now,
        temperature=30.0, humidity=70.0, rain=0.0, wind_speed=10.0
    ))
    db_session.add(AQI(
        city_id="hanoi", district_id=district.id, timestamp=now,
        pm25=60.0, pm10=90.0, co=1.2, no2=45.0, aqi_index=90
    ))
    await db_session.commit()

    response = await client.post(
        "/api/simulate",
        json={"scenario": "air_pollution", "district_id": district.id},
    )
    assert response.status_code == 200
    data = response.json()
    # aqi_index = 90 + 80 = 170 → hazardous → advisory in recommendations
    assert any("air quality" in r.lower() or "advisory" in r.lower() for r in data["recommendations"])


async def test_simulate_unknown_scenario_uses_defaults(db_session, client):
    """Unknown scenario key must not crash — falls back to neutral params."""
    district = District(city_id="hanoi", name="Unknown")
    db_session.add(district)
    await db_session.flush()

    now = datetime.now(timezone.utc)
    db_session.add(Weather(
        city_id="hanoi", district_id=district.id, timestamp=now,
        temperature=28.0, humidity=65.0, rain=0.0, wind_speed=5.0
    ))
    db_session.add(AQI(
        city_id="hanoi", district_id=district.id, timestamp=now,
        pm25=30.0, pm10=55.0, co=0.8, no2=30.0, aqi_index=70
    ))
    await db_session.commit()

    response = await client.post(
        "/api/simulate",
        json={"scenario": "nonexistent_scenario", "district_id": district.id},
    )
    assert response.status_code == 200
    data = response.json()
    assert "prediction" in data
