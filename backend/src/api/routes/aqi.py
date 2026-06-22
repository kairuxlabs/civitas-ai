from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from src.database.connection import get_db
from src.repositories.aqi_repo import AQIRepo

router = APIRouter(prefix="/api/aqi", tags=["aqi"])


class AQIPoint(BaseModel):
    time: str
    aqi_index: int
    pm25: float


@router.get("/history/{district_id}", response_model=list[AQIPoint])
async def get_aqi_history(district_id: int, limit: int = 24, session: AsyncSession = Depends(get_db)):
    rows = await AQIRepo.get_recent(session, district_id, limit)
    return [
        AQIPoint(
            time=r.timestamp.strftime("%H:%M"),
            aqi_index=r.aqi_index or 0,
            pm25=round(r.pm25 or 0, 1),
        )
        for r in rows
    ]
