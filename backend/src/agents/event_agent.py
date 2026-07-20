# backend/src/agents/event_agent.py
from datetime import datetime, timezone

from src.agents.base import AgentState
from src.utils.logger import get_logger

logger = get_logger(__name__)


def event_agent(state: AgentState) -> dict:
    events = state.get("event_data", [])
    now = datetime.now(timezone.utc).isoformat()

    if not events:
        analysis = "No significant events scheduled in this district."
        evidence = []
    else:
        high_impact = [e for e in events if e.get("impact_level") == "high"]
        if high_impact:
            analysis = f"{len(high_impact)} HIGH-impact event(s) may cause disruptions: {', '.join(e['title'] for e in high_impact[:3])}"
        else:
            analysis = f"{len(events)} event(s) scheduled. Low to moderate impact expected."

        evidence = [
            {
                "id": f"ev-event-{i + 1}",
                "agent": "event",
                "source": "CityOS Events DB",
                "type": "event",
                "content": f"{e['title']} ({e.get('category', 'unknown')}, impact={e.get('impact_level', 'unknown')})",
                "confidence": 0.85,
                "time": now,
            }
            for i, e in enumerate(high_impact[:3])
        ]

    logger.info(f"Event analysis: {analysis}")
    return {"event_analysis": analysis, "event_evidence": evidence}
