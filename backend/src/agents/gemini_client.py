# backend/src/agents/gemini_client.py
import json
import re
from src.utils.logger import get_logger

logger = get_logger(__name__)

# Current Gemini model supporting generateContent
GEMINI_MODEL = "gemini-2.0-flash"


def call_gemini(prompt: str, expect_json: bool = False) -> str | None:
    """Call Gemini API using google-genai SDK. Returns text or None if unavailable."""
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
        if not text:
            return None

        if expect_json:
            match = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", text, re.DOTALL)
            if match:
                text = match.group(1)
            else:
                # Try to find raw JSON object
                match = re.search(r"\{.*\}", text, re.DOTALL)
                if match:
                    text = match.group(0)

        return text
    except Exception as e:
        logger.warning(f"Gemini call failed: {e}")
        return None


def parse_json_safe(text: str) -> dict | None:
    try:
        return json.loads(text)
    except Exception:
        return None
