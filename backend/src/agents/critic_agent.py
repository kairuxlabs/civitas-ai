# backend/src/agents/critic_agent.py
from src.agents.base import AgentState
from src.reasoning import critic
from src.utils.logger import get_logger

logger = get_logger(__name__)


def critic_agent(state: AgentState) -> dict:
    decision = dict(state.get("decision", {}))
    evidence = state.get("evidence", [])

    result = critic.review(decision, evidence)
    decision["confidence"] = result["confidence"]

    logger.info(f"Critic: {len(evidence)} evidence, {len(result['critic_notes'])} note(s), confidence={result['confidence']:.0f}%")
    return {"decision": decision, "confidence": result["confidence"], "critic_notes": result["critic_notes"]}
