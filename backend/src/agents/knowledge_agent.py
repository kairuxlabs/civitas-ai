from src.agents.base import AgentState
from src.agents.gemini_client import call_gemini
from src.knowledge_pipeline.loaders import qdrant_loader
from src.utils.config import settings
from src.utils.logger import get_logger

logger = get_logger(__name__)

# Static SOP knowledge base — kept for concrete, action-oriented emergency
# steps even after city_knowledge (Qdrant) integration below; city_knowledge
# adds broader informational grounding, not a replacement for these SOPs.
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


def _first_action(content: str) -> str:
    """Extract step (1) from SOP content."""
    import re
    m = re.search(r"\(1\)\s*([^.]+\.)", content)
    return m.group(1).strip() if m else content[:80]


def knowledge_agent(state: AgentState) -> dict:
    query = state.get("query", "").lower()
    aqi_index = float(state.get("aqi_data", {}).get("aqi_index") or 100)
    rain = float(state.get("weather_data", {}).get("rain") or 0)
    temperature = float(state.get("weather_data", {}).get("temperature") or 30)

    # Only add context hints when thresholds are clearly exceeded
    context_hints = []
    if aqi_index > 150:
        context_hints.append("hazardous aqi air quality pollution")
    if rain > 20:
        context_hints.append("heavy rain flood drainage")
    if temperature > 38:
        context_hints.append("heatwave heat temperature")

    enriched_query = query + " " + " ".join(context_hints)

    scored = [
        (doc, _keyword_match(enriched_query, doc["keywords"]))
        for doc in _SOP_DOCS
    ]
    scored.sort(key=lambda x: x[1], reverse=True)
    top = [doc for doc, score in scored if score > 0][:2]

    city_chunks = []
    if settings.qdrant_url:
        city_chunks = qdrant_loader.search_chunks(state.get("query", ""), k=2)

    if not top and not city_chunks:
        summary = "No specific SOP matched. Apply general city operations protocol."
        logger.info("Knowledge agent: no SOP matched")
        return {"knowledge_summary": summary}

    # Try Gemini to synthesize a brief action summary from whatever context is available
    try:
        context_blocks = []
        if top:
            sop_texts = "\n".join(f"- {doc['title']}: {doc['content']}" for doc in top)
            context_blocks.append(f"Các SOP liên quan:\n{sop_texts}")
        if city_chunks:
            chunk_texts = "\n".join(
                f"- {c['title']} ({c['source']}): {c['content']}" for c in city_chunks
            )
            context_blocks.append(f"Ngữ cảnh liên quan:\n{chunk_texts}")

        prompt = (
            f"Dựa trên tình huống: AQI={aqi_index:.0f}, mưa={rain:.0f}mm/h, nhiệt độ={temperature:.0f}°C, "
            f"câu hỏi: '{state.get('query', '')}'\n\n"
            + "\n\n".join(context_blocks) +
            "\n\nHãy tóm tắt trong 1-2 câu tiếng Việt: cần thực hiện hành động ưu tiên nào ngay lập tức? "
            "Chỉ nêu hành động cụ thể, không giải thích dài dòng."
        )
        gemini_summary = call_gemini(prompt)
        if gemini_summary:
            if top:
                sop_names = ", ".join(doc["title"] for doc in top)
                summary = f"[{sop_names}] {gemini_summary}"
            else:
                summary = gemini_summary
            logger.info(
                f"Knowledge agent (Gemini): {len(top)} SOPs, {len(city_chunks)} city_knowledge chunks → summary"
            )
            return {"knowledge_summary": summary}
    except Exception:
        pass

    # Fallback: deterministic, SOP-only — city_chunks are intentionally not
    # stitched in without an LLM (a raw concatenation of Wikipedia/OSM text
    # and SOP action steps would read as incoherent).
    if top:
        parts = [f"{doc['title']}: {_first_action(doc['content'])}" for doc in top]
        summary = " | ".join(parts)
        logger.info(f"Knowledge agent (rule-based): {len(top)} SOPs")
        return {"knowledge_summary": summary}

    summary = "No specific SOP matched. Apply general city operations protocol."
    logger.info("Knowledge agent: no SOP matched (city_knowledge unavailable without LLM)")
    return {"knowledge_summary": summary}
