# backend/src/api/routes/runtime.py
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from src.runtime import monitor
from src.runtime.engine import engine
from src.runtime.state import run_store

router = APIRouter(prefix="/api/v2", tags=["runtime"])


class GoalIn(BaseModel):
    goal: str = Field(min_length=3, max_length=500)
    district_id: int = 1
    context_overrides: dict | None = None


class ApprovalIn(BaseModel):
    approved: bool


@router.post("/goal", status_code=202)
async def submit_goal(body: GoalIn):
    run = await engine.submit_goal(
        goal=body.goal,
        district_id=body.district_id,
        context_overrides=body.context_overrides,
    )
    return run.to_dict()


@router.get("/runs")
async def list_runs():
    return {"runs": [r.summary_dict() for r in run_store.list_recent()]}


@router.get("/runs/{run_id}")
async def get_run(run_id: str):
    run = run_store.get(run_id)
    if run is None:
        raise HTTPException(status_code=404, detail="Run not found")
    return run.to_dict()


@router.post("/runs/{run_id}/approval")
async def resolve_run(run_id: str, body: ApprovalIn):
    run = await engine.resolve(run_id, approved=body.approved)
    if run is None:
        raise HTTPException(status_code=404, detail="Run not found")
    return run.to_dict()


@router.get("/monitor")
async def runtime_monitor():
    return monitor.snapshot()
