from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.models.city_score import CityScore


class CityScoreRepo:
    @staticmethod
    async def get_latest_by_district(session: AsyncSession, district_id: int) -> CityScore | None:
        result = await session.execute(
            select(CityScore)
            .where(CityScore.district_id == district_id)
            .order_by(CityScore.timestamp.desc())
            .limit(1)
        )
        return result.scalar_one_or_none()

    @staticmethod
    async def get_recent(session: AsyncSession, district_id: int, limit: int = 24) -> list[CityScore]:
        result = await session.execute(
            select(CityScore)
            .where(CityScore.district_id == district_id)
            .order_by(CityScore.timestamp.desc())
            .limit(limit)
        )
        rows = result.scalars().all()
        return list(reversed(rows))

    @staticmethod
    async def save(session: AsyncSession, score: CityScore) -> CityScore:
        session.add(score)
        await session.commit()
        await session.refresh(score)
        return score

    @staticmethod
    async def get_city_overview(session: AsyncSession, city_id: str = "hanoi") -> list[CityScore]:
        # Portable "latest row per district_id" via GROUP BY + MAX, rather than
        # Postgres-only `DISTINCT ON`, which silently degrades to a plain
        # SELECT DISTINCT (no collapsing per district) on SQLite — the dialect
        # used by the test suite.
        subq = (
            select(
                CityScore.district_id,
                func.max(CityScore.timestamp).label("max_timestamp"),
            )
            .where(CityScore.city_id == city_id)
            .group_by(CityScore.district_id)
            .subquery()
        )
        result = await session.execute(
            select(CityScore).join(
                subq,
                (CityScore.district_id == subq.c.district_id) &
                (CityScore.timestamp == subq.c.max_timestamp)
            )
        )
        return list(result.scalars().all())
