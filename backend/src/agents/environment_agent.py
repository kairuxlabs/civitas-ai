# backend/src/agents/environment_agent.py
from src.agents.base import AgentState
from src.utils.logger import get_logger

logger = get_logger(__name__)


def environment_agent(state: AgentState) -> dict:
    aqi = state.get("aqi_data", {})
    pm25 = aqi.get("pm25", 50)
    pm10 = aqi.get("pm10", 80)
    aqi_index = aqi.get("aqi_index", 100)

    if aqi_index > 150:
        level = "HAZARDOUS"
        advice = "Avoid outdoor activities. Wear N95 masks."
    elif aqi_index > 100:
        level = "UNHEALTHY for sensitive groups"
        advice = "Sensitive groups should limit outdoor exposure."
    else:
        level = "MODERATE"
        advice = "Air quality is acceptable for most people."

    analysis = f"AQI {aqi_index} ({level}). PM2.5={pm25:.1f}μg/m³, PM10={pm10:.1f}μg/m³. {advice}"
    logger.info(f"Environment analysis: {analysis}")
    return {"environment_analysis": analysis}
