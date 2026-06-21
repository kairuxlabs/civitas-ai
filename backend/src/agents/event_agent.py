# backend/src/agents/event_agent.py
from src.agents.base import AgentState
from src.utils.logger import get_logger

logger = get_logger(__name__)


def event_agent(state: AgentState) -> dict:
    events = state.get("event_data", [])
    if not events:
        analysis = "No significant events scheduled in this district."
    else:
        high_impact = [e for e in events if e.get("impact_level") == "high"]
        if high_impact:
            analysis = f"{len(high_impact)} HIGH-impact event(s) may cause disruptions: {', '.join(e['title'] for e in high_impact[:3])}"
        else:
            analysis = f"{len(events)} event(s) scheduled. Low to moderate impact expected."

    logger.info(f"Event analysis: {analysis}")
    return {"event_analysis": analysis}
