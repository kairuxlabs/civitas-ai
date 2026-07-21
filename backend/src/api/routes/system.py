from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.agents.gemini_client import GEMINI_MODEL, GEMINI_TEMPERATURE
from src.ai.planner import PLANNER_MODELS
from src.database.connection import get_db
from src.schemas.system import SystemStatusOut
from src.utils.config import settings

router = APIRouter(prefix="/api/system", tags=["system"])


@router.get("/status", response_model=SystemStatusOut)
async def system_status(session: AsyncSession = Depends(get_db)):
    try:
        await session.execute(select(1))
        database_ok = True
    except Exception:
        database_ok = False

    return SystemStatusOut(
        database=database_ok,
        gemini_configured=bool(settings.gemini_api_key),
        neo4j_configured=bool(settings.neo4j_uri),
        qdrant_configured=bool(settings.qdrant_url),
        openrouter_configured=bool(settings.openrouter_api_key),
        gemini_model=GEMINI_MODEL,
        gemini_temperature=GEMINI_TEMPERATURE,
        openrouter_fallback_models=PLANNER_MODELS,
    )
