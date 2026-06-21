# backend/src/agents/decision_agent.py
from src.agents.base import AgentState
from src.utils.logger import get_logger

logger = get_logger(__name__)


def decision_agent(state: AgentState) -> dict:
    aqi = state.get("aqi_data", {})
    weather = state.get("weather_data", {})
    aqi_index = aqi.get("aqi_index", 100)
    rain = weather.get("rain", 0)

    recommendations = []
    risk_factors = 0

    if aqi_index > 150:
        recommendations.append("Issue air quality health advisory")
        recommendations.append("Restrict outdoor construction activities")
        risk_factors += 2
    elif aqi_index > 100:
        recommendations.append("Increase public transport frequency to reduce vehicle emissions")
        risk_factors += 1

    if rain > 20:
        recommendations.append("Activate flood drainage systems")
        recommendations.append("Deploy traffic management at flood-prone intersections")
        risk_factors += 2
    elif rain > 5:
        recommendations.append("Monitor drainage capacity")
        risk_factors += 1

    citizen_analysis = state.get("citizen_analysis", "")
    if "HIGH citizen dissatisfaction" in citizen_analysis:
        recommendations.append("Schedule emergency community meeting")
        risk_factors += 1

    if not recommendations:
        recommendations.append("Maintain current operations — conditions are stable")

    confidence = max(60, 95 - (risk_factors * 5))

    prediction = {
        "next_6h_aqi_trend": "increasing" if aqi_index > 100 else "stable",
        "flood_risk": "high" if rain > 20 else "low",
        "traffic_disruption": "likely" if aqi_index > 150 or rain > 10 else "unlikely",
    }

    impact = {
        "population_affected": f"{risk_factors * 50000:,} residents",
        "economic_impact": "high" if risk_factors >= 3 else "moderate" if risk_factors >= 1 else "low",
        "health_risk": "high" if aqi_index > 150 else "moderate" if aqi_index > 100 else "low",
    }

    decision = {
        "prediction": prediction,
        "impact": impact,
        "recommendations": recommendations,
        "confidence": confidence,
    }

    logger.info(f"Decision agent confidence: {confidence}")
    return {"decision": decision, "confidence": confidence}
