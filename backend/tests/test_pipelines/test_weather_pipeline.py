import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime, timezone
from src.pipelines.weather_pipeline import WeatherPipeline
from src.models.district import District


@pytest.mark.asyncio
async def test_weather_pipeline_saves_records(db_session):
    district = District(city_id="hanoi", name="Test District")
    db_session.add(district)
    await db_session.flush()

    mock_response = {
        "current": {
            "time": "2026-06-21T10:00",
            "temperature_2m": 32.5,
            "relative_humidity_2m": 75.0,
            "precipitation": 0.0,
            "wind_speed_10m": 12.0,
        }
    }

    with patch("src.pipelines.weather_pipeline.aiohttp.ClientSession") as mock_client:
        # Mock the response object that supports async context manager
        mock_resp = MagicMock()
        mock_resp.json = AsyncMock(return_value=mock_response)
        mock_resp.__aenter__ = AsyncMock(return_value=mock_resp)
        mock_resp.__aexit__ = AsyncMock(return_value=None)

        # Mock the ClientSession instance
        mock_session = MagicMock()
        mock_session.get = MagicMock(return_value=mock_resp)
        mock_session.__aenter__ = AsyncMock(return_value=mock_session)
        mock_session.__aexit__ = AsyncMock(return_value=None)

        # Mock ClientSession constructor
        mock_client.return_value = mock_session

        await WeatherPipeline.run(db_session)

    from sqlalchemy import select
    from src.models.weather import Weather
    result = await db_session.execute(select(Weather))
    records = result.scalars().all()
    assert len(records) == 1
    assert records[0].temperature == 32.5
