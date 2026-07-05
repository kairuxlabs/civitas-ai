import aiohttp

from src.utils.logger import get_logger

logger = get_logger(__name__)

OPENROUTER_BASE_URL = "https://openrouter.ai/api/v1"


async def call_openrouter(models: list[str], payload: dict, endpoint: str = "chat/completions") -> dict | None:
    from src.utils.config import settings
    if not settings.openrouter_api_key:
        return None

    url = f"{OPENROUTER_BASE_URL}/{endpoint}"
    headers = {"Authorization": f"Bearer {settings.openrouter_api_key}"}

    async with aiohttp.ClientSession() as http:
        for model in models:
            try:
                body = {**payload, "model": model}
                async with http.post(url, json=body, headers=headers) as resp:
                    data = await resp.json()
                    if resp.status == 200:
                        return data
                    logger.warning(f"OpenRouter model {model} returned status {resp.status}")
            except Exception as e:
                logger.warning(f"OpenRouter call failed for model {model}: {e}")

    return None
