# backend/src/agents/base.py
from typing import TypedDict


class AgentState(TypedDict):
    query: str
    district_id: int
    city_id: str
    weather_data: dict
    aqi_data: dict
    event_data: list
    feedback_data: list
    traffic_analysis: str
    environment_analysis: str
    event_analysis: str
    citizen_analysis: str
    decision: dict
    explanation: list[str]
    confidence: float
