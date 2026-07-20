# backend/src/agents/citizen_agent.py
from datetime import datetime, timezone

from src.agents.base import AgentState
from src.utils.logger import get_logger

logger = get_logger(__name__)


def citizen_agent(state: AgentState) -> dict:
    feedback = state.get("feedback_data", [])
    if not feedback:
        analysis = "No citizen feedback available for this district."
        return {"citizen_analysis": analysis, "citizen_evidence": []}

    negative = [f for f in feedback if f.get("sentiment") == "negative"]
    ratio = len(negative) / len(feedback) if feedback else 0

    if ratio > 0.7:
        analysis = f"HIGH citizen dissatisfaction ({ratio*100:.0f}% negative). Main concerns: {', '.join(set(f.get('category','') for f in negative[:3]))}"
    elif ratio > 0.4:
        analysis = f"MODERATE citizen concerns ({ratio*100:.0f}% negative feedback)."
    else:
        analysis = f"Citizen sentiment is POSITIVE ({(1-ratio)*100:.0f}% positive feedback)."

    evidence = [{
        "id": "ev-citizen-1",
        "agent": "citizen",
        "source": "CityOS Feedback DB",
        "type": "feedback",
        "content": f"{len(feedback)} reports, {ratio*100:.0f}% negative",
        "confidence": 0.8,
        "time": datetime.now(timezone.utc).isoformat(),
    }]

    logger.info(f"Citizen analysis: {analysis}")
    return {"citizen_analysis": analysis, "citizen_evidence": evidence}
