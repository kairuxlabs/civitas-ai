from src.agents.gemini_client import call_gemini, parse_json_safe
from src.utils.logger import get_logger

logger = get_logger(__name__)

ENTITY_LABELS = ["Hospital", "Road", "District", "Flood", "Emergency", "Traffic", "Shelter", "School"]


def build_extraction_prompt(chunk_text: str) -> str:
    labels = ", ".join(ENTITY_LABELS)
    return (
        f"Extract entities and relationships from this text for a city knowledge graph.\n"
        f"Entity types: {labels}.\n"
        f'Return ONLY a JSON object: {{"entities": [{{"type": "...", "name": "..."}}], '
        f'"relations": [{{"from": "...", "relation": "...", "to": "..."}}]}}\n\n'
        f"Text:\n{chunk_text[:2000]}"
    )


def extract_entities(chunk_text: str) -> dict:
    """Returns {"entities": [...], "relations": [...]}, empty lists on any
    failure (no Gemini key, bad JSON, API error) — never raises."""
    prompt = build_extraction_prompt(chunk_text)
    raw = call_gemini(prompt, expect_json=True)
    if not raw:
        return {"entities": [], "relations": []}

    parsed = parse_json_safe(raw)
    if not parsed:
        logger.warning("Entity extraction: Gemini response was not valid JSON")
        return {"entities": [], "relations": []}

    return {
        "entities": parsed.get("entities", []),
        "relations": parsed.get("relations", []),
    }
