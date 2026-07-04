from src.agents.base import AgentState
from src.utils.logger import get_logger

logger = get_logger(__name__)

# Static SOP knowledge base — replaced by ChromaDB vector search when available
_SOP_DOCS = [
    {
        "id": "sop-flood-001",
        "title": "Flood Emergency SOP",
        "content": (
            "When rain > 20mm/h: (1) Activate drainage pumps at all low-lying districts. "
            "(2) Deploy traffic police to flood-prone intersections. "
            "(3) Broadcast emergency alert via city PA system. "
            "(4) Coordinate with Red Cross for evacuation readiness. "
            "Authority: District Emergency Committee."
        ),
        "keywords": ["flood", "rain", "drainage", "heavy rain", "ngập", "mưa"],
    },
    {
        "id": "sop-aqi-001",
        "title": "Air Quality Emergency SOP",
        "content": (
            "When AQI > 150 (Hazardous): (1) Issue health advisory via city channels. "
            "(2) Suspend outdoor construction and burning. "
            "(3) Recommend N95 masks for outdoor activity. "
            "(4) Increase street-cleaning vehicle deployment. "
            "Notify Ministry of Natural Resources within 2 hours."
        ),
        "keywords": ["aqi", "air quality", "pollution", "pm25", "hazardous", "ô nhiễm"],
    },
    {
        "id": "sop-traffic-001",
        "title": "Traffic Congestion Management SOP",
        "content": (
            "When traffic index > HIGH: (1) Activate dynamic signal timing at key intersections. "
            "(2) Open emergency bus lanes on main corridors. "
            "(3) Alert commuters via Hanoi Traffic app push notifications. "
            "(4) Request Traffic Police rapid response unit deployment."
        ),
        "keywords": ["traffic", "congestion", "tắc đường", "intersection"],
    },
    {
        "id": "sop-heatwave-001",
        "title": "Heatwave Response SOP",
        "content": (
            "When temperature > 38°C for 3+ days: (1) Open cooling centers at all district community halls. "
            "(2) Increase water supply pressure in residential areas. "
            "(3) Deploy mobile medical teams in elderly-dense districts. "
            "(4) Restrict outdoor labor 11:00–14:00. "
            "Monitor vulnerable populations proactively."
        ),
        "keywords": ["heatwave", "heat", "temperature", "nắng nóng", "nhiệt độ"],
    },
    {
        "id": "sop-event-001",
        "title": "Mass Event Management SOP",
        "content": (
            "For events with > 10,000 attendees: (1) Close surrounding roads 2 hours before event. "
            "(2) Station ambulance and fire units at venue perimeter. "
            "(3) Coordinate with event organizer for crowd flow plan. "
            "(4) Pre-position 5 additional police units. "
            "Require 72-hour advance notice to city authorities."
        ),
        "keywords": ["event", "festival", "mass", "concert", "sự kiện", "lễ hội"],
    },
]


def _keyword_match(query: str, keywords: list[str]) -> int:
    q = query.lower()
    return sum(1 for kw in keywords if kw in q)


def knowledge_agent(state: AgentState) -> dict:
    query = state.get("query", "").lower()
    aqi_index = float(state.get("aqi_data", {}).get("aqi_index") or 100)
    rain = float(state.get("weather_data", {}).get("rain") or 0)

    # Augment query with sensor context for better matching
    context_hints = []
    if aqi_index > 150:
        context_hints.append("hazardous aqi air quality pollution")
    elif aqi_index > 100:
        context_hints.append("aqi air quality")
    if rain > 20:
        context_hints.append("heavy rain flood drainage")
    elif rain > 5:
        context_hints.append("rain")

    enriched_query = query + " " + " ".join(context_hints)

    scored = [
        (doc, _keyword_match(enriched_query, doc["keywords"]))
        for doc in _SOP_DOCS
    ]
    scored.sort(key=lambda x: x[1], reverse=True)

    top = [doc for doc, score in scored if score > 0][:2]

    if top:
        summary = "Relevant SOPs: " + "; ".join(
            f"[{doc['title']}] {doc['content'][:120]}..." for doc in top
        )
    else:
        summary = "No specific SOP matched. Apply general city operations protocol."

    logger.info(f"Knowledge agent found {len(top)} relevant SOPs")
    return {"knowledge_summary": summary}
