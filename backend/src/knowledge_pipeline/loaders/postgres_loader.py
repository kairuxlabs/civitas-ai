from sqlalchemy.ext.asyncio import AsyncSession

from src.repositories.district_repo import DistrictRepo


async def update_district_geojson(session: AsyncSession, district_geojson: dict[str, dict]) -> int:
    """Match GeoJSON Features (keyed by district name) to District rows and
    persist. Returns the number of districts updated."""
    districts = await DistrictRepo.get_all(session)
    updated = 0
    for district in districts:
        feature = district_geojson.get(district.name)
        if feature:
            district.geojson = feature
            updated += 1
    await session.commit()
    return updated
