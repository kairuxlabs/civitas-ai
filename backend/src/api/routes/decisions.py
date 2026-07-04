from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from src.database.connection import get_db
from src.models.decision import AgentDecision
from src.ws.manager import manager

router = APIRouter(prefix="/api/decisions", tags=["decisions"])


@router.post("/{decision_id}/approve")
async def approve_decision(decision_id: int, session: AsyncSession = Depends(get_db)):
    result = await session.execute(select(AgentDecision).where(AgentDecision.id == decision_id))
    decision = result.scalar_one_or_none()
    if not decision:
        raise HTTPException(status_code=404, detail="Decision not found")
    decision.approved = True
    await session.commit()
    await manager.broadcast({
        "type": "approval_result",
        "agent": "Supervisor",
        "status": "approved",
        "detail": f"Decision {decision_id} approved — executing workflow",
        "ts": datetime.now().isoformat(),
    })
    return {"id": decision_id, "approved": True}


@router.post("/{decision_id}/reject")
async def reject_decision(decision_id: int, session: AsyncSession = Depends(get_db)):
    result = await session.execute(select(AgentDecision).where(AgentDecision.id == decision_id))
    decision = result.scalar_one_or_none()
    if not decision:
        raise HTTPException(status_code=404, detail="Decision not found")
    decision.approved = False
    await session.commit()
    await manager.broadcast({
        "type": "approval_result",
        "agent": "Supervisor",
        "status": "rejected",
        "detail": f"Decision {decision_id} rejected by operator",
        "ts": datetime.now().isoformat(),
    })
    return {"id": decision_id, "approved": False}
