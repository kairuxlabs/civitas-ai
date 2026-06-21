from datetime import datetime
from pydantic import BaseModel


class DecisionOut(BaseModel):
    prediction: dict
    impact: dict
    recommendations: list[str]
    confidence: float
    explanation: list[str]


class AgentDecisionOut(BaseModel):
    id: int
    city_id: str
    district_id: int | None
    query: str | None
    prediction: dict | None
    impact: dict | None
    recommendations: list | None
    confidence: float | None
    explanation: list | None
    created_at: datetime | None

    model_config = {"from_attributes": True}
