# backend/src/runtime/workers.py
"""Workers: one async worker per specialized agent (spec_v2 §7, §13).

A worker receives the run, reads/writes the shared run.context (same keys
as the v1 AgentState) and returns a small result dict that always contains
"summary" and "confidence" (0..1) so Reflection can review it.
"""
import asyncio
from typing import Awaitable, Callable

from src.agents.citizen_agent import citizen_agent
from src.agents.environment_agent import environment_agent
from src.agents.knowledge_agent import knowledge_agent
from src.agents.traffic_agent import traffic_agent
from src.runtime.state import RunState, TaskSpec

Worker = Callable[[RunState, TaskSpec], Awaitable[dict]]


def _weather(run: RunState) -> dict:
    return run.context.get("weather_data", {}) or {}


def _aqi(run: RunState) -> dict:
    return run.context.get("aqi_data", {}) or {}


async def _run_v1_agent(agent_fn, run: RunState, output_key: str) -> str:
    """Run a sync v1 agent in a thread and merge its output into run.context."""
    result = await asyncio.to_thread(agent_fn, dict(run.context))
    run.context.update(result)
    return str(result.get(output_key, ""))


async def weather_worker(run: RunState, spec: TaskSpec) -> dict:
    rain = float(_weather(run).get("rain") or 0)
    flood_risk = "high" if rain > 50 else "medium" if rain > 20 else "low"
    run.context["flood_risk"] = flood_risk
    has_data = bool(run.context.get("weather_data"))
    summary = f"Rain {rain:.1f}mm/h — flood risk {flood_risk}"
    run.context["weather_analysis"] = summary
    return {
        "summary": summary,
        "flood_risk": flood_risk,
        "rain_level": rain,
        "confidence": 0.9 if has_data else 0.5,
    }


async def traffic_worker(run: RunState, spec: TaskSpec) -> dict:
    analysis = await _run_v1_agent(traffic_agent, run, "traffic_analysis")
    return {
        "summary": analysis or "No traffic signal",
        "confidence": 0.85 if analysis else 0.4,
        "evidence": run.context.get("traffic_evidence", []),
    }


async def environment_worker(run: RunState, spec: TaskSpec) -> dict:
    analysis = await _run_v1_agent(environment_agent, run, "environment_analysis")
    return {
        "summary": analysis or "No environment signal",
        "aqi_index": float(_aqi(run).get("aqi_index") or 0),
        "confidence": 0.85 if analysis else 0.4,
        "evidence": run.context.get("environment_evidence", []),
    }


async def citizen_worker(run: RunState, spec: TaskSpec) -> dict:
    analysis = await _run_v1_agent(citizen_agent, run, "citizen_analysis")
    return {
        "summary": analysis or "No citizen reports",
        "confidence": 0.8 if analysis else 0.4,
        "evidence": run.context.get("citizen_evidence", []),
    }


async def knowledge_worker(run: RunState, spec: TaskSpec) -> dict:
    if spec.params.get("deep"):
        # Reflection asked for a deeper pass: widen the query with sensor context
        run.context["query"] = (
            f"{run.context.get('query', run.goal)} "
            f"rain {(_weather(run).get('rain') or 0)}mm aqi {(_aqi(run).get('aqi_index') or 0)}"
        )
    summary = await _run_v1_agent(knowledge_agent, run, "knowledge_summary")
    return {
        "summary": summary or "No relevant SOP found",
        "confidence": 0.9 if summary else 0.3,
        "evidence": run.context.get("knowledge_evidence", []),
    }


async def forecast_worker(run: RunState, spec: TaskSpec) -> dict:
    rain = float(_weather(run).get("rain") or 0)
    aqi = float(_aqi(run).get("aqi_index") or 0)
    projected_rain = round(rain * 1.2, 1)
    projected_aqi = round(min(300.0, aqi * (1.1 if rain < 5 else 0.9)), 1)
    trend = "worsening" if projected_rain > rain and rain > 20 else "stable"
    summary = f"Next 6h: rain ~{projected_rain}mm/h, AQI ~{projected_aqi} ({trend})"
    run.context["forecast"] = {"rain_6h": projected_rain, "aqi_6h": projected_aqi, "trend": trend}
    return {"summary": summary, "rain_6h": projected_rain, "aqi_6h": projected_aqi, "confidence": 0.7}


async def emergency_worker(run: RunState, spec: TaskSpec) -> dict:
    flood_risk = run.context.get("flood_risk", "low")
    aqi = float(_aqi(run).get("aqi_index") or 0)
    units: list[str] = []
    if flood_risk == "high":
        units += ["Đội bơm thoát nước", "CSGT phân luồng điểm ngập", "Đội cứu hộ cứu nạn"]
    elif flood_risk == "medium":
        units += ["Đội giám sát mực nước", "CSGT ứng trực"]
    if aqi > 200:
        units.append("Đội y tế lưu động (ô nhiễm không khí)")
    readiness = "deploy" if flood_risk == "high" or aqi > 200 else "standby" if units else "normal"
    summary = f"Readiness: {readiness}" + (f" — {len(units)} units" if units else "")
    run.context["emergency"] = {"readiness": readiness, "units": units}
    return {"summary": summary, "readiness": readiness, "units": units, "confidence": 0.85}


async def analytics_worker(run: RunState, spec: TaskSpec) -> dict:
    rain = float(_weather(run).get("rain") or 0)
    aqi = float(_aqi(run).get("aqi_index") or 0)
    flood_risk = run.context.get("flood_risk", "low")
    risk_score = min(100.0, rain * 1.2 + aqi / 4)
    summary = f"Risk score {risk_score:.0f}/100 — flood {flood_risk}, AQI {aqi:.0f}"
    run.context["analytics"] = {"risk_score": risk_score}
    return {
        "summary": summary,
        "risk_score": risk_score,
        "flood_risk": flood_risk,
        "aqi_index": aqi,
        "confidence": 0.9,
    }


WORKERS: dict[str, Worker] = {
    "weather": weather_worker,
    "traffic": traffic_worker,
    "environment": environment_worker,
    "citizen": citizen_worker,
    "knowledge": knowledge_worker,
    "forecast": forecast_worker,
    "emergency": emergency_worker,
    "analytics": analytics_worker,
}
