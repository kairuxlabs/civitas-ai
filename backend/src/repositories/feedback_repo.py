from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from src.models.feedback import CitizenFeedback


class FeedbackRepo:
    @staticmethod
    async def get_recent(session: AsyncSession, district_id: int, limit: int = 10) -> list[CitizenFeedback]:
        """Return most recent citizen feedback for a district."""
        result = await session.execute(
            select(CitizenFeedback)
            .where(CitizenFeedback.district_id == district_id)
            .order_by(CitizenFeedback.created_at.desc())
            .limit(limit)
        )
        return list(result.scalars().all())
