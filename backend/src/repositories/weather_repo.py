from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.models.weather import Weather


class WeatherRepo:
    @staticmethod
    async def save_all(session: AsyncSession, weathers: list[Weather]) -> None:
        session.add_all(weathers)
        await session.commit()

    @staticmethod
    async def get_latest(session: AsyncSession, district_id: int) -> Weather | None:
        result = await session.execute(
            select(Weather)
            .where(Weather.district_id == district_id)
            .order_by(Weather.timestamp.desc())
            .limit(1)
        )
        return result.scalar_one_or_none()
