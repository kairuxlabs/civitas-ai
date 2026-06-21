from datetime import datetime
from pydantic import BaseModel, Field


class DecisionOut(BaseModel):
    prediction: dict
    impact: dict
    recommendations: list[str]
    confidence: float = Field(..., ge=0, le=100)
    explanation: list[str] = Field(..., min_length=5, max_length=5)


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
