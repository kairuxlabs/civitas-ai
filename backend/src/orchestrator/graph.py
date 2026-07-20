import asyncio
from datetime import datetime, timezone

from sqlalchemy.ext.asyncio import AsyncSession

from src.agents.base import AgentState
from src.agents.traffic_agent import traffic_agent
from src.agents.environment_agent import environment_agent
from src.agents.event_agent import event_agent
from src.agents.citizen_agent import citizen_agent
from src.agents.knowledge_agent import knowledge_agent
from src.agents.decision_agent import decision_agent
from src.agents.critic_agent import critic_agent
from src.agents.explanation_agent import explanation_agent
from src.models.decision import AgentDecision
from src.repositories.weather_repo import WeatherRepo
from src.repositories.aqi_repo import AQIRepo
from src.repositories.event_repo import EventRepo
from src.repositories.feedback_repo import FeedbackRepo
from src.schemas.decision import DecisionOut
from src.ws.manager import manager

PIPELINE = [
    ("traffic_node",      "Traffic Agent",      traffic_agent),
    ("environment_node",  "Environment Agent",  environment_agent),
    ("event_node",        "Event Agent",         event_agent),
    ("citizen_node",      "Citizen Agent",       citizen_agent),
    ("knowledge_node",    "Knowledge Agent",     knowledge_agent),
    ("decision_node",     "Decision Agent",      decision_agent),
    ("critic_node",       "Critic Agent",        critic_agent),
    ("explanation_node",  "Explanation Agent",   explanation_agent),
]


async def _broadcast(event_type: str, agent: str, status: str, detail: str = ""):
    await manager.broadcast({
        "type": event_type,
        "agent": agent,
        "status": status,
        "detail": detail,
        "ts": datetime.now(timezone.utc).isoformat(),
    })


async def run_agent_graph(
    query: str,
    district_id: int,
    session: AsyncSession,
    event_data: list | None = None,
    feedback_data: list | None = None,
) -> DecisionOut:
    # Kept sequential on purpose: these 4 reads share one AsyncSession, and
    # asyncio.gather()-ing multiple queries on a single asyncpg connection
    # corrupts the connection state in production. Each query is already
    # indexed and narrow (single district_id), so the latency cost is minimal.
    weather = await WeatherRepo.get_latest(session, district_id)
    aqi = await AQIRepo.get_latest(session, district_id)
    db_events = await EventRepo.get_current(session, district_id)
    db_feedback = await FeedbackRepo.get_recent(session, district_id)

    weather_data = {
        "temperature": float(weather.temperature or 30) if weather else 30,
        "humidity": float(weather.humidity or 70) if weather else 70,
        "rain": float(weather.rain or 0) if weather else 0,
        "wind_speed": float(weather.wind_speed or 10) if weather else 10,
    }
    aqi_data = {
        "pm25": float(aqi.pm25 or 50) if aqi else 50,
        "pm10": float(aqi.pm10 or 80) if aqi else 80,
        "co": float(aqi.co or 1.0) if aqi else 1.0,
        "no2": float(aqi.no2 or 40) if aqi else 40,
        "aqi_index": float(aqi.aqi_index or 100) if aqi else 100,
    }

    if event_data:
        for ev in event_data:
            if "rain_multiplier" in ev:
                weather_data["rain"] = weather_data["rain"] * ev["rain_multiplier"]
            if "aqi_boost" in ev:
                aqi_data["aqi_index"] = min(300, aqi_data["aqi_index"] + ev["aqi_boost"])
                aqi_data["pm25"] = min(300, aqi_data["pm25"] + ev["aqi_boost"] * 0.5)

    # Merge DB events with any scenario-injected events; prefer passed event_data if provided
    resolved_events = event_data if event_data is not None else [
        {"title": e.title, "category": e.category, "impact_level": e.impact_level}
        for e in db_events
    ]
    resolved_feedback = feedback_data if feedback_data is not None else [
        {"category": f.category, "sentiment": f.sentiment, "content": f.content}
        for f in db_feedback
    ]

    state: AgentState = {
        "query": query,
        "district_id": district_id,
        "city_id": "hanoi",
        "weather_data": weather_data,
        "aqi_data": aqi_data,
        "event_data": resolved_events,
        "feedback_data": resolved_feedback,
        "traffic_analysis": "",
        "environment_analysis": "",
        "event_analysis": "",
        "citizen_analysis": "",
        "knowledge_summary": "",
        "decision": {},
        "explanation": [],
        "confidence": 0.0,
    }

    await _broadcast("pipeline_start", "Supervisor", "planning", f"Processing query for district {district_id}")
    await asyncio.sleep(0.05)

    for node_id, agent_name, agent_fn in PIPELINE:
        await _broadcast("agent_update", agent_name, "running", "")
        result = await asyncio.to_thread(agent_fn, state)
        state = {**state, **result}
        await _broadcast("agent_update", agent_name, "done", "")
        await asyncio.sleep(0.05)

    dec = state["decision"]
    confidence = dec.get("confidence", 70.0)
    requires_approval = confidence < 75 or dec.get("prediction", {}).get("flood_risk") == "high"

    out = DecisionOut(
        prediction=dec.get("prediction", {}),
        impact=dec.get("impact", {}),
        recommendations=dec.get("recommendations", []),
        confidence=confidence,
        explanation=state.get("explanation", []),
        evidence=state.get("evidence", []),
    )

    await _broadcast("pipeline_done", "Supervisor", "done", f"Confidence: {confidence:.0f}%")

    decision_record = AgentDecision(
        city_id="hanoi",
        district_id=district_id,
        query=query,
        prediction=out.prediction,
        impact=out.impact,
        recommendations=out.recommendations,
        confidence=out.confidence,
        explanation=out.explanation,
        evidence=out.evidence,
        requires_approval=requires_approval,
        approved=None,
        created_at=datetime.now(timezone.utc),
    )
    session.add(decision_record)
    await session.commit()
    await session.refresh(decision_record)

    # Broadcast approval needed if required
    if requires_approval:
        await _broadcast("approval_needed", "Supervisor", "waiting",
                         f"Decision ID {decision_record.id} requires human approval")

    return out
