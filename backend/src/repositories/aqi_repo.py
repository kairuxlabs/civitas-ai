from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.models.aqi import AQI


class AQIRepo:
    @staticmethod
    async def save(session: AsyncSession, aqi: AQI) -> AQI:
        session.add(aqi)
        await session.commit()
        await session.refresh(aqi)
        return aqi

    @staticmethod
    async def get_latest(session: AsyncSession, district_id: int) -> AQI | None:
        result = await session.execute(
            select(AQI)
            .where(AQI.district_id == district_id)
            .order_by(AQI.timestamp.desc())
            .limit(1)
        )
        return result.scalar_one_or_none()

    @staticmethod
    async def get_recent(session: AsyncSession, district_id: int, limit: int = 24) -> list[AQI]:
        result = await session.execute(
            select(AQI)
            .where(AQI.district_id == district_id)
            .order_by(AQI.timestamp.desc())
            .limit(limit)
        )
        rows = result.scalars().all()
        return list(reversed(rows))
