import asyncio
import pytest
import aiohttp
from unittest.mock import AsyncMock, MagicMock, patch
from src.pipelines.aqi_pipeline import AQIPipeline, pm25_to_aqi
from src.models.district import District
from src.utils.config import settings


def _make_json_response(payload):
    resp = MagicMock()
    resp.json = AsyncMock(return_value=payload)
    resp.__aenter__ = AsyncMock(return_value=resp)
    resp.__aexit__ = AsyncMock(return_value=None)
    return resp


def _mock_session_for(locations_payload, latest_payload_by_station_id):
    """A ClientSession double that returns the locations payload for the
    /locations search and a per-station payload for each /locations/{id}/latest
    call, so the two-step OpenAQ lookup can be exercised without real network."""
    locations_resp = _make_json_response(locations_payload)

    def fake_get(url, *args, **kwargs):
        if url.rstrip("/").endswith("/latest"):
            station_id = int(url.rstrip("/").split("/")[-2])
            return _make_json_response(latest_payload_by_station_id[station_id])
        return locations_resp

    mock_session = MagicMock()
    mock_session.get = MagicMock(side_effect=fake_get)
    mock_session.__aenter__ = AsyncMock(return_value=mock_session)
    mock_session.__aexit__ = AsyncMock(return_value=None)
    return mock_session


@pytest.mark.asyncio
async def test_aqi_pipeline_saves_real_fetched_values_not_random(db_session, monkeypatch):
    monkeypatch.setattr(settings, "openaq_api_key", "test-key")
    district = District(city_id="hanoi", name="Hoàn Kiếm")
    db_session.add(district)
    await db_session.flush()

    locations_payload = {
        "results": [{
            "id": 501,
            "name": "Hanoi Station",
            "coordinates": {"latitude": 21.03, "longitude": 105.85},
            "sensors": [
                {"id": 10, "name": "pm25 µg/m³", "parameter": {"name": "pm25"}},
                {"id": 11, "name": "pm10 µg/m³", "parameter": {"name": "pm10"}},
            ],
        }]
    }
    latest_payload = {501: {"results": [
        {"sensorsId": 10, "value": 42.5},
        {"sensorsId": 11, "value": 60.0},
    ]}}

    with patch("src.pipelines.aqi_pipeline.aiohttp.ClientSession") as mock_client:
        mock_client.return_value = _mock_session_for(locations_payload, latest_payload)
        await AQIPipeline.run(db_session)

    from sqlalchemy import select
    from src.models.aqi import AQI
    result = await db_session.execute(select(AQI))
    records = result.scalars().all()
    assert len(records) == 1
    assert records[0].pm25 == 42.5
    assert records[0].pm10 == 60.0
    assert records[0].aqi_index == pm25_to_aqi(42.5)


@pytest.mark.asyncio
async def test_aqi_pipeline_assigns_nearest_station_per_district(db_session, monkeypatch):
    monkeypatch.setattr(settings, "openaq_api_key", "test-key")
    hoan_kiem = District(city_id="hanoi", name="Hoàn Kiếm")
    ha_dong = District(city_id="hanoi", name="Hà Đông")
    db_session.add_all([hoan_kiem, ha_dong])
    await db_session.flush()

    locations_payload = {
        "results": [
            {
                "id": 1,
                "coordinates": {"latitude": 21.0285, "longitude": 105.8542},  # near Hoàn Kiếm
                "sensors": [{"id": 10, "parameter": {"name": "pm25"}}],
            },
            {
                "id": 2,
                "coordinates": {"latitude": 20.9718, "longitude": 105.7797},  # near Hà Đông
                "sensors": [{"id": 20, "parameter": {"name": "pm25"}}],
            },
        ]
    }
    latest_payload = {
        1: {"results": [{"sensorsId": 10, "value": 30.0}]},
        2: {"results": [{"sensorsId": 20, "value": 90.0}]},
    }

    with patch("src.pipelines.aqi_pipeline.aiohttp.ClientSession") as mock_client:
        mock_client.return_value = _mock_session_for(locations_payload, latest_payload)
        await AQIPipeline.run(db_session)

    from sqlalchemy import select
    from src.models.aqi import AQI
    result = await db_session.execute(select(AQI))
    by_district = {r.district_id: r for r in result.scalars().all()}
    assert by_district[hoan_kiem.id].pm25 == 30.0
    assert by_district[ha_dong.id].pm25 == 90.0


@pytest.mark.asyncio
async def test_aqi_pipeline_skips_without_api_key(db_session, monkeypatch):
    monkeypatch.setattr(settings, "openaq_api_key", "")
    district = District(city_id="hanoi", name="Test District")
    db_session.add(district)
    await db_session.flush()

    with patch("src.pipelines.aqi_pipeline.aiohttp.ClientSession") as mock_client:
        await AQIPipeline.run(db_session)
        mock_client.assert_not_called()

    from sqlalchemy import select
    from src.models.aqi import AQI
    result = await db_session.execute(select(AQI))
    assert result.scalars().all() == []


@pytest.mark.asyncio
async def test_aqi_pipeline_returns_gracefully_on_timeout(db_session, monkeypatch):
    monkeypatch.setattr(settings, "openaq_api_key", "test-key")
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
async def test_aqi_pipeline_returns_gracefully_on_connection_error(db_session, monkeypatch):
    monkeypatch.setattr(settings, "openaq_api_key", "test-key")
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


@pytest.mark.asyncio
async def test_aqi_pipeline_returns_gracefully_when_no_station_has_pm25(db_session, monkeypatch):
    monkeypatch.setattr(settings, "openaq_api_key", "test-key")
    district = District(city_id="hanoi", name="Test District")
    db_session.add(district)
    await db_session.flush()

    locations_payload = {"results": [{
        "id": 1,
        "coordinates": {"latitude": 21.03, "longitude": 105.85},
        "sensors": [{"id": 99, "parameter": {"name": "co"}}],  # no pm25 sensor
    }]}
    latest_payload = {1: {"results": [{"sensorsId": 99, "value": 0.5}]}}

    with patch("src.pipelines.aqi_pipeline.aiohttp.ClientSession") as mock_client:
        mock_client.return_value = _mock_session_for(locations_payload, latest_payload)
        await AQIPipeline.run(db_session)

    from sqlalchemy import select
    from src.models.aqi import AQI
    result = await db_session.execute(select(AQI))
    assert result.scalars().all() == []


def test_pm25_to_aqi_matches_epa_breakpoints():
    assert pm25_to_aqi(0.0) == 0
    assert pm25_to_aqi(12.0) == 50
    assert pm25_to_aqi(35.4) == 100
    assert pm25_to_aqi(55.4) == 150
    assert pm25_to_aqi(1000.0) == 500
