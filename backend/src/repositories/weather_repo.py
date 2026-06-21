from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.models.weather import Weather


class WeatherRepo:
    @staticmethod
    async def save(session: AsyncSession, weather: Weather) -> Weather:
        session.add(weather)
        await session.commit()
        await session.refresh(weather)
        return weather

    @staticmethod
    async def get_latest(session: AsyncSession, district_id: int) -> Weather | None:
        result = await session.execute(
            select(Weather)
            .where(Weather.district_id == district_id)
            .order_by(Weather.timestamp.desc())
            .limit(1)
        )
        return result.scalar_one_or_none()
