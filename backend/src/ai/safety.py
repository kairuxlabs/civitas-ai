from src.ai.gateway import call_openrouter

SAFETY_MODELS = ["nvidia/nemotron-3.5-content-safety:free"]


async def check_safety(text: str) -> dict:
    response = await call_openrouter(
        SAFETY_MODELS,
        {"messages": [{"role": "user", "content": text}]},
    )
    if response is None:
        return {"safe": True, "reason": None}

    try:
        content = response["choices"][0]["message"]["content"].strip().lower()
    except (KeyError, IndexError, AttributeError):
        return {"safe": True, "reason": None}

    if "unsafe" in content:
        return {"safe": False, "reason": content}
    return {"safe": True, "reason": None}
