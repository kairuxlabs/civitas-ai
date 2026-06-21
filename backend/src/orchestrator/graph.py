# backend/src/orchestrator/graph.py
from langgraph.graph import StateGraph, END
from sqlalchemy.ext.asyncio import AsyncSession

from src.agents.base import AgentState
from src.agents.traffic_agent import traffic_agent
from src.agents.environment_agent import environment_agent
from src.agents.event_agent import event_agent
from src.agents.citizen_agent import citizen_agent
from src.agents.decision_agent import decision_agent
from src.agents.explanation_agent import explanation_agent
from src.repositories.weather_repo import WeatherRepo
from src.repositories.aqi_repo import AQIRepo
from src.schemas.decision import DecisionOut


def build_graph():
    graph = StateGraph(AgentState)

    graph.add_node("traffic", traffic_agent)
    graph.add_node("environment", environment_agent)
    graph.add_node("event", event_agent)
    graph.add_node("citizen", citizen_agent)
    graph.add_node("decision", decision_agent)
    graph.add_node("explanation", explanation_agent)

    graph.set_entry_point("traffic")
    graph.add_edge("traffic", "environment")
    graph.add_edge("environment", "event")
    graph.add_edge("event", "citizen")
    graph.add_edge("citizen", "decision")
    graph.add_edge("decision", "explanation")
    graph.add_edge("explanation", END)

    return graph.compile()


compiled_graph = build_graph()


async def run_agent_graph(
    query: str,
    district_id: int,
    session: AsyncSession,
    event_data: list | None = None,
    feedback_data: list | None = None,
) -> DecisionOut:
    weather = await WeatherRepo.get_latest(session, district_id)
    aqi = await AQIRepo.get_latest(session, district_id)

    initial_state: AgentState = {
        "query": query,
        "district_id": district_id,
        "city_id": "hanoi",
        "weather_data": {
            "temperature": weather.temperature if weather else 30,
            "humidity": weather.humidity if weather else 70,
            "rain": weather.rain if weather else 0,
            "wind_speed": weather.wind_speed if weather else 10,
        },
        "aqi_data": {
            "pm25": aqi.pm25 if aqi else 50,
            "pm10": aqi.pm10 if aqi else 80,
            "co": aqi.co if aqi else 1.0,
            "no2": aqi.no2 if aqi else 40,
            "aqi_index": aqi.aqi_index if aqi else 100,
        },
        "event_data": event_data or [],
        "feedback_data": feedback_data or [],
        "traffic_analysis": "",
        "environment_analysis": "",
        "event_analysis": "",
        "citizen_analysis": "",
        "decision": {},
        "explanation": [],
        "confidence": 0.0,
    }

    result = compiled_graph.invoke(initial_state)
    dec = result["decision"]

    return DecisionOut(
        prediction=dec.get("prediction", {}),
        impact=dec.get("impact", {}),
        recommendations=dec.get("recommendations", []),
        confidence=dec.get("confidence", 70.0),
        explanation=result.get("explanation", []),
    )
