# backend/src/reasoning/thresholds.py
"""Shared, named thresholds for evidence/decision reasoning — the single
source of truth for values that must agree across the v1 pipeline
(src/agents/decision_agent.py, src/orchestrator/graph.py) and the v2 runtime
(src/runtime/workers.py).

Previously these lived as inline literals duplicated — and drifted — between
runtime/workers.py (rain > 50mm/h => "high") and agents/decision_agent.py
(rain > 20mm/h => "high"): the same physical quantity (rain mm/h) mapped to
"high" flood risk at two different thresholds depending on which runtime
handled the request, silently changing whether a decision triggered the
human-approval gate (requires_approval when flood_risk == "high").
"""

from src.reasoning.critic import CONFIDENCE_FLOOR

# Rain (mm/h) above which flood_risk is "high". 20mm/h is the value used by
# the v1 pipeline and is a standard meteorological "heavy rain" threshold —
# it's also reused directly by src/simulation/profiles.py's heavy_rain
# scenario's auto-goal trigger, corroborating it as the right value to unify
# on (rather than v2's old 50mm/h).
FLOOD_RISK_HIGH_RAIN_MM = 20.0

# Rain (mm/h) above which flood_risk is "moderate" (a.k.a. "medium"), below
# the HIGH threshold above.
FLOOD_RISK_MODERATE_RAIN_MM = 5.0

# Minimum decision confidence below which a decision requires human approval
# (src/orchestrator/graph.py human-in-the-loop gate). This is a distinct
# concept from CONFIDENCE_FLOOR (re-exported below): CONFIDENCE_FLOOR is the
# floor critic.review() clamps an evidence-penalized confidence to, not the
# point at which the pipeline routes a decision to a human for approval.
APPROVAL_CONFIDENCE_THRESHOLD = 75.0

# Re-exported so any module needing the confidence-floor value can import it
# alongside the other reasoning thresholds without reaching into critic.py
# directly. Do not redefine this elsewhere — critic.py is its source of truth.
__all__ = [
    "FLOOD_RISK_HIGH_RAIN_MM",
    "FLOOD_RISK_MODERATE_RAIN_MM",
    "APPROVAL_CONFIDENCE_THRESHOLD",
    "CONFIDENCE_FLOOR",
]
