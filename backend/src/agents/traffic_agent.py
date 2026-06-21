# backend/src/agents/traffic_agent.py
from src.agents.base import AgentState
from src.utils.logger import get_logger

logger = get_logger(__name__)


def traffic_agent(state: AgentState) -> dict:
    aqi = state.get("aqi_data", {})
    weather = state.get("weather_data", {})

    aqi_index = aqi.get("aqi_index", 100)
    rain = weather.get("rain", 0)

    if aqi_index > 150 or rain > 10:
        analysis = "HIGH traffic congestion risk due to poor air quality or heavy rain."
    elif aqi_index > 100:
        analysis = "MODERATE traffic congestion expected. Air quality is degraded."
    else:
        analysis = "Traffic conditions are NORMAL. No significant disruptions expected."

    logger.info(f"Traffic analysis: {analysis}")
    return {"traffic_analysis": analysis}
