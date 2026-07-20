# backend/src/agents/traffic_agent.py
from datetime import datetime, timezone

from src.agents.base import AgentState
from src.utils.logger import get_logger

logger = get_logger(__name__)


def traffic_agent(state: AgentState) -> dict:
    aqi = state.get("aqi_data", {})
    weather = state.get("weather_data", {})

    aqi_index = float(aqi.get("aqi_index") or 100)
    rain = float(weather.get("rain") or 0)
    has_real_data = (aqi.get("aqi_index") is not None and aqi.get("aqi_index") != 100) or (weather.get("rain") is not None and weather.get("rain") != 0)
    now = datetime.now(timezone.utc).isoformat()

    if aqi_index > 150 or rain > 10:
        analysis = "HIGH traffic congestion risk due to poor air quality or heavy rain."
        source = "OpenAQ" if aqi_index > 150 else "Open-Meteo"
        content = f"AQI {aqi_index:.0f} driving congestion risk" if aqi_index > 150 else f"Rain {rain:.1f}mm/h driving congestion risk"
    elif aqi_index > 100:
        analysis = "MODERATE traffic congestion expected. Air quality is degraded."
        source = "OpenAQ"
        content = f"AQI {aqi_index:.0f} (moderate)"
    else:
        analysis = "Traffic conditions are NORMAL. No significant disruptions expected."
        source = "OpenAQ"
        content = f"AQI {aqi_index:.0f} (normal)"

    evidence = [{
        "id": "ev-traffic-1",
        "agent": "traffic",
        "source": source,
        "type": "sensor",
        "content": content,
        "confidence": 0.9 if has_real_data else 0.5,
        "time": now,
    }]

    logger.info(f"Traffic analysis: {analysis}")
    return {"traffic_analysis": analysis, "traffic_evidence": evidence}
