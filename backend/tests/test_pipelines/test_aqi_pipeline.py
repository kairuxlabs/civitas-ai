import pytest
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
