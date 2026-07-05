from src.ai.gateway import call_openrouter
from src.ai.safety import check_safety

PLANNER_MODELS = ["nvidia/nemotron-3-ultra:free", "openrouter/free"]


async def complete(prompt: str, context: str = "") -> str | None:
    pre = await check_safety(prompt)
    if not pre["safe"]:
        return None

    full_prompt = f"{context}\n\n{prompt}" if context else prompt
    response = await call_openrouter(
        PLANNER_MODELS,
        {"messages": [{"role": "user", "content": full_prompt}]},
    )
    if response is None:
        return None

    try:
        text = response["choices"][0]["message"]["content"]
    except (KeyError, IndexError, TypeError):
        return None

    post = await check_safety(text)
    if not post["safe"]:
        return None

    return text
