from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from src.database.connection import get_db
from src.orchestrator.graph import run_agent_graph
from src.schemas.decision import DecisionOut

router = APIRouter(prefix="/api/simulate", tags=["simulator"])

SCENARIOS = {
    "heavy_rain": {"rain_multiplier": 10.0, "aqi_boost": 20},
    "air_pollution": {"rain_multiplier": 1.0, "aqi_boost": 80},
    "major_event": {"rain_multiplier": 1.0, "aqi_boost": 30},
    "heatwave": {"rain_multiplier": 0.0, "aqi_boost": 50},
}


class SimulateRequest(BaseModel):
    scenario: str
    district_id: int


@router.post("", response_model=DecisionOut)
async def simulate(request: SimulateRequest, session: AsyncSession = Depends(get_db)):
    scenario_params = SCENARIOS.get(request.scenario, {})
    query = f"Simulate scenario: {request.scenario}"

    sim_event = [
        {
            "title": f"Simulated: {request.scenario}",
            "impact_level": "high",
            "category": "simulation",
        }
    ]

    return await run_agent_graph(
        query=query,
        district_id=request.district_id,
        session=session,
        event_data=sim_event,
    )
