from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from src.database.connection import get_db
from src.models.decision import AgentDecision
from src.utils.auth import require_api_key
from src.ws.manager import manager

router = APIRouter(prefix="/api/decisions", tags=["decisions"])


async def _set_approval(decision_id: int, approved: bool, session: AsyncSession) -> dict:
    result = await session.execute(select(AgentDecision).where(AgentDecision.id == decision_id))
    decision = result.scalar_one_or_none()
    if not decision:
        raise HTTPException(status_code=404, detail="Decision not found")
    decision.approved = approved
    await session.commit()

    status = "approved" if approved else "rejected"
    detail = (
        f"Decision {decision_id} approved — executing workflow"
        if approved
        else f"Decision {decision_id} rejected by operator"
    )
    await manager.broadcast({
        "type": "approval_result",
        "agent": "Supervisor",
        "status": status,
        "detail": detail,
        "ts": datetime.now(timezone.utc).isoformat(),
    })
    return {"id": decision_id, "approved": approved}


@router.post("/{decision_id}/approve", dependencies=[Depends(require_api_key)])
async def approve_decision(decision_id: int, session: AsyncSession = Depends(get_db)):
    return await _set_approval(decision_id, True, session)


@router.post("/{decision_id}/reject", dependencies=[Depends(require_api_key)])
async def reject_decision(decision_id: int, session: AsyncSession = Depends(get_db)):
    return await _set_approval(decision_id, False, session)
