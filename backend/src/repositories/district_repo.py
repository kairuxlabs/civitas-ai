from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.models.district import District


class DistrictRepo:
    @staticmethod
    async def get_all(session: AsyncSession) -> list[District]:
        result = await session.execute(select(District).where(District.city_id == "hanoi"))
        return list(result.scalars().all())

    @staticmethod
    async def get_by_id(session: AsyncSession, district_id: int) -> District | None:
        result = await session.execute(select(District).where(District.id == district_id))
        return result.scalar_one_or_none()
