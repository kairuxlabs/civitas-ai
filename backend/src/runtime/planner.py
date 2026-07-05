# backend/src/runtime/planner.py
"""Planner: turns a natural-language goal into a task DAG.

The planner never calls tools itself — it only decides which specialized
agents are needed and in what dependency order (spec_v2 §4).
"""
import asyncio

from src.agents.gemini_client import call_gemini, parse_json_safe
from src.runtime.state import TaskSpec
from src.utils.logger import get_logger

logger = get_logger(__name__)

AGENT_CATALOG: set[str] = {
    "weather", "traffic", "environment", "citizen",
    "knowledge", "forecast", "emergency", "analytics",
}

_EMERGENCY_KEYWORDS = ("rain", "flood", "storm", "fire", "accident", "mưa", "ngập", "bão", "cháy", "tai nạn")
_ENVIRONMENT_KEYWORDS = ("air", "aqi", "pollution", "smog", "ô nhiễm", "khói", "bụi")
_FORECAST_KEYWORDS = ("tonight", "tomorrow", "forecast", "predict", "dự báo", "tối nay", "ngày mai")

_PLANNER_PROMPT = """You are the Planner of CityOS, an autonomous city-management runtime.
Break the following goal into agent tasks. Available agents: {catalog}.
Rules: output ONLY JSON of shape {{"tasks": [{{"id": str, "agent": str, "depends_on": [str]}}]}}.
Task ids must be unique; depends_on must reference other task ids; keep 3-7 tasks.

Goal: {goal}
"""


def rule_based_plan(goal: str) -> list[TaskSpec]:
    """Deterministic fallback plan derived from goal keywords."""
    g = goal.lower()
    specs: list[TaskSpec] = [
        TaskSpec(id="weather", agent="weather", priority=1),
        TaskSpec(id="knowledge", agent="knowledge", priority=1),
        TaskSpec(id="citizen", agent="citizen", priority=2),
        TaskSpec(id="traffic", agent="traffic", depends_on=["weather"], priority=2),
    ]
    if any(kw in g for kw in _ENVIRONMENT_KEYWORDS):
        specs.append(TaskSpec(id="environment", agent="environment", priority=2))
    if any(kw in g for kw in _EMERGENCY_KEYWORDS):
        specs.append(TaskSpec(id="emergency", agent="emergency", depends_on=["weather"], priority=1))
    if any(kw in g for kw in _FORECAST_KEYWORDS):
        specs.append(TaskSpec(id="forecast", agent="forecast", depends_on=["weather"], priority=2))
    specs.append(TaskSpec(
        id="analytics", agent="analytics",
        depends_on=[s.id for s in specs], priority=3,
    ))
    return specs


def _has_cycle(tasks: dict[str, list[str]]) -> bool:
    visiting: set[str] = set()
    visited: set[str] = set()

    def visit(node: str) -> bool:
        if node in visited:
            return False
        if node in visiting:
            return True
        visiting.add(node)
        for dep in tasks.get(node, []):
            if visit(dep):
                return True
        visiting.discard(node)
        visited.add(node)
        return False

    return any(visit(n) for n in tasks)


def _validate_plan(raw: dict) -> list[TaskSpec] | None:
    tasks = raw.get("tasks")
    if not isinstance(tasks, list) or not tasks:
        return None
    ids = [t.get("id") for t in tasks if isinstance(t, dict)]
    if len(ids) != len(tasks) or len(set(ids)) != len(ids) or not all(isinstance(i, str) and i for i in ids):
        return None
    id_set = set(ids)
    specs: list[TaskSpec] = []
    dep_map: dict[str, list[str]] = {}
    for t in tasks:
        agent = t.get("agent")
        deps = t.get("depends_on") or []
        if agent not in AGENT_CATALOG:
            return None
        if not isinstance(deps, list) or any(d not in id_set or d == t["id"] for d in deps):
            return None
        dep_map[t["id"]] = deps
        specs.append(TaskSpec(id=t["id"], agent=agent, depends_on=list(deps)))
    if _has_cycle(dep_map):
        return None
    return specs


async def create_plan(goal: str) -> list[TaskSpec]:
    """LLM plan with strict validation; falls back to rule-based on any failure."""
    prompt = _PLANNER_PROMPT.format(catalog=", ".join(sorted(AGENT_CATALOG)), goal=goal)
    text = await asyncio.to_thread(call_gemini, prompt, True)
    if text:
        raw = parse_json_safe(text)
        if raw:
            specs = _validate_plan(raw)
            if specs:
                logger.info(f"Planner: Gemini plan with {len(specs)} tasks")
                return specs
        logger.warning("Planner: Gemini plan invalid, falling back to rules")
    return rule_based_plan(goal)
