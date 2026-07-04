from datetime import datetime, timezone, timedelta
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from src.models.event import Event


class EventRepo:
    @staticmethod
    async def get_current(session: AsyncSession, district_id: int, limit: int = 5) -> list[Event]:
        """Return active or recently started events for a district (last 24h window)."""
        cutoff = datetime.now(timezone.utc) - timedelta(hours=24)
        result = await session.execute(
            select(Event)
            .where(Event.district_id == district_id)
            .where(Event.start_time >= cutoff)
            .order_by(Event.start_time.desc())
            .limit(limit)
        )
        return list(result.scalars().all())
