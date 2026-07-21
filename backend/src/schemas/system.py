from pydantic import BaseModel


class SystemStatusOut(BaseModel):
    database: bool
    gemini_configured: bool
    neo4j_configured: bool
    qdrant_configured: bool
    openrouter_configured: bool
    gemini_model: str
    gemini_temperature: float
    openrouter_fallback_models: list[str]
