import asyncio
import pytest
import aiohttp
from unittest.mock import AsyncMock, MagicMock, patch
from src.pipelines.aqi_pipeline import AQIPipeline
from src.models.district import District


@pytest.mark.asyncio
async def test_aqi_pipeline_saves_records(db_session):
    district = District(city_id="hanoi", name="Test District")
    db_session.add(district)
    await db_session.flush()

    mock_response = {
        "results": [{
            "id": 1,
            "name": "Hanoi Station",
            "coordinates": {"latitude": 21.03, "longitude": 105.85},
            "sensors": [],
        }]
    }

    with patch("src.pipelines.aqi_pipeline.aiohttp.ClientSession") as mock_client:
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

        await AQIPipeline.run(db_session)

    from sqlalchemy import select
    from src.models.aqi import AQI
    result = await db_session.execute(select(AQI))
    records = result.scalars().all()
    assert len(records) >= 1


@pytest.mark.asyncio
async def test_aqi_pipeline_returns_gracefully_on_timeout(db_session):
    district = District(city_id="hanoi", name="Test District")
    db_session.add(district)
    await db_session.flush()

    with patch("src.pipelines.aqi_pipeline.aiohttp.ClientSession") as mock_client:
        mock_session = MagicMock()
        mock_session.get = MagicMock(side_effect=asyncio.TimeoutError())
        mock_session.__aenter__ = AsyncMock(return_value=mock_session)
        mock_session.__aexit__ = AsyncMock(return_value=None)
        mock_client.return_value = mock_session

        # Must not raise — the pipeline should log and return gracefully.
        await AQIPipeline.run(db_session)

    from sqlalchemy import select
    from src.models.aqi import AQI
    result = await db_session.execute(select(AQI))
    assert result.scalars().all() == []


@pytest.mark.asyncio
async def test_aqi_pipeline_returns_gracefully_on_connection_error(db_session):
    district = District(city_id="hanoi", name="Test District")
    db_session.add(district)
    await db_session.flush()

    with patch("src.pipelines.aqi_pipeline.aiohttp.ClientSession") as mock_client:
        mock_session = MagicMock()
        mock_session.get = MagicMock(side_effect=aiohttp.ClientConnectionError("boom"))
        mock_session.__aenter__ = AsyncMock(return_value=mock_session)
        mock_session.__aexit__ = AsyncMock(return_value=None)
        mock_client.return_value = mock_session

        # Must not raise — one bad pipeline step shouldn't kill the 15-min cycle.
        await AQIPipeline.run(db_session)

    from sqlalchemy import select
    from src.models.aqi import AQI
    result = await db_session.execute(select(AQI))
    assert result.scalars().all() == []
