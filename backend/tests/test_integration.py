from src.models.district import District
from src.models.weather import Weather
from src.models.aqi import AQI
from src.orchestrator.graph import run_agent_graph
from datetime import datetime, timezone


async def test_full_pipeline_to_decision(db_session, client):
    district = District(city_id="hanoi", name="Integration Test District")
    db_session.add(district)
    await db_session.flush()

    now = datetime.now(timezone.utc)
    db_session.add(Weather(
        city_id="hanoi", district_id=district.id, timestamp=now,
        temperature=34.0, humidity=85.0, rain=15.0, wind_speed=5.0
    ))
    db_session.add(AQI(
        city_id="hanoi", district_id=district.id, timestamp=now,
        pm25=90.0, pm10=130.0, co=2.0, no2=60.0, aqi_index=155
    ))
    await db_session.commit()

    # Test via graph directly
    decision = await run_agent_graph("What action should we take?", district.id, db_session)
    assert decision.prediction != {}
    assert decision.impact != {}
    assert len(decision.recommendations) >= 1
    assert 0 < decision.confidence <= 100
    assert len(decision.explanation) == 5

    # Test via API
    response = await client.post("/api/chat", json={"query": "Status?", "district_id": district.id})
    assert response.status_code == 200
    data = response.json()
    assert "prediction" in data
    assert "recommendations" in data
    assert "confidence" in data
    assert "explanation" in data
    assert "impact" in data
