from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from src.database.connection import get_db
from src.repositories.city_score_repo import CityScoreRepo
from src.repositories.district_repo import DistrictRepo
from src.services.city_score_service import CityScoreService
from src.schemas.city_score import CityScoreOut

router = APIRouter(prefix="/api/scores", tags=["scores"])


class ScoreHistoryPoint(BaseModel):
    time: str
    traffic_score: float
    environment_score: float
    citizen_score: float
    risk_score: float


@router.get("", response_model=list[CityScoreOut])
async def get_all_scores(session: AsyncSession = Depends(get_db)):
    districts = await DistrictRepo.get_all(session)
    latest_by_district = {
        s.district_id: s for s in await CityScoreRepo.get_city_overview(session)
    }
    scores = []
    for d in districts:
        score = latest_by_district.get(d.id)
        if score is None:
            score = await CityScoreService.calculate_and_save(session, d.id)
        scores.append(CityScoreOut.model_validate(score))
    return scores


@router.get("/history/{district_id}", response_model=list[ScoreHistoryPoint])
async def get_score_history(
    district_id: int, limit: int = Query(default=24, le=100), session: AsyncSession = Depends(get_db)
):
    rows = await CityScoreRepo.get_recent(session, district_id, limit)
    return [
        ScoreHistoryPoint(
            time=r.timestamp.strftime("%H:%M"),
            traffic_score=r.traffic_score,
            environment_score=r.environment_score,
            citizen_score=r.citizen_score,
            risk_score=r.risk_score,
        )
        for r in rows
    ]


@router.get("/{district_id}", response_model=CityScoreOut)
async def get_district_score(district_id: int, session: AsyncSession = Depends(get_db)):
    score = await CityScoreRepo.get_latest_by_district(session, district_id)
    if score is None:
        score = await CityScoreService.calculate_and_save(session, district_id)
    return CityScoreOut.model_validate(score)
