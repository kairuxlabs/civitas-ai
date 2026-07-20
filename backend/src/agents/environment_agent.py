# backend/src/agents/environment_agent.py
from datetime import datetime, timezone

from src.agents.base import AgentState
from src.utils.logger import get_logger

logger = get_logger(__name__)


def environment_agent(state: AgentState) -> dict:
    aqi = state.get("aqi_data", {})
    pm25 = float(aqi.get("pm25") or 50)
    pm10 = float(aqi.get("pm10") or 80)
    aqi_index = float(aqi.get("aqi_index") or 100)

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

    evidence = [{
        "id": "ev-environment-1",
        "agent": "environment",
        "source": "OpenAQ",
        "type": "sensor",
        "content": f"AQI {aqi_index:.0f} ({level}), PM2.5={pm25:.1f}μg/m³, PM10={pm10:.1f}μg/m³",
        "confidence": 0.9,
        "time": datetime.now(timezone.utc).isoformat(),
    }]

    logger.info(f"Environment analysis: {analysis}")
    return {"environment_analysis": analysis, "environment_evidence": evidence}
