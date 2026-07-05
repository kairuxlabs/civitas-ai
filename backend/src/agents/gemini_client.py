# backend/src/agents/gemini_client.py
import asyncio
import json
import re
from src.utils.logger import get_logger

logger = get_logger(__name__)

# Current Gemini model supporting generateContent
GEMINI_MODEL = "gemini-2.0-flash"
EMBED_MODEL = "models/gemini-embedding-001"
EMBED_DIM = 768


def _call_gemini_raw(prompt: str) -> str | None:
    try:
        from src.utils.config import settings
        if not settings.gemini_api_key:
            return None

        from google import genai
        from google.genai import types

        client = genai.Client(api_key=settings.gemini_api_key)
        response = client.models.generate_content(
            model=GEMINI_MODEL,
            contents=prompt,
            config=types.GenerateContentConfig(
                max_output_tokens=600,
                temperature=0.4,
            ),
        )
        text = response.text.strip() if response.text else None
        return text or None
    except Exception as e:
        logger.warning(f"Gemini call failed: {e}")
        return None


def _call_openrouter_fallback(prompt: str) -> str | None:
    """Fallback to the free OpenRouter/Nemotron planner (src/ai/planner.py) when
    Gemini is unavailable (e.g. quota exhausted). No-ops when OPENROUTER_API_KEY
    is unset, since call_openrouter already degrades to None in that case.

    NOTE: call_gemini (and therefore this) must only be invoked from a sync
    context without a running event loop — every existing call site already
    wraps call_gemini in asyncio.to_thread(), so asyncio.run() below is safe.
    Calling it from within a running loop would raise RuntimeError, which is
    caught here and degrades to None rather than crashing.
    """
    try:
        from src.ai.planner import complete
        return asyncio.run(complete(prompt))
    except Exception as e:
        logger.warning(f"OpenRouter fallback failed: {e}")
        return None


def _extract_json(text: str) -> str:
    match = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", text, re.DOTALL)
    if match:
        return match.group(1)
    match = re.search(r"\{.*\}", text, re.DOTALL)
    if match:
        return match.group(0)
    return text


def call_gemini(prompt: str, expect_json: bool = False) -> str | None:
    """Call Gemini API using google-genai SDK, falling back to the OpenRouter/Nemotron
    gateway when Gemini fails (e.g. quota exhausted). Returns text or None if both
    providers are unavailable."""
    text = _call_gemini_raw(prompt)
    if text is None:
        text = _call_openrouter_fallback(prompt)
    if text is None:
        return None

    if expect_json:
        text = _extract_json(text)

    return text


def embed_text(text: str, task_type: str = "RETRIEVAL_QUERY") -> list[float] | None:
    """Embed text via Gemini. task_type is RETRIEVAL_DOCUMENT when indexing, RETRIEVAL_QUERY when searching."""
    try:
        from src.utils.config import settings
        if not settings.gemini_api_key:
            return None

        from google import genai
        from google.genai import types

        client = genai.Client(api_key=settings.gemini_api_key)
        response = client.models.embed_content(
            model=EMBED_MODEL,
            contents=text,
            config=types.EmbedContentConfig(output_dimensionality=EMBED_DIM, task_type=task_type),
        )
        return response.embeddings[0].values
    except Exception as e:
        logger.warning(f"Gemini embedding failed: {e}")
        return None


def parse_json_safe(text: str) -> dict | None:
    try:
        return json.loads(text)
    except Exception:
        return None
