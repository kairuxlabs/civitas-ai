from src.ai.gateway import call_openrouter

EMBEDDING_MODELS = ["nvidia/llama-nemotron-embed-vl-1b-v2:free"]


async def embed(text: str) -> list[float] | None:
    response = await call_openrouter(
        EMBEDDING_MODELS,
        {"input": text},
        endpoint="embeddings",
    )
    if response is None:
        return None
    try:
        return response["data"][0]["embedding"]
    except (KeyError, IndexError, TypeError):
        return None
