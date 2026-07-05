from src.ai.gateway import call_openrouter

RERANK_MODELS = ["nvidia/llama-nemotron-rerank-vl-1b-v2:free"]


async def rerank(query: str, documents: list[str], top_k: int = 5) -> list[int]:
    if not documents:
        return []

    fallback = list(range(min(top_k, len(documents))))

    response = await call_openrouter(
        RERANK_MODELS,
        {"query": query, "documents": documents, "top_n": top_k},
        endpoint="rerank",
    )
    if response is None:
        return fallback

    try:
        ranked = sorted(response["results"], key=lambda r: r["relevance_score"], reverse=True)
        return [r["index"] for r in ranked[:top_k]]
    except (KeyError, TypeError):
        return fallback
