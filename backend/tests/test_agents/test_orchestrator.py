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
    assert len(result.explanation) == 5
