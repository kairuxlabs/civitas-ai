# backend/src/api/routes/simulation_v2.py
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from src.crawlers.crawl_service import ALL_SOURCES, run_crawl
from src.database.connection import get_db
from src.simulation.engine import simulation
from src.simulation.profiles import PROFILES
from src.utils.auth import require_api_key

router = APIRouter(prefix="/api/v2", tags=["simulation"])


class SimulationStartIn(BaseModel):
    scenario: str
    interval_s: float = Field(default=30.0, ge=5.0, le=600.0)
    auto_goal: bool = True


class CrawlIn(BaseModel):
    sources: list[str] | None = None


@router.post("/simulation/start", dependencies=[Depends(require_api_key)])
async def start_simulation(body: SimulationStartIn):
    if body.scenario not in PROFILES:
        raise HTTPException(status_code=422, detail=f"Unknown scenario. Available: {sorted(PROFILES)}")
    return await simulation.start(body.scenario, interval_s=body.interval_s, auto_goal=body.auto_goal)


@router.post("/simulation/stop", dependencies=[Depends(require_api_key)])
async def stop_simulation():
    return await simulation.stop()


@router.get("/simulation/status")
async def simulation_status():
    return simulation.status()


@router.get("/simulation/scenarios")
async def simulation_scenarios():
    return {"scenarios": [{"name": p.name, "label": p.label} for p in PROFILES.values()]}


@router.post("/crawl", dependencies=[Depends(require_api_key)])
async def crawl(body: CrawlIn, session: AsyncSession = Depends(get_db)):
    sources = body.sources or ALL_SOURCES
    results = await run_crawl(sources, session)
    return {"results": results}
