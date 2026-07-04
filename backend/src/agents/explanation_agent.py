from src.agents.base import AgentState
from src.utils.logger import get_logger

logger = get_logger(__name__)


def explanation_agent(state: AgentState) -> dict:
    confidence = state.get("confidence", 0)
    knowledge = state.get("knowledge_summary", "")
    explanation = [
        f"Traffic Analysis: {state.get('traffic_analysis', 'N/A')}",
        f"Environment Analysis: {state.get('environment_analysis', 'N/A')}",
        f"Event Analysis: {state.get('event_analysis', 'N/A')}",
        f"Citizen Sentiment: {state.get('citizen_analysis', 'N/A')}",
    ]
    if knowledge and "No specific SOP" not in knowledge:
        explanation.append(f"Knowledge Base: {knowledge[:200]}")
    explanation.append(f"Confidence: {confidence:.0f}% based on 5 data streams")
    logger.info(f"Explanation generated with {len(explanation)} items")
    return {"explanation": explanation}
