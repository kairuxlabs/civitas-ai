# backend/src/reasoning/critic.py
"""Rule-based, deterministic decision critic — no LLM call, shared by the
v1 pipeline (src/agents/critic_agent.py) and v2 runtime (src/runtime/decision.py).
"""

_PENALTY_PER_NOTE = 15
_CONFIDENCE_FLOOR = 30
_SUFFICIENCY_THRESHOLD = 2


def review(decision: dict, evidence: list[dict]) -> dict:
    notes: list[str] = []

    if len(evidence) < _SUFFICIENCY_THRESHOLD:
        notes.append(f"Insufficient evidence: only {len(evidence)} item(s) support this decision.")

    evidence_types = {e.get("type") for e in evidence}
    evidence_sources = {e.get("source") for e in evidence}
    if "gap" in evidence_types:
        notes.append("Knowledge gap: retrieval found no supporting SOP, city knowledge, or graph facts for this query.")
    prediction = decision.get("prediction", {}) or {}
    if not isinstance(prediction, dict):
        # v2 runtime decisions carry "prediction" as a free-text string, not a
        # structured dict like v1's AgentState — nothing to structurally check.
        prediction = {}

    if prediction.get("flood_risk") == "high" and "Open-Meteo" not in evidence_sources:
        notes.append("Prediction flood_risk=high is not backed by any Open-Meteo (weather) evidence.")

    if prediction.get("traffic_disruption") == "likely" and not (evidence_types & {"sensor", "event"}):
        notes.append("Prediction traffic_disruption=likely is not backed by any sensor or event evidence.")

    original_confidence = float(decision.get("confidence", 70))
    penalty = _PENALTY_PER_NOTE * len(notes)
    adjusted_confidence = max(_CONFIDENCE_FLOOR, original_confidence - penalty) if notes else original_confidence

    return {"confidence": adjusted_confidence, "critic_notes": notes}
