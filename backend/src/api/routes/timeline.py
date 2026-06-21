from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from src.database.connection import get_db
from src.models.decision import AgentDecision
from src.schemas.decision import AgentDecisionOut

router = APIRouter(prefix="/api/timeline", tags=["timeline"])

@router.get("", response_model=list[AgentDecisionOut])
async def get_timeline(limit: int = 20, session: AsyncSession = Depends(get_db)):
    result = await session.execute(
        select(AgentDecision)
        .order_by(AgentDecision.created_at.desc())
        .limit(limit)
    )
    records = list(result.scalars().all())
    return [AgentDecisionOut.model_validate(r) for r in records]
