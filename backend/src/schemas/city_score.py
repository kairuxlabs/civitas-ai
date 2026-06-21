from datetime import datetime
from pydantic import BaseModel


class CityScoreOut(BaseModel):
    id: int
    city_id: str
    district_id: int | None
    timestamp: datetime
    traffic_score: float
    environment_score: float
    citizen_score: float
    risk_score: float
    overall_score: float

    model_config = {"from_attributes": True}
