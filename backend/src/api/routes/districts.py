from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from src.database.connection import get_db
from src.repositories.district_repo import DistrictRepo
from src.schemas.district import DistrictOut

router = APIRouter(prefix="/api/districts", tags=["districts"])


@router.get("", response_model=list[DistrictOut])
async def get_districts(session: AsyncSession = Depends(get_db)):
    districts = await DistrictRepo.get_all(session)
    return [DistrictOut.model_validate(d) for d in districts]
