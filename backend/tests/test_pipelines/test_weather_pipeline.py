import asyncio
import pytest
import aiohttp
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


@pytest.mark.asyncio
async def test_weather_pipeline_fetches_distinct_readings_per_district(db_session):
    hoan_kiem = District(city_id="hanoi", name="Hoàn Kiếm")
    ha_dong = District(city_id="hanoi", name="Hà Đông")
    db_session.add_all([hoan_kiem, ha_dong])
    await db_session.flush()

    # Open-Meteo returns a list (one structure per input coordinate pair,
    # same order as the request) once more than one lat/lon is queried.
    mock_response = [
        {"current": {"temperature_2m": 30.0, "relative_humidity_2m": 70.0, "precipitation": 0.0, "wind_speed_10m": 8.0}},
        {"current": {"temperature_2m": 34.5, "relative_humidity_2m": 55.0, "precipitation": 2.0, "wind_speed_10m": 15.0}},
    ]

    with patch("src.pipelines.weather_pipeline.aiohttp.ClientSession") as mock_client:
        mock_resp = MagicMock()
        mock_resp.json = AsyncMock(return_value=mock_response)
        mock_resp.__aenter__ = AsyncMock(return_value=mock_resp)
        mock_resp.__aexit__ = AsyncMock(return_value=None)

        captured_url = {}

        def fake_get(url, *args, **kwargs):
            captured_url["url"] = url
            return mock_resp

        mock_session = MagicMock()
        mock_session.get = MagicMock(side_effect=fake_get)
        mock_session.__aenter__ = AsyncMock(return_value=mock_session)
        mock_session.__aexit__ = AsyncMock(return_value=None)
        mock_client.return_value = mock_session

        await WeatherPipeline.run(db_session)

    # The request itself must carry both districts' real coordinates, not
    # a single shared point.
    assert "21.0285,20.9718" == captured_url["url"].split("latitude=")[1].split("&")[0]

    from sqlalchemy import select
    from src.models.weather import Weather
    result = await db_session.execute(select(Weather))
    records = {r.district_id: r for r in result.scalars().all()}
    assert records[hoan_kiem.id].temperature == 30.0
    assert records[ha_dong.id].temperature == 34.5
    assert records[hoan_kiem.id].temperature != records[ha_dong.id].temperature


@pytest.mark.asyncio
async def test_weather_pipeline_returns_gracefully_on_timeout(db_session):
    district = District(city_id="hanoi", name="Test District")
    db_session.add(district)
    await db_session.flush()

    with patch("src.pipelines.weather_pipeline.aiohttp.ClientSession") as mock_client:
        mock_session = MagicMock()
        mock_session.get = MagicMock(side_effect=asyncio.TimeoutError())
        mock_session.__aenter__ = AsyncMock(return_value=mock_session)
        mock_session.__aexit__ = AsyncMock(return_value=None)
        mock_client.return_value = mock_session

        # Must not raise — the pipeline should log and return gracefully.
        await WeatherPipeline.run(db_session)

    from sqlalchemy import select
    from src.models.weather import Weather
    result = await db_session.execute(select(Weather))
    assert result.scalars().all() == []


@pytest.mark.asyncio
async def test_weather_pipeline_returns_gracefully_on_connection_error(db_session):
    district = District(city_id="hanoi", name="Test District")
    db_session.add(district)
    await db_session.flush()

    with patch("src.pipelines.weather_pipeline.aiohttp.ClientSession") as mock_client:
        mock_session = MagicMock()
        mock_session.get = MagicMock(side_effect=aiohttp.ClientConnectionError("boom"))
        mock_session.__aenter__ = AsyncMock(return_value=mock_session)
        mock_session.__aexit__ = AsyncMock(return_value=None)
        mock_client.return_value = mock_session

        # Must not raise — one bad pipeline step shouldn't kill the 15-min cycle.
        await WeatherPipeline.run(db_session)

    from sqlalchemy import select
    from src.models.weather import Weather
    result = await db_session.execute(select(Weather))
    assert result.scalars().all() == []
