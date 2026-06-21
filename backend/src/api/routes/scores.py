from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from src.database.connection import get_db
from src.repositories.city_score_repo import CityScoreRepo
from src.repositories.district_repo import DistrictRepo
from src.services.city_score_service import CityScoreService
from src.schemas.city_score import CityScoreOut

router = APIRouter(prefix="/api/scores", tags=["scores"])


@router.get("", response_model=list[CityScoreOut])
async def get_all_scores(session: AsyncSession = Depends(get_db)):
    districts = await DistrictRepo.get_all(session)
    scores = []
    for d in districts:
        score = await CityScoreRepo.get_latest_by_district(session, d.id)
        if score is None:
            score = await CityScoreService.calculate_and_save(session, d.id)
        scores.append(CityScoreOut.model_validate(score))
    return scores


@router.get("/{district_id}", response_model=CityScoreOut)
async def get_district_score(district_id: int, session: AsyncSession = Depends(get_db)):
    score = await CityScoreRepo.get_latest_by_district(session, district_id)
    if score is None:
        score = await CityScoreService.calculate_and_save(session, district_id)
    return CityScoreOut.model_validate(score)
