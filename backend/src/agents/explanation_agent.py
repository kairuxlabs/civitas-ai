# backend/src/agents/explanation_agent.py
from src.agents.base import AgentState
from src.utils.logger import get_logger

logger = get_logger(__name__)


def explanation_agent(state: AgentState) -> dict:
    explanation = [
        f"Traffic Analysis: {state.get('traffic_analysis', 'N/A')}",
        f"Environment Analysis: {state.get('environment_analysis', 'N/A')}",
        f"Event Analysis: {state.get('event_analysis', 'N/A')}",
        f"Citizen Sentiment: {state.get('citizen_analysis', 'N/A')}",
        f"Confidence: {state.get('confidence', 0):.0f}% based on 4 data streams",
    ]
    logger.info(f"Explanation generated with {len(explanation)} items")
    return {"explanation": explanation}
