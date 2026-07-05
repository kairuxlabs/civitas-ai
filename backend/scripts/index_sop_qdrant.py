# backend/scripts/index_sop_qdrant.py
"""One-time indexer: embeds the static SOP docs via Gemini and loads them into
the Qdrant `cityos_sop` collection, so KnowledgeMemory.search()
(src/runtime/memory.py) can hit real vector search instead of the keyword
fallback.

Usage:
    cd backend
    python -m scripts.index_sop_qdrant
"""
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, PointStruct, VectorParams

from src.agents.gemini_client import EMBED_DIM, embed_text
from src.agents.knowledge_agent import _SOP_DOCS
from src.utils.config import settings

COLLECTION = "cityos_sop"


def main() -> None:
    if not settings.qdrant_url:
        raise SystemExit("QDRANT_URL is not set — check backend/.env")
    if not settings.gemini_api_key:
        raise SystemExit("GEMINI_API_KEY is not set — needed to embed the SOP docs")

    client = QdrantClient(url=settings.qdrant_url, api_key=settings.qdrant_api_key or None)

    if client.collection_exists(COLLECTION):
        client.delete_collection(COLLECTION)
    client.create_collection(
        collection_name=COLLECTION,
        vectors_config=VectorParams(size=EMBED_DIM, distance=Distance.COSINE),
    )

    points = []
    for i, doc in enumerate(_SOP_DOCS, start=1):
        vector = embed_text(doc["content"], task_type="RETRIEVAL_DOCUMENT")
        if vector is None:
            raise SystemExit(f"Failed to embed doc {doc['id']} — check GEMINI_API_KEY / quota")
        points.append(PointStruct(
            id=i,
            vector=vector,
            payload={"doc_id": doc["id"], "title": doc["title"], "content": doc["content"]},
        ))

    client.upsert(collection_name=COLLECTION, points=points)

    count = client.count(COLLECTION).count
    print(f"Indexed {count} SOP docs into '{COLLECTION}' at {settings.qdrant_url}")


if __name__ == "__main__":
    main()
