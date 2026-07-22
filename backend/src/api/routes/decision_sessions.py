from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from src.database.connection import get_db
from src.services.decision_session_service import DecisionSessionService
from src.utils.auth import require_api_key

router = APIRouter(prefix="/api/decision-sessions", tags=["decision-sessions"])


# NOTE: /analytics MUST be declared before /{session_id} — FastAPI matches
# routes in registration order, and /{session_id}: int would otherwise
# capture the literal path "analytics" and fail int-coercion with a 422
# before ever reaching the analytics route.
@router.get("/analytics")
async def get_analytics(session: AsyncSession = Depends(get_db)):
    return await DecisionSessionService.analytics(session)


@router.get("")
async def list_sessions(status: str | None = None, session: AsyncSession = Depends(get_db)):
    records = await DecisionSessionService.list_sessions(session, status=status)
    return [r.to_dict() for r in records]


@router.get("/{session_id}")
async def get_session(session_id: int, session: AsyncSession = Depends(get_db)):
    record = await DecisionSessionService.get(session, session_id)
    if record is None:
        raise HTTPException(status_code=404, detail="Decision session not found")
    return record.to_dict()


@router.post("/{session_id}/observe", dependencies=[Depends(require_api_key)])
async def observe_session(session_id: int, session: AsyncSession = Depends(get_db)):
    record = await DecisionSessionService.observe(session, session_id)
    if record is None:
        existing = await DecisionSessionService.get(session, session_id)
        if existing is None:
            raise HTTPException(status_code=404, detail="Decision session not found")
        raise HTTPException(status_code=409, detail=f"Session is '{existing.status}', not 'observing'")
    return record.to_dict()
