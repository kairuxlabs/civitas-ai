from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from src.database.connection import get_db
from src.orchestrator.graph import run_agent_graph
from src.schemas.decision import DecisionOut

router = APIRouter(prefix="/api/chat", tags=["chat"])


class ChatRequest(BaseModel):
    query: str
    district_id: int


@router.post("", response_model=DecisionOut)
async def chat(request: ChatRequest, session: AsyncSession = Depends(get_db)):
    return await run_agent_graph(
        query=request.query,
        district_id=request.district_id,
        session=session,
    )
