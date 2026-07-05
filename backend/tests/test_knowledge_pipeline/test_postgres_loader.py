import pytest

from src.knowledge_pipeline.loaders.postgres_loader import update_district_geojson
from src.models.district import District


@pytest.mark.asyncio
async def test_updates_matching_district_by_name(db_session):
    db_session.add(District(city_id="hanoi", name="Ba Đình"))
    db_session.add(District(city_id="hanoi", name="Hoàn Kiếm"))
    await db_session.flush()

    feature = {"type": "Feature", "properties": {"name": "Ba Đình"}, "geometry": {"type": "MultiLineString", "coordinates": []}}
    count = await update_district_geojson(db_session, {"Ba Đình": feature})

    assert count == 1
    from sqlalchemy import select
    result = await db_session.execute(select(District).where(District.name == "Ba Đình"))
    assert result.scalar_one().geojson == feature


@pytest.mark.asyncio
async def test_ignores_unmatched_district_names(db_session):
    db_session.add(District(city_id="hanoi", name="Cầu Giấy"))
    await db_session.flush()

    count = await update_district_geojson(db_session, {"Nonexistent District": {"type": "Feature"}})
    assert count == 0
