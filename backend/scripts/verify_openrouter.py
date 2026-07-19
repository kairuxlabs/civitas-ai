"""Manual verification script for the OpenRouter/Nemotron AI Gateway.

Run this once with a real OPENROUTER_API_KEY before a demo to confirm the
configured model slugs (src/ai/planner.py, embedding.py, reranker.py,
safety.py) still resolve against the live OpenRouter API. Not run in CI —
it makes real network calls and requires a real key.

Usage:
    cd backend
    OPENROUTER_API_KEY=sk-... python -m scripts.verify_openrouter
"""
import asyncio
import os
import sys

# Allow running as: python -m scripts.verify_openrouter from backend/
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.ai import embedding, planner, reranker, safety  # noqa: E402
from src.utils.config import settings  # noqa: E402


async def main() -> None:
    if not settings.openrouter_api_key:
        print("OPENROUTER_API_KEY is not set — nothing to verify.")
        return

    planner_result = await planner.complete("Say hello in one word.")
    print(f"planner.complete: {'OK' if planner_result is not None else 'FAILED (None — check model slug/logs)'} "
          f"-> {planner_result!r}")

    embedding_result = await embedding.embed("Hanoi flood risk")
    ok = embedding_result is not None and len(embedding_result) > 0
    print(f"embedding.embed: {'OK' if ok else 'FAILED (None/empty — check model slug/logs)'} "
          f"-> vector length {len(embedding_result) if embedding_result else 0}")

    safety_result = await safety.check_safety("Hanoi flood risk")
    print(f"safety.check_safety: OK -> {safety_result!r}")

    rerank_result = await reranker.rerank(
        "flood risk", ["Flood SOP for Hanoi", "Unrelated document about parks"], top_k=1
    )
    print(f"reranker.rerank: {'OK' if rerank_result else 'FAILED (empty)'} -> {rerank_result!r}")


if __name__ == "__main__":
    asyncio.run(main())
